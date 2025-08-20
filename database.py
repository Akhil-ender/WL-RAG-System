from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, Enum, Numeric, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import os
import uuid
import enum
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/pdf_chat_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_query = Column(Text, nullable=False)
    model_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    document_name = Column(String(255), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

class ClaimsList(Base):
    __tablename__ = "claims_list"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String(255), nullable=False)
    billed_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False)
    insurer_name = Column(String(255), nullable=False)
    discharge_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    details = relationship("ClaimsDetail", back_populates="claim")

class ClaimsDetail(Base):
    __tablename__ = "claims_detail"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims_list.id"), nullable=False, index=True)
    denial_reason = Column(Text, nullable=True)
    cpt_codes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    claim = relationship("ClaimsList", back_populates="details")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create database tables, skipping those that require PGVector extension"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create all tables: {e}")
        for table_name, table in Base.metadata.tables.items():
            if table_name not in ['document_chunks']:  # Skip tables with vector columns
                try:
                    table.create(bind=engine, checkfirst=True)
                    print(f"Created table: {table_name}")
                except Exception as table_error:
                    print(f"Could not create table {table_name}: {table_error}")

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
