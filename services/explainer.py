import json
import litellm
from models.search_results import SearchResultItem
from models.prompts import EXPLAINER_PROMPT
from services.rate_limiter import RateLimiter


class LLMExplainer:
    def __init__(self, api_key: str, model: str = "mistral-small-2603", timeout: int = 60, rate_limiter: RateLimiter | None = None, api_base: str | None = None) -> None:
        self.model = f"mistral/{model}"
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.rate_limiter = rate_limiter

    async def explain(self, query: str, candidate: str, vectors: list[SearchResultItem], github_analysis: dict = None) -> str:
        vectors.sort(key=lambda x: x.distance)

        candidate_chunks = [r.text for r in vectors if r.source == candidate]

        context = "\n".join(candidate_chunks[:3])

        github_context = "None"
        if github_analysis and "error" not in github_analysis:
            github_context = json.dumps(github_analysis, ensure_ascii=False, indent=2)

        prompt = EXPLAINER_PROMPT.format(
            query=query,
            context=context,
            github_context=github_context
        )

        if self.rate_limiter:
            self.rate_limiter.wait()
        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a technical recruiter. Answer in user language."},
                {"role": "user", "content": prompt}
            ],
            api_key=self.api_key,
            api_base=self.api_base,
            timeout=self.timeout,
        )

        return response.choices[0].message.content
