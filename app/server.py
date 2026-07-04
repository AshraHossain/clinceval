import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.observability import get_logger, install_request_logging, log_query
from app.pipeline import run_pipeline
from app.rate_limiter import rate_limit
from app.reliability import call_with_timeout
from app.security import validate_query

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
PIPELINE_TIMEOUT_S = 30.0

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the retriever (Chroma + embedding model) so the first user request
    # isn't a 10-second cold start
    from app.retriever import retrieve
    retrieve("warmup", k=1)
    app.state.ready = True
    yield
    app.state.ready = False


app = FastAPI(title="ClinCalc-Eval demo", lifespan=lifespan)
app.state.ready = False
install_request_logging(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("ALLOWED_ORIGIN", "http://localhost:8000")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
)


class RecommendRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict:
    """Liveness: process is up."""
    return {"status": "ok"}


@app.get("/ready")
def ready(request: Request) -> dict:
    """Readiness: retriever warmed, safe to route traffic (K8s readinessProbe)."""
    if not request.app.state.ready:
        raise HTTPException(status_code=503, detail="retriever not warmed up yet")
    return {"status": "ready"}


@app.post("/api/recommend")
def recommend(req: RecommendRequest, request: Request, api_key: str = Depends(rate_limit)) -> dict:
    try:
        query = validate_query(req.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    log_query(logger, query, request_id=request.headers.get("X-Request-ID"))
    try:
        return call_with_timeout(run_pipeline, PIPELINE_TIMEOUT_S, query, k=3)
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pipeline error: {exc}")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
