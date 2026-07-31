"""
Ingests documents from the DATA_DIR folder into a persisted Chroma vector store.

Run this once whenever you add or change documents:
    python ingest.py
"""
import time
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai._common import GoogleGenerativeAIError

from config import GOOGLE_API_KEY, CHROMA_PERSIST_DIR, DATA_DIR, EMBEDDING_MODEL

BATCH_SIZE = 10
DELAY_SECONDS = 8          # base delay between successful batches
MAX_RETRIES = 6            # per batch, before giving up
INITIAL_BACKOFF = 20       # seconds, doubles each retry


def load_documents():
    docs = []

    txt_loader = DirectoryLoader(
        DATA_DIR, glob="**/*.txt", loader_cls=TextLoader, show_progress=True
    )
    docs.extend(txt_loader.load())

    pdf_loader = DirectoryLoader(
        DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True
    )
    docs.extend(pdf_loader.load())

    md_loader = DirectoryLoader(
        DATA_DIR, glob="**/*.md", loader_cls=TextLoader, show_progress=True
    )
    docs.extend(md_loader.load())

    return docs


def embed_batch_with_retry(vectorstore, batch, embeddings, is_first_batch):
    """Embeds one batch, retrying on 429s with exponential backoff."""
    backoff = INITIAL_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if is_first_batch:
                return Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=CHROMA_PERSIST_DIR,
                )
            else:
                vectorstore.add_documents(batch)
                return vectorstore
        except GoogleGenerativeAIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(
                    f"    Rate limited (attempt {attempt}/{MAX_RETRIES}). "
                    f"Waiting {backoff}s before retrying..."
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                raise

    raise RuntimeError(
        "Still rate-limited after multiple retries. This likely means you've hit "
        "today's daily quota (RPD) for this model, not just a per-minute limit. "
        "Check https://ai.dev/rate-limit for your current usage, and either wait "
        "for it to reset (quotas typically reset at midnight Pacific time) or "
        "switch to a different free provider for now."
    )


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

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY
    )

    print(f"Embedding and storing chunks in: {CHROMA_PERSIST_DIR}")

    vectorstore = None
    total = len(chunks)
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        print(f"  Embedding chunks {i + 1}-{min(i + BATCH_SIZE, total)} of {total}...")

        vectorstore = embed_batch_with_retry(
            vectorstore, batch, embeddings, is_first_batch=(vectorstore is None)
        )

        if i + BATCH_SIZE < total:
            time.sleep(DELAY_SECONDS)

    print(f"Done. Vector store now has {vectorstore._collection.count()} vectors.")


if __name__ == "__main__":
    main()