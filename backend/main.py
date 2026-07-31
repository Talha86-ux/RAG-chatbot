from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from chat.routers import chat_router

app = FastAPI(title="Business Knowledge Base Chatbot", version="1.0.0")



# Allow the React dev server to call this API.
# Add your real frontend domain here before deploying to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, tags=["chat"])


@app.get("/health")
def health():
    return {"status": "ok"}