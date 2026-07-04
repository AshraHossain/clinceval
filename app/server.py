import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.pipeline import run_pipeline

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the retriever (Chroma + embedding model) so the first user request
    # isn't a 10-second cold start
    from app.retriever import retrieve
    retrieve("warmup", k=1)
    yield


app = FastAPI(title="ClinCalc-Eval demo", lifespan=lifespan)


class RecommendRequest(BaseModel):
    query: str


@app.post("/api/recommend")
def recommend(req: RecommendRequest) -> dict:
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query must not be empty")
    try:
        return run_pipeline(query, k=3)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pipeline error: {exc}")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
