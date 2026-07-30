"""
Ingests documents from the DATA_DIR folder into a persisted Chroma vector store.

Run this once whenever you add or change documents:
    python ingest.py
"""
import os
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from config import OPENAI_API_KEY, CHROMA_PERSIST_DIR, DATA_DIR, EMBEDDING_MODEL


def load_documents():
    docs = []

    # Load .txt files
    txt_loader = DirectoryLoader(
        DATA_DIR, glob="**/*.txt", loader_cls=TextLoader, show_progress=True
    )
    docs.extend(txt_loader.load())

    # Load .pdf files
    pdf_loader = DirectoryLoader(
        DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True
    )
    docs.extend(pdf_loader.load())

    # Load .md files (treated as text)
    md_loader = DirectoryLoader(
        DATA_DIR, glob="**/*.md", loader_cls=TextLoader, show_progress=True
    )
    docs.extend(md_loader.load())

    return docs


def main():
    print(f"Loading documents from: {DATA_DIR}")
    documents = load_documents()

    if not documents:
        print(
            f"No documents found in {DATA_DIR}. "
            "Add .txt, .md, or .pdf files there and re-run this script."
        )
        return

    print(f"Loaded {len(documents)} document(s). Splitting into chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)

    print(f"Embedding and storing chunks in: {CHROMA_PERSIST_DIR}")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    print(f"Done. Vector store now has {vectorstore._collection.count()} vectors.")


if __name__ == "__main__":
    main()