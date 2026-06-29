from openai import AsyncOpenAI
import json
from models.prompts import PROFILE_BUILDER_PROMPT


class ProfileBuilder:
    def __init__(self, api_key: str, model="mistral-small-latest", timeout=120, rate_limiter=None):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
            timeout=timeout
        )
        self.rate_limiter = rate_limiter

    async def generate(self, prompt: str) -> str:
        if self.rate_limiter:
            self.rate_limiter.wait()
            
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ]
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

        if self.rate_limiter:
            self.rate_limiter.wait()
            
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Empty response from LLM")

        try:
            profile = json.loads(content)
            print(f"DEBUG: ProfileBuilder received github_analysis: {github_analysis}")
            if github_analysis:
                print(f"DEBUG: Injecting github_analysis into profile (status: {'error' if 'error' in github_analysis else 'success'})")
                profile["github_analysis"] = github_analysis
            else:
                print("DEBUG: github_analysis is None, nothing to inject")
            return profile
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {content}")
