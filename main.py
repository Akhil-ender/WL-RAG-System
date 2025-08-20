from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import tempfile
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, create_tables, DocumentChunk, ChatHistory
import numpy as np

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI(title="PDF Chat API", description="RAG-powered PDF Q&A API using Gemini Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

class ProcessResponse(BaseModel):
    message: str
    chunks_count: int


def get_pdf_text(pdf_files: List[UploadFile]) -> str:
    """Extract text from uploaded PDF files"""
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf.file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text: str) -> List[str]:
    """Split text into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def store_document_chunks(text_chunks: List[str], document_name: str, db: Session):
    """Store document chunks with embeddings in PostgreSQL"""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    for i, chunk in enumerate(text_chunks):
        embedding = embeddings.embed_query(chunk)
        
        doc_chunk = DocumentChunk(
            content=chunk,
            embedding=embedding,
            document_name=document_name,
            chunk_index=i
        )
        db.add(doc_chunk)
    
    db.commit()
    return len(text_chunks)

def get_conversational_chain():
    """Create conversational chain with Gemini Pro"""
    prompt_template = """
    Answer the question as detailed as possible from the provided context. If the answer is not in
    the provided context, just say, "Sorry, the question is out of context documents!" Don't provide the wrong answer.

    Context:
    {context}?

    Question:
    {question}

    Answer:
    """
    
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PDF Chat API is running"}

@app.post("/upload", response_model=ProcessResponse)
async def upload_pdfs(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload and process PDF files"""
    try:
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        raw_text = get_pdf_text(files)
        
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF files")
        
        text_chunks = get_text_chunks(raw_text)
        
        document_name = files[0].filename if files else "unknown.pdf"
        chunks_count = store_document_chunks(text_chunks, document_name, db)
        
        return ProcessResponse(
            message="PDFs processed successfully! You can now ask questions.",
            chunks_count=chunks_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat endpoint for asking questions about uploaded PDFs"""
    try:
        chunk_count = db.query(DocumentChunk).count()
        if chunk_count == 0:
            raise HTTPException(
                status_code=400, 
                detail="No PDF files have been processed. Please upload PDFs first."
            )
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        query_embedding = embeddings.embed_query(request.question)
        
        similar_chunks = db.execute(
            text("""
                SELECT content, embedding <-> :query_embedding as distance
                FROM document_chunks
                ORDER BY embedding <-> :query_embedding
                LIMIT 4
            """),
            {"query_embedding": str(query_embedding)}
        ).fetchall()
        
        if not similar_chunks:
            raise HTTPException(status_code=400, detail="No relevant documents found.")
        
        from langchain.schema import Document
        docs_content = [Document(page_content=chunk[0]) for chunk in similar_chunks]
        
        chain = get_conversational_chain()
        response = chain.invoke({"input_documents": docs_content, "question": request.question})
        
        chat_entry = ChatHistory(
            user_query=request.question,
            model_response=response["output_text"]
        )
        db.add(chat_entry)
        db.commit()
        
        return ChatResponse(answer=response["output_text"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get the current status of the system"""
    try:
        chunk_count = db.query(DocumentChunk).count()
        chat_count = db.query(ChatHistory).count()
        
        return {
            "database_connected": True,
            "document_chunks": chunk_count,
            "chat_history_entries": chat_count,
            "api_key_configured": bool(os.getenv("GOOGLE_API_KEY"))
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "api_key_configured": bool(os.getenv("GOOGLE_API_KEY"))
        }

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
