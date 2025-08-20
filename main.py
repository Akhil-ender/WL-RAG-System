from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
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
from database import get_db, create_tables, DocumentChunk, ChatHistory, User, UserRole, ClaimsList, ClaimsDetail
import numpy as np
import bcrypt
import jwt
from datetime import datetime, timedelta
import uuid

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="PDF Chat API", description="RAG-powered PDF Q&A API using Gemini Pro")
security = HTTPBearer()

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

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime


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

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user info"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    """Get current user from token"""
    user = db.query(User).filter(User.id == token_data.get("sub")).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "PDF Chat API is running"}

@app.post("/signup", response_model=Token)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """User signup endpoint"""
    try:
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        user_count = db.query(User).count()
        role = UserRole.ADMIN if user_count == 0 else UserRole.USER
        
        hashed_password = hash_password(user_data.password)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
            role=role
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(new_user.id), "role": role.value},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(new_user.id),
            role=role.value
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """User login endpoint"""
    try:
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user or not verify_password(user_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            role=user.role.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        created_at=current_user.created_at
    )

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

@app.get("/claims")
async def get_claims(db: Session = Depends(get_db)):
    """Get all claims with their details"""
    try:
        claims = db.query(ClaimsList).all()
        return {"claims": claims, "count": len(claims)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching claims: {str(e)}")

@app.get("/claims/{claim_id}")
async def get_claim_details(claim_id: int, db: Session = Depends(get_db)):
    """Get specific claim with details"""
    try:
        claim = db.query(ClaimsList).filter(ClaimsList.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching claim: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
