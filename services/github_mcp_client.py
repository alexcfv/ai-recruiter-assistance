import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GitHubMCPClient:
    def __init__(self, server_command: str, env: dict = None):
        self.server_params = StdioServerParameters(
            command=server_command.split()[0],
            args=server_command.split()[1:],
            env={**os.environ, **(env or {})}
        )
        self.session = None
        self._client_context = None

    async def __aenter__(self):
        self._client_context = stdio_client(self.server_params)
        read, write = await self._client_context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_user_repositories(self, username: str):
        response = await self.session.call_tool("search_repositories", {"query": f"user:{username} sort:stars"})
        return response

    async def get_file_contents(self, owner: str, repo: str, path: str):
        response = await self.session.call_tool("get_file_contents", {"owner": owner, "repo": repo, "path": path})
        return response

    async def list_repository_tree(self, owner: str, repo: str, path: str = "."):
        response = await self.session.call_tool("list_repository_tree", {"owner": owner, "repo": repo, "path": path})
        return response
