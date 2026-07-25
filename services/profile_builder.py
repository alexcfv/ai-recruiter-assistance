import litellm
import json
from models.prompts import PROFILE_BUILDER_PROMPT


class ProfileBuilder:
    def __init__(self, api_key: str, model="mistral-small-latest", timeout=120, rate_limiter=None, api_base=None):
        self.model = f"mistral/{model}"
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.rate_limiter = rate_limiter

    async def generate(self, prompt: str) -> str:
        if self.rate_limiter:
            self.rate_limiter.wait()

        response = await litellm.acompletion(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            api_key=self.api_key,
            api_base=self.api_base,
            timeout=self.timeout,
        )
        return response.choices[0].message.content or ""

    async def build_profile(self, chunks: list[str], github_analysis: dict = None) -> dict:
        context = "\n".join(chunks)

        github_context = ""
        if github_analysis and "error" not in github_analysis:
            github_context = f"""

GitHub Analysis:
- Code Quality: {github_analysis.get('code_quality', 'N/A')}
- Technical Depth: {github_analysis.get('technical_depth', 'N/A')}
- Architecture Patterns: {', '.join(github_analysis.get('architecture_patterns', []))}
- Key Technologies: {', '.join(github_analysis.get('key_technologies', []))}
- Overall Assessment: {github_analysis.get('overall_assessment', 'N/A')}
"""

        prompt = PROFILE_BUILDER_PROMPT.format(context=context, github_context=github_context)
        profile = await self.complete(prompt, json_mode=True)

        if github_analysis:
            profile["github_analysis"] = github_analysis
        return profile

    async def complete(self, prompt: str, json_mode: bool = False) -> any:
        if self.rate_limiter:
            self.rate_limiter.wait()

        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "api_key": self.api_key,
            "api_base": self.api_base,
            "timeout": self.timeout,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content

        if not content:
            raise ValueError("Empty response from LLM")

        if json_mode:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON from LLM: {content}")
        return content
