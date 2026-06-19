from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, emails, threads, chat, compose, sync, embed

app = FastAPI(title="Gmail Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(embed.router, prefix="/embed", tags=["embed"])
app.include_router(emails.router, prefix="/emails", tags=["emails"])
app.include_router(threads.router, prefix="/threads", tags=["threads"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(compose.router, prefix="/compose", tags=["compose"])


@app.get("/health")
def health():
    return {"status": "ok"}
