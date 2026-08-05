from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import GOOGLE_API_KEY, CHROMA_PERSIST_DIR, EMBEDDING_MODEL, CHAT_MODEL

SYSTEM_PROMPT = """You are a helpful assistant answering questions about our company's
internal knowledge base. Use ONLY the context below to answer the question.

Rules:
- If the answer isn't in the context, say you don't have that information — never make something up.
- Be concise and direct.
- If helpful, mention which document/section the info came from.
- Use the conversation so far to understand follow-up questions, but still answer only from the provided context.

Conversation so far:
{chat_history}

Context:
{context}
"""

PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "{question}")]
)


def format_docs(docs):
    return "\n\n---\n\n".join(
        f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for d in docs
    )


def format_history(history):
    if not history:
        return "(no prior messages)"
    speaker = {"user": "User", "bot": "Assistant"}
    return "\n".join(f"{speaker.get(m['role'], m['role'])}: {m['content']}" for m in history)


def get_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
    return Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embeddings)


def build_rag_chain(k: int = 4):
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.2)

    chain = (
        {
            "context": (lambda x: x["question"]) | retriever | format_docs,
            "question": lambda x: x["question"],
            "chat_history": lambda x: format_history(x.get("history", [])),
        }
        | PROMPT
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def answer_question(question: str, k: int = 4, history=None):
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(question)

    chain, _ = build_rag_chain(k=k)
    answer = chain.invoke({"question": question, "history": history or []})

    seen = set()
    sources = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        if src not in seen:
            seen.add(src)
            sources.append({"source": src, "snippet": d.page_content[:200]})

    return answer, sources