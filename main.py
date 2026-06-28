from embedding.embedder import MistralEmbedder
from db.vector_store import VectorStore
from ingestion.loader import ResumeLoader
from ingestion.parser import ResumeParser
from services.explainer import LLMExplainer
from services.index_service import IndexService
from services.query_service import QueryService
from db.sqlite.migrations import init_db
from repositories.profile_repo import ProfileRepository
from services.profile_builder import ProfileBuilder
from services.profile_reranker import ProfileReranker
from services.rate_limiter import RateLimiter
from github.mcp_client import GitHubMCPClient
from github.collector import GitHubDataCollector
from github.analyzer import GitHubCodeAnalyzer
from config import load_config
import chromadb
import asyncio


async def create_github_client(cfg):
    github_cfg = cfg.get("github", {})
    if not github_cfg:
        return None
    
    server_command = github_cfg.get("mcp_server_command")
    env = github_cfg.get("env", {})
    
    if not server_command:
        return None
    
    client = GitHubMCPClient(server_command, env)
    await client.__aenter__()
    return client


def main():
    cfg = load_config()
    init_db()
    api_key_mistral = cfg["api"]["mistral_key"]

    rate_limiter = RateLimiter(min_interval=cfg["rate_limiter"]["min_interval"])

    embedder = MistralEmbedder(api_key_mistral, model=cfg["embedder"]["model"], timeout=cfg["embedder"]["timeout"], rate_limiter=rate_limiter)
    explainer = LLMExplainer(api_key_mistral, model=cfg["explainer"]["model"], timeout=cfg["explainer"]["timeout"], rate_limiter=rate_limiter)
    loader = ResumeLoader()
    parser = ResumeParser()
    profile_repository = ProfileRepository()
    profile_builder = ProfileBuilder(api_key_mistral, model=cfg["profile_builder"]["model"], timeout=cfg["profile_builder"]["timeout"], rate_limiter=rate_limiter)
    profile_reranker = ProfileReranker(api_key_mistral, model=cfg["reranker"]["model"], timeout=cfg["reranker"]["timeout"], rate_limiter=rate_limiter)
    client = chromadb.PersistentClient(path="./chromadb")
    vector_store = VectorStore(client)

    github_client = None
    github_collector = None
    github_analyzer = None
    
    try:
        github_client = asyncio.run(create_github_client(cfg))
        if github_client:
            github_collector = GitHubDataCollector(github_client)
            github_analyzer = GitHubCodeAnalyzer(api_key_mistral, model=cfg["profile_builder"]["model"], timeout=cfg["profile_builder"]["timeout"], rate_limiter=rate_limiter)
            print("GitHub MCP client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize GitHub MCP client: {e}")
        print("Continuing without GitHub analysis...")

    index_service = IndexService(embedder, loader, vector_store, profile_builder, profile_repository, github_collector, github_analyzer, parser)
    query_service = QueryService(embedder, vector_store, explainer, profile_repository, profile_reranker)

    dir_path = input("Enter resumes dir path: ")
    result = index_service.index_folder(dir_path)
    print(f"Indexed {result['new_chunks']} chunks, {len(result['new_profiles'])} new profiles")

    query = input("Enter search query: ")
    search_result = query_service.search(query)

    for c in search_result["candidates"]:
        print(f"\n--- {c['source']} (score: {c['score']:.4f}) ---")
        print(c["explanation"])
    
    if github_client:
        asyncio.run(github_client.__aexit__(None, None, None))


if __name__ == "__main__":
    main()
