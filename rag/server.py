from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from router import boilerplate, knowledge_base, draft, system

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(draft.router)
app.include_router(knowledge_base.router)
app.include_router(boilerplate.router)
app.include_router(system.router)

app.mount("/", StaticFiles(directory="../ui/dist", html=True), name="ui")
