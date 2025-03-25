# 🤖 RAG FastAPI App (with Ollama + Docker)

## 🚀 How to Run


docker-compose up --build

# 🌐 Swagger UI
## After launch, open:

👉 http://localhost:8000/docs

# 📋 Usage Flow
## POST /upload-data
→ Upload .txt file

## POST /train
→ Index documents and create vector DB

## GET /ask?question=...
→ Ask a question based on the uploaded files