from openai import OpenAI
import json


class ProfileBuilder:
    def __init__(self, api_key: str, model="mistral-small-latest", timeout=120, rate_limiter=None):
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
            timeout=timeout
        )
        self.rate_limiter = rate_limiter

    def build_profile(self, chunks: list[str], github_analysis: dict = None) -> dict:
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

        prompt = f"""
Extract a structured candidate profile from the resume text below.

Return valid JSON with EXACTLY these fields:
- "summary": string
- "skills": flat list of strings, e.g. ["Python", "Django", "FastAPI", "Docker"]
- "experience": list of objects, each with "role", "company", "description"
- "education": list of objects, each with "degree", "institution"
- "projects": list of objects, each with "name", "description"
- "github_analysis": object with fields "code_quality", "technical_depth", "architecture_patterns", "key_technologies", "overall_assessment" (if available, otherwise null)

Rules:
- "skills" MUST be a flat array of strings. NEVER group skills into categories.
- All string values use double quotes.

Resume:
{context}
{github_context}
"""

        if self.rate_limiter:
            self.rate_limiter.wait()
        response = self.client.chat.completions.create(
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
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from LLM: {content}")
