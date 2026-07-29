import logging
import inspect
from embedding.embedder import MistralEmbedder
from ingestion.loader import ResumeLoader
from db.vector_store import VectorStore
from services.profile_builder import ProfileBuilder
from repositories.profile_repo import ProfileRepository
from github.collector import GitHubDataCollector
from github.analyzer import GitHubCodeAnalyzer
from ingestion.parser import ResumeParser

logger = logging.getLogger(__name__)


class IndexService:
    def __init__(self, embedder: MistralEmbedder, loader: ResumeLoader, vector_store: VectorStore, profile_builder: ProfileBuilder, profile_repository: ProfileRepository, github_collector: GitHubDataCollector | None = None, github_analyzer: GitHubCodeAnalyzer | None = None, resume_parser: ResumeParser | None = None) -> None:
        self.embedder = embedder
        self.loader = loader
        self.vector_store = vector_store
        self.profile_builder = profile_builder
        self.profile_repository = profile_repository
        self.github_collector = github_collector
        self.github_analyzer = github_analyzer
        self.resume_parser = resume_parser

    async def index_folder(self, dir_path: str) -> dict:
        documents = self.loader.load_folder(dir_path)

        existing = set()
        if self.vector_store.collection.count() > 0:
            existing = set(
                m["source"]
                for m in self.vector_store.collection.get(limit=10000)["metadatas"]
            )

        new_docs = [d for d in documents if d["source"] not in existing]

        if new_docs:
            await self.vector_store.add_documents(new_docs, self.embedder)

        all_grouped = self.vector_store.get_all_grouped_by_source()
        new_profiles = []
        for source, chunks in all_grouped.items():
            if not self.profile_repository.profile_exists(source):
                github_analysis = None
                
                if self.resume_parser and self.github_collector and self.github_analyzer:
                    full_text = " ".join(chunks)
                    github_username = self.resume_parser.extract_github_link(full_text)
                    
                    if github_username:
                        try:
                            github_data = await self.github_collector.collect_user_data(github_username)
                            
                            if inspect.iscoroutinefunction(self.github_analyzer.analyze_code):
                                github_analysis = await self.github_analyzer.analyze_code(github_data)
                            else:
                                github_analysis = self.github_analyzer.analyze_code(github_data)
                        
                        except Exception as e:
                            logger.error("GitHub analysis failed for %s: %s", source, e, exc_info=True)
                
                profile = await self.profile_builder.build_profile(chunks, github_analysis)
                self.profile_repository.create_profile(source, profile)
                new_profiles.append(source)

        return {
            "total_files": len(set(d["source"] for d in documents)),
            "new_chunks": len(new_docs),
            "new_profiles": new_profiles,
        }
