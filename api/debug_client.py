import logging
import asyncio
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.types import CallToolResult
import sys
import json

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()


class DebugClient:
    """Debug client for investigating MCP server responses."""

    def __init__(
        self,
        server_url: str = "http://localhost:8080/aa9a7ec5/sse",
        api_key: str = "sk-hive-api01-MzYwMzNmN2ItMmE0MC00MjA0LWE0MzctZTdiNDk2YmI2YjQ4-YjcyNjNiAAA"
    ):
        self.server_url = server_url
        self.api_key = api_key
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(self) -> None:
        try:
            logger.info(f"Connecting to: {self.server_url}")
            logger.info(f"Using API key: {'***' + self.api_key[-8:] if self.api_key and len(self.api_key) > 8 else 'None'}")
            
            # Create headers dict with API key
            headers = {"x-api-key": self.api_key} if self.api_key else {}
            
            sse_transport = await self.exit_stack.enter_async_context(
                sse_client(url=self.server_url, headers=headers)
            )
            stdio, write = sse_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            logger.info("Initializing session...")
            await self.session.initialize()
            logger.info("Session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to {self.server_url}: {e}")
            await self._safe_cleanup()
            raise

    async def debug_server_capabilities(self) -> None:
        """Debug what capabilities the server provides."""
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        logger.info("=== SERVER CAPABILITIES DEBUG ===")
        
        try:
            # List prompts
            logger.info("Fetching prompts...")
            prompts_response = await self.session.list_prompts()
            logger.info(f"Prompts response type: {type(prompts_response)}")
            logger.info(f"Prompts response: {prompts_response}")
            logger.info(f"Number of prompts: {len(prompts_response.prompts)}")
            if prompts_response.prompts:
                for i, prompt in enumerate(prompts_response.prompts):
                    logger.info(f"Prompt {i}: {prompt}")
            else:
                logger.warning("No prompts found")
                
        except Exception as e:
            logger.error(f"Error fetching prompts: {e}")
        
        try:
            # List tools
            logger.info("Fetching tools...")
            tools_response = await self.session.list_tools()
            logger.info(f"Tools response type: {type(tools_response)}")
            logger.info(f"Tools response: {tools_response}")
            logger.info(f"Number of tools: {len(tools_response.tools)}")
            if tools_response.tools:
                for i, tool in enumerate(tools_response.tools):
                    logger.info(f"Tool {i}: {tool}")
            else:
                logger.warning("No tools found")
                
        except Exception as e:
            logger.error(f"Error fetching tools: {e}")
        
        try:
            # List resources
            logger.info("Fetching resources...")
            resources_response = await self.session.list_resources()
            logger.info(f"Resources response type: {type(resources_response)}")
            logger.info(f"Resources response: {resources_response}")
            logger.info(f"Number of resources: {len(resources_response.resources)}")
            if resources_response.resources:
                for i, resource in enumerate(resources_response.resources):
                    logger.info(f"Resource {i}: {resource}")
            else:
                logger.warning("No resources found")
                
        except Exception as e:
            logger.error(f"Error fetching resources: {e}")

    async def test_raw_communication(self) -> None:
        """Test raw communication with the server."""
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        logger.info("=== RAW COMMUNICATION TEST ===")
        
        try:
            # Try to get server info if available
            logger.info("Session object details:")
            logger.info(f"Session type: {type(self.session)}")
            logger.info(f"Session attributes: {dir(self.session)}")
            
            # Check if we can access the underlying transport
            if hasattr(self.session, '_read_stream'):
                logger.info("Session has _read_stream")
            if hasattr(self.session, '_write_stream'):
                logger.info("Session has _write_stream")
                
        except Exception as e:
            logger.error(f"Error in raw communication test: {e}")

    async def _safe_cleanup(self) -> None:
        """Perform safe cleanup avoiding the cancel scope issue."""
        try:
            await asyncio.wait_for(self.exit_stack.aclose(), timeout=5.0)
        except (RuntimeError, asyncio.TimeoutError) as e:
            if "cancel scope" in str(e) or isinstance(e, asyncio.TimeoutError):
                logger.warning(f"Handled cleanup issue during shutdown: {e}")
                self.exit_stack = AsyncExitStack()
            else:
                logger.error(f"Unexpected error during cleanup: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}")

    async def cleanup(self) -> None:
        """Clean up all sessions with proper error handling."""
        await self._safe_cleanup()


async def main():
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        # Extract API key from URL if present
        api_key = None
        if "x-api-key=" in server_url:
            parts = server_url.split("x-api-key=")
            if len(parts) > 1:
                api_key = parts[1].split("&")[0]  # Handle multiple query params
                server_url = parts[0].rstrip("?&")  # Remove API key from URL
        client = DebugClient(server_url=server_url, api_key=api_key)
    else:
        # Default values
        server_url = "http://localhost:8080/aa9a7ec5/sse"
        api_key = "sk-hive-api01-MzYwMzNmN2ItMmE0MC00MjA0LWE0MzctZTdiNDk2YmI2YjQ4-YjcyNjNiAAA"
        client = DebugClient(server_url=server_url, api_key=api_key)
    
    try:
        await client.connect()
        await client.debug_server_capabilities()
        await client.test_raw_communication()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 
