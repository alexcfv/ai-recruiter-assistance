import asyncio
import json
from services.ranking import find_best_candidates


class QueryService:
    def __init__(self, embedder, vector_store, explainer, profile_repository, profile_reranker):
        self.embedder = embedder
        self.vector_store = vector_store
        self.explainer = explainer
        self.profile_repository = profile_repository
        self.profile_reranker = profile_reranker

    async def search(self, query: str, top_k: int = 3) -> dict:
        results = await asyncio.to_thread(self.vector_store.search, query, self.embedder, k=10)
        ranked = find_best_candidates(results)

        sources = [s for s, _ in ranked]
        profiles = await asyncio.to_thread(self.profile_repository.get_by_sources, sources)

        reranked = await asyncio.to_thread(self.profile_reranker.rerank, query, ranked, profiles)

        candidates = []
        for source, score, explanation in reranked[:top_k]:
            full_explanation = await asyncio.to_thread(self.explainer.explain, query, source, results)
            candidates.append({
                "source": source,
                "score": score,
                "explanation": full_explanation,
                "profile": profiles.get(source, {}).get("profile", {}) if isinstance(profiles.get(source, {}).get("profile"), dict) else json.loads(profiles.get(source, {}).get("profile", "{}"))
            })

        return {
            "query": query,
            "candidates": candidates,
        }
