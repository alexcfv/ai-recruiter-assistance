import asyncio
import json
from github.mcp_client import GitHubMCPClient


class GitHubDataCollector:
    def __init__(self, mcp_client: GitHubMCPClient):
        self.mcp_client = mcp_client

    async def collect_user_data(self, username: str) -> dict:
        repos_response = await self.mcp_client.get_user_repositories(username)
        
        if not repos_response or not repos_response.content:
            return {"error": "No repositories found"}
        
        repos_data = json.loads(repos_response.content[0].text)
        # MCP GitHub server returns repos in 'items' for search results
        top_repos = repos_data.get("items", repos_data.get("repositories", []))[:3]

        collected_data = {
            "username": username,
            "repositories": []
        }

        for repo in top_repos:
            repo_name = repo.get("name")
            repo_owner = repo.get("owner", {}).get("login", username)
            
            repo_info = {
                "name": repo_name,
                "description": repo.get("description"),
                "stars": repo.get("stargazerCount", 0),
                "language": repo.get("primaryLanguage", {}).get("name"),
                "files": []
            }

            try:
                readme_response = await self.mcp_client.get_file_contents(repo_owner, repo_name, "README.md")
                if readme_response and readme_response.content:
                    readme_data = json.loads(readme_response.content[0].text)
                    repo_info["readme"] = readme_data.get("content", "")[:2000]
            except:
                repo_info["readme"] = ""

            try:
                tree_response = await self.mcp_client.list_repository_tree(repo_owner, repo_name)
                if tree_response and tree_response.content:
                    tree_data = json.loads(tree_response.content[0].text)
                    files = tree_data.get("tree", [])
                    
                    code_files = [f for f in files if f.get("path", "").endswith((".py", ".js", ".ts", ".java", ".go"))][:5]
                    
                    for file_info in code_files:
                        file_path = file_info.get("path")
                        try:
                            file_response = await self.mcp_client.get_file_contents(repo_owner, repo_name, file_path)
                            if file_response and file_response.content:
                                file_data = json.loads(file_response.content[0].text)
                                repo_info["files"].append({
                                    "path": file_path,
                                    "content": file_data.get("content", "")[:1500]
                                })
                        except:
                            pass
            except:
                pass

            collected_data["repositories"].append(repo_info)

        return collected_data
