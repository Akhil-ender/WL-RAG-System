# PDF Chat - AI-Powered Document Q&A Application

A full-stack web application that enables users to upload PDF documents and ask questions about their content using AI-powered Retrieval-Augmented Generation (RAG). Features include natural language to SQL queries for claims data analysis and admin-controlled CSV data uploads. Built with FastAPI backend, React frontend, and PostgreSQL with PGVector for efficient vector storage.

## 🚀 Features

### Core Functionality
- **PDF Document Processing**: Upload and process multiple PDF files simultaneously
- **AI-Powered Q&A**: Ask natural language questions about uploaded documents
- **Text-to-SQL Queries**: Convert natural language questions into SQL queries for claims database analysis
- **CSV Data Management**: Admin-only CSV file uploads to populate claims database tables
- **Real-time Chat Interface**: Interactive chat with typing indicators and message history
- **Document Chunking**: Intelligent text segmentation for optimal retrieval

### Authentication & Security
- **User Authentication**: Secure signup/login with JWT tokens
- **Role-Based Access**: Admin and User roles with first-user-becomes-admin logic
- **Admin-Only Features**: CSV upload and database management restricted to admin users
- **API Rate Limiting**: Graceful "Out of Message Quota" error handling for API limits
- **Password Security**: bcrypt hashing for secure password storage
- **Session Management**: Persistent authentication with localStorage

### Modern UI/UX
- **Responsive Design**: Beautiful beige and light red themed interface
- **Drag & Drop Upload**: Intuitive file upload with progress indicators
- **Tabbed Interface**: Clean navigation between upload, chat, Text2SQL, and CSV upload functions
- **Role-Based UI**: Dynamic tab visibility based on user permissions
- **Error Handling**: User-friendly error messages with graceful API rate limit handling
- **Mobile Friendly**: Responsive design that works on all devices

### Technical Stack
- **Backend**: FastAPI with Python 3.9+
- **Frontend**: React 18 with modern hooks and context API
- **Database**: PostgreSQL with PGVector extension for vector storage
- **AI/ML**: Google Gemini Pro for language generation and SQL query generation, HuggingFace embeddings
- **SQL Chain**: LangChain SQLDatabaseChain for natural language to SQL conversion
- **Vector Search**: PGVector for efficient similarity search
- **Authentication**: JWT tokens with bcrypt password hashing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   PostgreSQL    │
│                 │    │                 │    │   + PGVector    │
│ • Authentication│◄──►│ • JWT Auth      │◄──►│                 │
│ • PDF Upload    │    │ • PDF Processing│    │ • Users         │
│ • Chat Interface│    │ • RAG Pipeline  │    │ • Chat History  │
│ • Text2SQL UI   │    │ • SQL Chain     │    │ • Document Chunks│
│ • CSV Upload    │    │ • CSV Processing│    │ • Claims Data   │
│ • Role-based UI │    │ • API Endpoints │    │ • Claims Detail │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.9+**
- **Node.js 16+** and **npm**
- **PostgreSQL 12+** with **PGVector extension**
- **Google API Key** for Gemini Pro

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Akhil-ender/GeminiPro-Powered-RAG-QA.git
cd GeminiPro-Powered-RAG-QA
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### PostgreSQL Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE pdf_chat_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE pdf_chat_db TO your_username;
\q

# Install PGVector extension
sudo -u postgres psql -d pdf_chat_db
CREATE EXTENSION vector;
\q
```

#### Environment Variables
Create a `.env` file in the root directory:

```env
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database Configuration
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/pdf_chat_db
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start the Backend Server
```bash
# From the root directory
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at: `http://localhost:8000`

### Start the Frontend Development Server
```bash
# From the frontend directory
cd frontend
npm start
```

The frontend will be available at: `http://localhost:3000`

## 📚 API Documentation

### Authentication Endpoints

#### POST `/signup`
Create a new user account (first user becomes admin)
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

#### POST `/login`
Authenticate user and receive JWT token
```json
{
  "username": "string",
  "password": "string"
}
```

#### GET `/me`
Get current user information (requires authentication)

### Document Processing Endpoints

#### POST `/upload`
Upload and process PDF files
- **Content-Type**: `multipart/form-data`
- **Body**: PDF files as form data

#### POST `/chat`
Send a question about uploaded documents
```json
{
  "question": "string"
}
```

#### GET `/status`
Check application status and health

### Claims Data Endpoints

#### POST `/text2sql`
Convert natural language questions to SQL queries and execute them on claims database (requires authentication)
```json
{
  "question": "How many claims are denied?",
  "top_k": 3
}
```

#### POST `/upload-csv`
Upload CSV files to populate claims database tables (admin-only access)
- **Content-Type**: `multipart/form-data`
- **Body**: CSV file and table_name parameter
- **Requires**: Admin role authentication

### Response Format
All API responses follow this structure:
```json
{
  "message": "string",
  "data": {},
  "status": "success|error"
}
```

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chat History Table
```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    user_query TEXT NOT NULL,
    model_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Claims List Table
```sql
CREATE TABLE claims_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_name VARCHAR(255) NOT NULL,
    billed_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2),
    status VARCHAR(50),
    insurer_name VARCHAR(255),
    discharge_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Claims Detail Table
```sql
CREATE TABLE claims_detail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES claims_list(id),
    denial_reason TEXT,
    cpt_codes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 Usage Guide

### 1. User Registration
- Navigate to `http://localhost:3000`
- Click "Sign up" to create an account
- First registered user automatically becomes admin

### 2. Upload PDF Documents
- Login to access the dashboard
- Click "Upload PDF" tab
- Drag and drop PDF files or click to browse
- Click "Upload & Process" to process documents

### 3. Ask Questions
- Switch to "Chat" tab after uploading documents
- Type questions about your uploaded PDFs
- Receive AI-powered answers based on document content

### 4. Query Claims Data with Natural Language
- Switch to "Text to SQL" tab
- Type natural language questions about claims data
- Examples: "How many claims are denied?", "What's the average billed amount?"
- View generated SQL queries and results in formatted tables

### 5. Upload Claims Data (Admin Only)
- Admin users will see "CSV Upload" tab
- Select target table (claims_list or claims_detail)
- Drag and drop CSV files or click to browse
- Supports pipe-delimited CSV files (|)
- Upload progress and status messages provided

### 6. View Chat History
- All conversations are automatically saved
- Chat history is preserved across sessions

## 🔧 Configuration

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google Gemini Pro API key | Yes | - |
| `JWT_SECRET_KEY` | Secret key for JWT token signing | Yes | - |
| `JWT_ALGORITHM` | JWT signing algorithm | No | HS256 |
| `JWT_EXPIRATION_HOURS` | Token expiration time | No | 24 |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |

### Frontend Configuration
The frontend automatically connects to the backend at `http://localhost:8000`. To change this, modify the `API_BASE_URL` in `frontend/src/utils/api.js`.

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues
- **Database connection errors**: Verify PostgreSQL is running and credentials are correct
- **PGVector extension missing**: Install PGVector extension in your PostgreSQL database
- **Google API errors**: Verify your `GOOGLE_API_KEY` is valid and has Gemini Pro access

#### Frontend Issues
- **CORS errors**: Ensure backend is running on port 8000
- **Authentication issues**: Check JWT token in browser localStorage
- **Upload failures**: Verify backend `/upload` endpoint is accessible
- **Text2SQL errors**: Check database connection and claims tables exist
- **CSV upload access denied**: Verify user has admin role for CSV upload functionality
- **"Out of Message Quota" errors**: API rate limits reached, wait before retrying

#### Database Issues
- **Migration errors**: Drop and recreate tables if schema changes
- **Vector dimension errors**: Ensure embedding model produces 768-dimensional vectors

### Logs and Debugging
- Backend logs: Check console output from uvicorn server
- Frontend logs: Open browser developer tools console
- Database logs: Check PostgreSQL logs for connection issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini Pro** for powerful language generation
- **LangChain** for RAG pipeline framework
- **PGVector** for efficient vector storage
- **HuggingFace** for embedding models
- **FastAPI** for modern Python web framework
- **React** for dynamic frontend interface
  

