import os
import logging
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class GitHubMCPClient:
    def __init__(self, server_command: str, env: dict | None = None) -> None:
        parts = server_command.split()
        self.server_params = StdioServerParameters(
            command=parts[0],
            args=parts[1:],
            env={**os.environ, **(env or {})},
        )
        self.session: ClientSession | None = None
        self._stack: AsyncExitStack | None = None

    async def __aenter__(self) -> "GitHubMCPClient":
        logger.info("Starting stdio client...")
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(
            stdio_client(self.server_params)
        )
        logger.info("Stdio ready, opening ClientSession...")
        self.session = await self._stack.enter_async_context(
            ClientSession(read, write)
        )
        logger.info("Initializing session...")
        await self.session.initialize()
        logger.info("Session initialized")
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def get_user_repositories(self, username: str) -> object:
        return await self.session.call_tool(
            "search_repositories", {"query": f"user:{username} sort:stars"}
        )

    async def get_file_contents(self, owner: str, repo: str, path: str) -> object:
        return await self.session.call_tool(
            "get_file_contents", {"owner": owner, "repo": repo, "path": path}
        )

    async def list_repository_tree(self, owner: str, repo: str, path: str = ".") -> object:
        return await self.session.call_tool(
            "list_repository_tree", {"owner": owner, "repo": repo, "path": path}
        )