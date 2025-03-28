from fastapi import FastAPI, UploadFile, File, Query, HTTPException
import shutil
import os

from confluence_bot_app import run_program
from bridge.bridge_v1 import AzureConnector
from rag_gema3 import RAGModel, custom_prompt

app = FastAPI()
rag = RAGModel()

DATA_DIR = "../data"
os.makedirs(DATA_DIR, exist_ok=True)

@app.post("/upload-data")
def upload_data(file: UploadFile = File(...)):
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "uploaded", "filename": file.filename}


@app.delete("/delete-file")
def delete_file(filename: str = Query(...)):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)
    return {"status": "deleted", "filename": filename}


@app.get("/files")
def list_uploaded_files():
    files = os.listdir(DATA_DIR)
    return {"files": files}


@app.post("/train")
def train_model():
    rag.load_and_index_documents(DATA_DIR)
    rag.setup_qa_chain(custom_prompt)
    return {"status": "training complete"}


@app.get("/ask")
def ask_question(question: str = Query(..., min_length=1)):
    try:
        answer = rag.ask(question)
        return {"question": question, "answer": answer}
    except ValueError as e:
        return {"error": str(e)}


@app.post("/run_ai_program")
async def run_ai_program(ai_model: str = Query(..., min_length=1)):
    await run_program(rag, ai_model)


@app.post("/fedramp/ask")
def ask_question_bridge_ai(question: str = Query(..., min_length=1)):
    try:
        connector = AzureConnector()
        answer = connector.process_fedramp_query(question)
        return {
            "question": question,
            "answer": answer,
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
