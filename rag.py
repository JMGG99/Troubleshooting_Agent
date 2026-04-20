import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


load_dotenv(".env")

DOCS_PATH = "docs"
VECTORSTORE_PATH = "vectorstore"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def load_pdfs():
    docs = []
    for file in os.listdir(DOCS_PATH):
        if file.endswith(".pdf"):
            path = os.path.join(DOCS_PATH, file)
            loader = PyPDFLoader(path)
            pages = loader.load()
            docs.extend(pages)
            print(f"{file} — {len(pages)} páginas")
    print(f"\nTotal: {len(docs)} páginas")
    return docs

def chunk_docs(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 800,
        chunk_overlap = 160
    )
    chunks = splitter.split_documents(docs)
    print(f"Total chunks: {len(chunks)}")
    print(f"\nEjemplo:\n{chunks[0].page_content}")
    return chunks

def build_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    vectorstore.save_local(VECTORSTORE_PATH)
    return vectorstore

def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(folder_path=VECTORSTORE_PATH, embeddings=embeddings, allow_dangerous_deserialization=True)
    return vectorstore

def get_retriever():
    if not os.path.exists(VECTORSTORE_PATH):
       docs = load_pdfs()
       chunks = chunk_docs(docs)
       build_vectorstore(chunks)
    
    vectorstore = load_vectorstore()

    return vectorstore.as_retriever(search_type="mmr", search_kwargs={"k":5})


if __name__ == "__main__":
    retriever = get_retriever()
    query = "How to troubleshoot BGP neighbor issues?"
    results = retriever.invoke(query)
    
    print(f"\n{'='*50}")
    print(f"Query: {query}")
    print(f"{'='*50}")
    for i, doc in enumerate(results):
        print(f"\nChunk {i+1}:")
        print(doc.page_content)
        print(f"Fuente: {doc.metadata}")