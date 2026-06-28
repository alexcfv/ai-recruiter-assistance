from openai import OpenAI
import json


class GitHubCodeAnalyzer:
    def __init__(self, api_key: str, model="mistral-small-latest", timeout=120, rate_limiter=None):
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
            timeout=timeout
        )
        self.rate_limiter = rate_limiter

    def analyze_code(self, github_data: dict) -> dict:
        if "error" in github_data:
            return {"error": github_data["error"]}

        context = self._build_context(github_data)

        prompt = f"""
Analyze the following GitHub repositories and provide a technical assessment of the developer.

Return valid JSON with EXACTLY these fields:
- "code_quality": string (assessment of code cleanliness, structure, and best practices)
- "technical_depth": string (assessment of complexity and sophistication of solutions)
- "architecture_patterns": list of strings (identified design patterns and architectural approaches)
- "key_technologies": list of strings (main technologies and frameworks used)
- "overall_assessment": string (brief summary of technical capabilities)

Rules:
- Focus on code quality, not quantity
- Assess real technical depth, not just framework usage
- All string values use double quotes

GitHub Data:
{context}
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
