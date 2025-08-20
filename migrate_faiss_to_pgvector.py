import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from database import get_db, DocumentChunk, create_tables
from dotenv import load_dotenv

load_dotenv()

def migrate_faiss_to_pgvector():
    """Migrate existing FAISS data to PGVector if it exists"""
    if not os.path.exists("faiss_index"):
        print("No FAISS index found. Skipping migration.")
        return
    
    print("Found existing FAISS index. Starting migration...")
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        
        db = next(get_db())
        
        existing_count = db.query(DocumentChunk).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} chunks. Skipping migration.")
            return
        
        texts = []
        embeddings_list = []
        
        docstore = vector_store.docstore
        index_to_docstore_id = vector_store.index_to_docstore_id
        
        for i in range(vector_store.index.ntotal):
            doc_id = index_to_docstore_id[i]
            doc = docstore.search(doc_id)
            if doc:
                texts.append(doc.page_content)
                embedding = vector_store.index.reconstruct(i)
                embeddings_list.append(embedding.tolist())
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings_list)):
            doc_chunk = DocumentChunk(
                content=text,
                embedding=embedding,
                document_name="migrated_from_faiss",
                chunk_index=i
            )
            db.add(doc_chunk)
        
        db.commit()
        print(f"Successfully migrated {len(texts)} chunks from FAISS to PGVector")
        
        backup_dir = "faiss_index_backup"
        if not os.path.exists(backup_dir):
            os.rename("faiss_index", backup_dir)
            print(f"FAISS index backed up to {backup_dir}")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    create_tables()
    migrate_faiss_to_pgvector()
