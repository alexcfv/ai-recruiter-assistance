from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from embedding.embedder import MistralEmbedder
from db.vector_store import VectorStore
from ingestion.loader import ResumeLoader
from ingestion.parser import ResumeParser
from services.explainer import LLMExplainer
from services.index_service import IndexService
from services.query_service import QueryService
from services.analytics_service import AnalyticsService
from db.sqlite.migrations import init_db
from repositories.profile_repo import ProfileRepository
from services.profile_builder import ProfileBuilder
from services.profile_reranker import ProfileReranker
from services.rate_limiter import RateLimiter
from github.mcp_client import GitHubMCPClient
from github.collector import GitHubDataCollector
from github.analyzer import GitHubCodeAnalyzer
from config import load_config
from api.endpoints import search, analytics, index

import chromadb
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    init_db()
    api_key_mistral = cfg["api"]["mistral_key"]
    llm_base_url = cfg["api"]["llm_base_url"]
    rate_limiter = RateLimiter(min_interval=cfg["rate_limiter"]["min_interval"])

    embedder = MistralEmbedder(api_key_mistral, model=cfg["embedder"]["model"], timeout=cfg["embedder"]["timeout"], rate_limiter=rate_limiter, api_base=llm_base_url)
    explainer = LLMExplainer(api_key_mistral, model=cfg["explainer"]["model"], timeout=cfg["explainer"]["timeout"], rate_limiter=rate_limiter, api_base=llm_base_url)
    loader = ResumeLoader()
    parser = ResumeParser()
    profile_repository = ProfileRepository()
    profile_builder = ProfileBuilder(api_key_mistral, model=cfg["profile_builder"]["model"], timeout=cfg["profile_builder"]["timeout"], rate_limiter=rate_limiter, api_base=llm_base_url)
    profile_reranker = ProfileReranker(api_key_mistral, model=cfg["reranker"]["model"], timeout=cfg["reranker"]["timeout"], rate_limiter=rate_limiter, api_base=llm_base_url)
    client = chromadb.PersistentClient(path="./chromadb")
    vector_store = VectorStore(client)
    
    analytics_service = AnalyticsService(llm_client=profile_builder)

    github_cfg = cfg.get("github", {})
    server_command = github_cfg.get("mcp_server_command")
    github_env = github_cfg.get("env", {})

    github_collector = None
    github_analyzer = None

    if server_command:
        github_client = GitHubMCPClient(server_command, github_env)
        try:
            await github_client.__aenter__()
            github_collector = GitHubDataCollector(github_client)
            github_analyzer = GitHubCodeAnalyzer(api_key_mistral, model=cfg["profile_builder"]["model"], timeout=cfg["profile_builder"]["timeout"], rate_limiter=rate_limiter, api_base=llm_base_url)
            app.state.github_client = github_client
            print("GitHub MCP client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize GitHub MCP client: {e}")

    app.state.index_service = IndexService(embedder, loader, vector_store, profile_builder, profile_repository, github_collector, github_analyzer, parser)
    app.state.query_service = QueryService(embedder, vector_store, explainer, profile_repository, profile_reranker, llm_client=profile_builder)
    app.state.analytics_service = analytics_service

    yield

    if hasattr(app.state, "github_client"):
        await app.state.github_client.__aexit__(None, None, None)

app = FastAPI(title="AI Recruiter API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(index.router, prefix="/api/index", tags=["index"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

static_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
