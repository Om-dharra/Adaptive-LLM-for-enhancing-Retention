from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .routers import auth
from .database import Base,engine

from api.routers import chat
from api.routers import quiz
from api.routers import analytics

app = FastAPI()

Base.metadata.create_all(bind=engine)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}


app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(auth.router)
app.include_router(analytics.router)