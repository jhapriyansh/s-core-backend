import config
from fastapi import FastAPI, UploadFile
import os
from ingestion.extract import extract_pdf
from ingestion.syllabus_map import map_to_syllabus
from ingestion.embed import embed
from db.chroma import get_chroma
from runtime.retrieve import retrieve
from runtime.classify import classify
from runtime.pace import pace_config
from runtime.respond import respond
from dotenv import load_dotenv
from runtime.coverage import coverage_check
load_dotenv()
app = FastAPI()

SYLLABUS = ""
COLLECTION = None

@app.post("/upload")
async def upload(file: UploadFile, syllabus: str):
    global SYLLABUS, COLLECTION
    path = file.filename
    with open(path, "wb") as f:
        f.write(await file.read())

    SYLLABUS = syllabus
    COLLECTION = get_chroma("deck1")

    chunks = extract_pdf(path)

    for chunk in chunks:
        topics = map_to_syllabus(chunk, syllabus)
        if topics:
            vec = embed(chunk)
            COLLECTION.add(
                documents=[chunk],
                embeddings=[vec],
                ids=[str(len(chunk))]
            )
    return {"status": "ingested"}
@app.post("/ask")
async def ask(query: str, pace: str):
    intent = classify(query)
    vec = embed(query)

    docs = retrieve(COLLECTION, vec, pace, query)

    enough = coverage_check(docs, vec, embed)

    answer = respond("\n".join(docs), query, pace)

    # label if outside syllabus
    if not enough:
        answer = "[Outside Syllabus]\n\n" + answer

    return {
        "intent": intent,
        "coverage": enough,
        "answer": answer
    }
