import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GitHubMCPClient:
    def __init__(self, server_command: str, env: dict | None = None):
        parts = server_command.split()
        self.server_params = StdioServerParameters(
            command=parts[0],
            args=parts[1:],
            env={**os.environ, **(env or {})},
        )
        self.session: ClientSession | None = None
        self._stack: AsyncExitStack | None = None

    async def __aenter__(self):
        print("[MCP] Starting stdio_client...")
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(
            stdio_client(self.server_params)
        )
        print("[MCP] stdio ready, opening ClientSession...")
        self.session = await self._stack.enter_async_context(
            ClientSession(read, write)
        )
        print("[MCP] Initializing session...")
        await self.session.initialize()
        print("[MCP] Session initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def get_user_repositories(self, username: str):
        return await self.session.call_tool(
            "search_repositories", {"query": f"user:{username} sort:stars"}
        )

    async def get_file_contents(self, owner: str, repo: str, path: str):
        return await self.session.call_tool(
            "get_file_contents", {"owner": owner, "repo": repo, "path": path}
        )

    async def list_repository_tree(self, owner: str, repo: str, path: str = "."):
        return await self.session.call_tool(
            "list_repository_tree", {"owner": owner, "repo": repo, "path": path}
        )