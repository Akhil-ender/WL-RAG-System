import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Functions to handle PDF processing and embedding
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context. If the answer is not in
    the provided context, just say, "Sorry, the question is out of context documents!" Don't provide the wrong answer.

    Context:
    {context}?

    Question:
    {question}

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.6)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

# Streamlit app
def main():
    st.set_page_config(page_title="Chat with PDF")
    st.title("Chat with PDF using Gemini Pro!")

    # Sidebar for uploading PDFs
    with st.sidebar:
        st.title("Menu")
        pdf_docs = st.file_uploader("Upload your PDF files:", accept_multiple_files=True)
        if st.button("Submit & Process"):
            if pdf_docs:
                with st.spinner("Processing PDFs..."):
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(raw_text)
                    get_vector_store(text_chunks)
                    st.success("PDFs processed successfully! Start chatting.")
            else:
                st.warning("Please upload at least one PDF file.")

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display chat messages from history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input section at the bottom
    if prompt := st.chat_input("Ask a question about the uploaded PDF(s):"):
        if not os.path.exists("faiss_index"):
            st.error("No PDF files have been processed. Please upload and process PDFs first.")
        else:
            # Add user message to chat history
            st.session_state["messages"].append({"role": "user", "content": prompt})

            # Load FAISS index and query
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            docs = new_db.similarity_search(prompt)

            # Get conversational chain and generate response
            chain = get_conversational_chain()
            response = chain({"input_documents": docs, "question": prompt}, return_only_outputs=True)
            bot_response = response["output_text"]

            # Add assistant response to chat history
            st.session_state["messages"].append({"role": "assistant", "content": bot_response})

            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(bot_response)

if __name__ == "__main__":
    main()
