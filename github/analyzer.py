import json
import litellm
from models.prompts import GITHUB_ANALYZER_PROMPT
from services.rate_limiter import RateLimiter


class GitHubCodeAnalyzer:
    def __init__(self, api_key: str, model: str = "mistral-small-latest", timeout: int = 120, rate_limiter: RateLimiter | None = None, api_base: str | None = None) -> None:
        self.model = f"mistral/{model}"
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.rate_limiter = rate_limiter

    async def analyze_code(self, github_data: dict) -> dict:
        if "error" in github_data:
            return {"error": github_data["error"]}

        context = self._build_context(github_data)

        prompt = GITHUB_ANALYZER_PROMPT.format(context=context)

        if self.rate_limiter:
            self.rate_limiter.wait()

        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
            api_key=self.api_key,
            api_base=self.api_base,
            timeout=self.timeout,
        )

        try:
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": f"Failed to parse LLM response: {e}"}

    def _build_context(self, github_data: dict) -> str:
        context_parts = []

        for repo in github_data.get("repositories", []):
            repo_context = f"Repository: {repo['name']}\n"
            repo_context += f"Description: {repo.get('description', 'N/A')}\n"
            repo_context += f"Language: {repo.get('language', 'N/A')}\n"
            repo_context += f"Stars: {repo.get('stars', 0)}\n"

            if repo.get("readme"):
                repo_context += f"\nREADME:\n{repo['readme'][:1000]}\n"

            if repo.get("files"):
                repo_context += "\nCode samples:\n"
                for file in repo["files"][:3]:
                    repo_context += f"\n--- {file['path']} ---\n{file['content'][:800]}\n"

            context_parts.append(repo_context)

        return "\n".join(context_parts)
