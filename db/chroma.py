import chromadb

def get_chroma(deck_id: str):
    client = chromadb.Client()
    return client.get_or_create_collection(deck_id)

