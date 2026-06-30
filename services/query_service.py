import asyncio
import json
from services.ranking import find_best_candidates
from models.prompts import QUERY_VALIDATOR_PROMPT


class QueryService:
    def __init__(self, embedder, vector_store, explainer, profile_repository, profile_reranker, llm_client=None):
        self.embedder = embedder
        self.vector_store = vector_store
        self.explainer = explainer
        self.profile_repository = profile_repository
        self.profile_reranker = profile_reranker
        self.llm_client = llm_client

    async def _validate_query(self, query: str) -> dict:
        if not self.llm_client:
            return {"is_valid": True, "reason": ""}

        prompt = QUERY_VALIDATOR_PROMPT.format(query=query)
        try:
            result = await self.llm_client.complete(prompt, json_mode=True)
            if isinstance(result, str):
                result = json.loads(result)
            return result
        except Exception as e:
            return {"is_valid": True, "reason": ""}

    async def search(self, query: str, top_k: int = 3) -> dict:
        validation = await self._validate_query(query)
        if not validation.get("is_valid", True):
            return {
                "query": query,
                "candidates": [],
                "error": validation.get("reason", "Invalid query")
            }

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
