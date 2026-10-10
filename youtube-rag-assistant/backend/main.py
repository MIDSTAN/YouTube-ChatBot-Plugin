from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router


app = FastAPI(
    title="YouTube RAG Assistant API",
    description=(
        "Extract YouTube transcripts and answer questions "
        "using LangChain, ChromaDB, and Groq."
    ),
    version="1.0.0",
)


# Development configuration.
# Restrict this further when deploying the application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "YouTube RAG Assistant API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }