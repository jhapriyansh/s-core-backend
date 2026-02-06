"""
Embedding Module for S-Core
Converts text to semantic vectors using ONNX Runtime (fast CPU inference).
Replaces sentence-transformers + PyTorch for ~2-4x speed and ~1.8GB less disk.
"""

import os
import numpy as np
from typing import List, Union
from pathlib import Path

from config import EMBEDDING_MODEL

# ─────────────────────────────────────────────────────────────
# Model Loading (Singleton)
# ─────────────────────────────────────────────────────────────

_tokenizer = None
_session = None
_model_dir = None


def _get_model_dir() -> str:
    """Get or download the ONNX model directory."""
    global _model_dir
    if _model_dir is not None:
        return _model_dir

    cache_dir = os.path.join(Path.home(), ".cache", "score_models", EMBEDDING_MODEL)
    onnx_path = os.path.join(cache_dir, "model.onnx")

    if not os.path.exists(onnx_path):
        print(f"Downloading ONNX model: {EMBEDDING_MODEL} ...")
        os.makedirs(cache_dir, exist_ok=True)
        _download_onnx_model(cache_dir)
        print("✓ ONNX model downloaded")

    _model_dir = cache_dir
    return _model_dir


def _download_onnx_model(cache_dir: str):
    """Download the ONNX model and tokenizer from Hugging Face."""
    from huggingface_hub import hf_hub_download

    repo_id = f"sentence-transformers/{EMBEDDING_MODEL}"

    # Download ONNX model
    hf_hub_download(
        repo_id=repo_id,
        filename="onnx/model.onnx",
        local_dir=cache_dir,
    )
    # Move from onnx/ subfolder to model.onnx
    onnx_sub = os.path.join(cache_dir, "onnx", "model.onnx")
    onnx_dst = os.path.join(cache_dir, "model.onnx")
    if os.path.exists(onnx_sub) and not os.path.exists(onnx_dst):
        os.rename(onnx_sub, onnx_dst)

    # Download tokenizer files
    for fname in ["tokenizer.json", "tokenizer_config.json", "vocab.txt",
                  "special_tokens_map.json", "config.json"]:
        try:
            hf_hub_download(
                repo_id=repo_id,
                filename=fname,
                local_dir=cache_dir,
            )
        except Exception:
            pass  # Some files are optional


def _get_tokenizer():
    """Get the tokenizer (lazy loading singleton)."""
    global _tokenizer
    if _tokenizer is None:
        from tokenizers import Tokenizer

        model_dir = _get_model_dir()
        tokenizer_path = os.path.join(model_dir, "tokenizer.json")
        _tokenizer = Tokenizer.from_file(tokenizer_path)
        _tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        _tokenizer.enable_truncation(max_length=256)
    return _tokenizer


def _get_session():
    """Get the ONNX inference session (lazy loading singleton)."""
    global _session
    if _session is None:
        import onnxruntime as ort

        model_dir = _get_model_dir()
        onnx_path = os.path.join(model_dir, "model.onnx")

        # Use all available CPU threads
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = os.cpu_count()
        opts.intra_op_num_threads = os.cpu_count()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        print(f"Loading ONNX embedding model: {EMBEDDING_MODEL}")
        _session = ort.InferenceSession(onnx_path, sess_options=opts,
                                        providers=["CPUExecutionProvider"])
        print("✓ ONNX embedding model loaded")
    return _session


def _mean_pooling(token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    """Apply mean pooling — take mean of token embeddings weighted by attention mask."""
    mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
    sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
    return sum_embeddings / sum_mask


def _normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize embedding vectors."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.clip(norms, a_min=1e-9, a_max=None)
    return vectors / norms


# ─────────────────────────────────────────────────────────────
# Embedding Functions
# ─────────────────────────────────────────────────────────────

def embed(text: str) -> List[float]:
    """
    Convert a single text to embedding vector.

    Args:
        text: Input text

    Returns:
        Embedding as list of floats (384 dimensions)
    """
    return embed_batch([text])[0]


def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Convert multiple texts to embeddings (efficient batched ONNX inference).

    Args:
        texts: List of input texts
        batch_size: Batch size for encoding

    Returns:
        List of embeddings
    """
    tokenizer = _get_tokenizer()
    session = _get_session()

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        encoded = tokenizer.encode_batch(batch_texts)

        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

        outputs = session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        # outputs[0] = last hidden state (batch, seq_len, hidden_dim)
        pooled = _mean_pooling(outputs[0], attention_mask)
        normalized = _normalize(pooled)

        all_embeddings.extend(normalized.tolist())

    return all_embeddings


def embed_query(query: str) -> List[float]:
    """
    Embed a query (same as embed, but semantically distinct).
    """
    return embed(query)


# ─────────────────────────────────────────────────────────────
# Similarity Functions
# ─────────────────────────────────────────────────────────────

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts."""
    vec1 = embed(text1)
    vec2 = embed(text2)
    return cosine_similarity(vec1, vec2)
