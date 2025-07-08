"""
Main entry point for the Python backend.
This module handles Tauri native command invocations.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Ensure UTF-8 encoding for stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Set environment variables for consistent encoding
os.environ["PYTHONIOENCODING"] = "utf-8"

# Import our infrastructure modules
from db import (
    BookmarkOperations,
    ChatOperations,
    HistoryOperations,
    close_database,
    init_database,
)
from llm import get_conversation_context, get_ollama_client, get_prompt_builder
from utils import (
    get_logger,
    init_config,
    init_logging,
    log_command_error,
    log_command_start,
    log_command_success,
)

# Initialize configuration and logging
config = init_config()
init_logging()
logger = get_logger("main")


class CommandHandler:
    """Handles incoming commands from Tauri frontend."""

    def __init__(self):
        """Initialize command handler with available commands."""
        self.commands = {
            "init_database": self.init_database_command,
            "chat_with_llm": self.chat_with_llm_command,
            "save_bookmark": self.save_bookmark_command,
            "get_chat_history": self.get_chat_history_command,
            "get_bookmarks": self.get_bookmarks_command,
            "search_bookmarks": self.search_bookmarks_command,
            "get_browser_history": self.get_browser_history_command,
            "add_history_entry": self.add_history_entry_command,
            "hello": self.hello_command,  # Keep for testing
            "process_url": self.process_url,  # Legacy command
            "extract_page_content": self.process_url,  # Alias for process_url
            "get_browser_data": self.get_browser_data,  # Legacy command
            "analyze_content": self.analyze_content,  # Legacy command
            "summarize_page": self.summarize_page_command,
            "search_web": self.search_web_command,
        }
        # Check if the database is already initialized by verifying that it
        # exists and is accessible
        self._database_initialized = self._check_database_state()

    def _check_database_state(self) -> bool:
        """Check if database is already initialized and accessible."""
        try:
            # Import here to avoid circular imports
            from db.database import db_manager

            # Check if the database manager has an active engine
            if db_manager.engine is None:
                # Try to initialize with default path if not already done
                db_manager.initialize()

            # Test database connection by trying to get session
            if db_manager.SessionLocal is not None:
                with db_manager.get_session():
                    pass  # Just test if we can get a session
                logger.info("Database state check: initialized and accessible")
                return True
            else:
                logger.info("Database state check: not initialized")
                return False

        except Exception as e:
            logger.warning(f"Database state check failed: {str(e)}")
            return False

    async def init_database_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the database."""
        try:
            db_path = payload.get("db_path")
            success = init_database(db_path)

            if success:
                self._database_initialized = True
                logger.info("Database initialized successfully")
                return {
                    "success": True,
                    "message": "Database initialized successfully",
                    "db_path": db_path,
                }
            else:
                return {"success": False, "error": "Failed to initialize database"}
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def chat_with_llm_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a chat message with the LLM."""
        try:
            message = payload.get("message")
            session_id = payload.get("session_id", "default")

            if not message:
                return {"success": False, "error": "No message provided"}

            # Get conversation context
            context = get_conversation_context(session_id)

            # Add user message to context
            context.add_message("user", message)

            # Build system prompt
            prompt_builder = get_prompt_builder()
            system_prompt = prompt_builder.build_chat_prompt(message)

            # Get conversation messages for LLM
            messages = [
                {"role": "system", "content": system_prompt}
            ] + context.get_context_messages()

            # Get LLM response
            client = await get_ollama_client()
            result = await client.chat_completion(messages)

            if result["success"]:
                response_content = result["message"].get("content", "")

                # Add assistant response to context
                context.add_message("assistant", response_content)

                # Save both messages to database
                if self._database_initialized:
                    await ChatOperations.save_message(message, "user", session_id)
                    await ChatOperations.save_message(
                        response_content, "assistant", session_id
                    )

                return {
                    "success": True,
                    "response": response_content,
                    "session_id": session_id,
                    "model": result.get("model"),
                    "context_summary": context.get_context_summary(),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown LLM error"),
                    "session_id": session_id,
                }

        except Exception as e:
            logger.error(f"Chat command error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": payload.get("session_id", "default"),
            }

    async def save_bookmark_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Save a bookmark."""
        try:
            url = payload.get("url")
            title = payload.get("title")
            content = payload.get("content")
            tags = payload.get("tags")
            folder = payload.get("folder", "default")

            if not url:
                return {"success": False, "error": "No URL provided"}

            if not self._database_initialized:
                return {"success": False, "error": "Database not initialized"}

            bookmark = await BookmarkOperations.save_bookmark(
                url=url, title=title, content=content, tags=tags, folder=folder
            )

            if bookmark:
                return {
                    "success": True,
                    "bookmark_id": bookmark.id,
                    "message": "Bookmark saved successfully",
                }
            else:
                return {"success": False, "error": "Failed to save bookmark"}

        except Exception as e:
            logger.error(f"Save bookmark error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_chat_history_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get chat history for a session."""
        try:
            session_id = payload.get("session_id", "default")
            limit = payload.get("limit", 50)

            if not self._database_initialized:
                return {"success": False, "error": "Database not initialized"}

            history = await ChatOperations.get_chat_history(session_id, limit)

            return {
                "success": True,
                "history": history,
                "session_id": session_id,
                "count": len(history),
            }

        except Exception as e:
            logger.error(f"Get chat history error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_bookmarks_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get bookmarks."""
        try:
            folder = payload.get("folder")
            limit = payload.get("limit", 100)

            if not self._database_initialized:
                return {"success": False, "error": "Database not initialized"}

            bookmarks = await BookmarkOperations.get_bookmarks(folder, limit)

            return {"success": True, "bookmarks": bookmarks, "count": len(bookmarks)}

        except Exception as e:
            logger.error(f"Get bookmarks error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def search_bookmarks_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Search bookmarks."""
        try:
            query = payload.get("query")
            limit = payload.get("limit", 50)

            if not query:
                return {"success": False, "error": "No search query provided"}

            if not self._database_initialized:
                return {"success": False, "error": "Database not initialized"}

            results = await BookmarkOperations.search_bookmarks(query, limit)

            return {
                "success": True,
                "results": results,
                "query": query,
                "count": len(results),
            }

        except Exception as e:
            logger.error(f"Search bookmarks error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_browser_history_command(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get browser history."""
        try:
            session_id = payload.get("session_id")
            limit = payload.get("limit", 100)

            if not self._database_initialized:
                return {"success": False, "error": "Database not initialized"}

            history = await HistoryOperations.get_history(session_id, limit)

            return {"success": True, "history": history, "count": len(history)}

        except Exception as e:
            logger.error(f"Get browser history error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_history_entry_command(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a browser history entry."""
        try:
            url = payload.get("url")
            title = payload.get("title")
            session_id = payload.get("session_id", "default")

            if not url:
                return {"success": False, "error": "No URL provided"}

            if not self._database_initialized:
                return {"success": False, "error": "Database not initialized"}

            success = await HistoryOperations.add_history_entry(url, title, session_id)

            if success:
                return {"success": True, "message": "History entry added successfully"}
            else:
                return {"success": False, "error": "Failed to add history entry"}

        except Exception as e:
            logger.error(f"Add history entry error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def hello_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test command to verify communication."""
        name = payload.get("name", "World")
        return {
            "success": True,
            "message": f"Hello, {name}! Backend is working.",
            "timestamp": payload.get("timestamp"),
            "database_initialized": self._database_initialized,
        }

    async def process_url(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a URL for content extraction using async content extractor."""
        url = payload.get("url")
        if not url:
            return {"success": False, "error": "No URL provided"}

        try:
            # Import the content extractor
            from agents.content_extractor import ContentExtractor

            # Normalize URL
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # Use the async content extractor
            async with ContentExtractor() as extractor:
                result = await extractor.extract_content(url)

                if result["success"]:
                    # Format response for compatibility with existing frontend code
                    return {
                        "success": True,
                        "url": result["url"],
                        "title": result["title"],
                        "content": result["text"],
                        "description": result.get("description", ""),
                        "links": result.get("links", []),
                        "images": result.get("images", []),
                        "headings": result.get("headings", []),
                        "metadata": {
                            "status_code": result.get("status_code"),
                            "content_type": result.get("content_type"),
                            "size": result.get("size"),
                        },
                    }
                else:
                    return result  # Return the error result as-is

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return {"success": False, "error": f"Processing error: {str(e)}"}

    async def get_browser_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy: Get browser history or bookmarks."""
        data_type = payload.get("type", "history")

        # Redirect to new commands
        if data_type == "history":
            return await self.get_browser_history_command(payload)
        elif data_type == "bookmarks":
            return await self.get_bookmarks_command(payload)
        else:
            return {"success": False, "error": f"Unknown data type: {data_type}"}

    async def analyze_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze arbitrary content using the LLM."""
        content = payload.get("content")
        if not content:
            return {"success": False, "error": "No content provided"}

        url = payload.get("url", "")
        title = payload.get("title", "")

        try:
            prompt_builder = get_prompt_builder()
            prompt = prompt_builder.build_bookmark_analysis_prompt(url, title, content)

            client = await get_ollama_client()
            llm_result = await client.chat_completion(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content[:2000]},
                ]
            )

            if llm_result["success"]:
                analysis_text = llm_result["message"].get("content", "")
                return {
                    "success": True,
                    "analysis": analysis_text,
                    "model": llm_result.get("model"),
                }
            else:
                return {
                    "success": False,
                    "error": llm_result.get("error", "LLM error"),
                }

        except Exception as e:
            logger.error(f"Analyze content error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def summarize_page_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a URL and return an LLM summary."""
        url = payload.get("url")
        if not url:
            return {"success": False, "error": "No URL provided"}

        try:
            from agents.content_extractor import ContentExtractor
            from db.operations import SummaryOperations

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            async with ContentExtractor() as extractor:
                result = await extractor.extract_content(url)

            if not result.get("success"):
                return result

            title = result.get("title", "")
            text = result.get("text", "")

            prompt_builder = get_prompt_builder()
            prompt = prompt_builder.build_summarization_prompt(url, title, text)

            client = await get_ollama_client()
            llm_result = await client.chat_completion(
                [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text[:2000]},
                ]
            )

            if llm_result["success"]:
                summary_text = llm_result["message"].get("content", "")

                if self._database_initialized:
                    await SummaryOperations.save_summary(
                        url, summary_text, text, llm_result.get("model")
                    )

                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "summary": summary_text,
                    "model": llm_result.get("model"),
                }
            else:
                return {"success": False, "error": llm_result.get("error", "LLM error")}

        except Exception as e:
            logger.error(f"Summarize page error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def search_web_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Search the web using DuckDuckGo."""
        query = payload.get("query")
        max_results = int(payload.get("max_results", 5))

        if not query:
            return {"success": False, "error": "No query provided"}

        try:
            from agents.search_agent import SearchAgent

            agent = SearchAgent()
            results = await agent.search(query, max_results=max_results)

            return {"success": True, "results": results, "count": len(results)}
        except Exception as e:  # pragma: no cover - network errors
            logger.error(f"Search web error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def handle_command(
        self, command: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle incoming command with proper logging and error handling."""
        session_id = payload.get("session_id", "default")
        start_time = time.time()

        # Log command start
        log_command_start(command, payload, session_id)

        if command not in self.commands:
            error_msg = f"Unknown command: {command}"
            log_command_error(command, error_msg, session_id)
            return {"success": False, "error": error_msg}

        try:
            result = await self.commands[command](payload)
            duration = time.time() - start_time

            if result.get("success", False):
                log_command_success(command, duration, session_id)
            else:
                log_command_error(
                    command, result.get("error", "Unknown error"), session_id
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            log_command_error(command, error_msg, session_id)
            logger.error(f"Unhandled error in command '{command}': {error_msg}")
            return {"success": False, "error": error_msg}


async def main():
    """Main entry point for command-line execution."""
    try:
        if len(sys.argv) < 3:
            result = {
                "success": False,
                "error": "Usage: python main.py <command> <json_payload>",
            }
            print(json.dumps(result))
            sys.exit(1)

        command = sys.argv[1]
        payload_source = sys.argv[2]

        # Check if the payload is a file path by seeing if it ends with
        # ``temp_payload.json`` or if the path exists on disk
        if (
            payload_source.endswith("temp_payload.json")
            or Path(payload_source).exists()
        ):
            # Read JSON from file
            try:
                with open(payload_source, "r", encoding="utf-8") as f:
                    payload_text = f.read()
                payload = json.loads(payload_text)
            except (FileNotFoundError, IOError) as e:
                result = {
                    "success": False,
                    "error": f"Failed to read payload file: {str(e)}",
                }
                print(json.dumps(result))
                sys.exit(1)
            except json.JSONDecodeError as e:
                result = {
                    "success": False,
                    "error": f"Invalid JSON in payload file: {str(e)}",
                }
                print(json.dumps(result))
                sys.exit(1)
        else:
            # Parse as direct JSON string (fallback)
            try:
                payload = json.loads(payload_source)
            except json.JSONDecodeError as e:
                result = {"success": False, "error": f"Invalid JSON payload: {str(e)}"}
                print(json.dumps(result))
                sys.exit(1)

        # Initialize handler and process command
        handler = CommandHandler()
        result = await handler.handle_command(command, payload)

        # Output result as JSON for Tauri to consume
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        # Final error handler for any unhandled exceptions
        result = {"success": False, "error": f"Fatal error: {str(e)}"}
        print(json.dumps(result))
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)

    finally:
        # Cleanup
        try:
            from llm import close_ollama_client

            await close_ollama_client()
            close_database()
        except Exception:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    asyncio.run(main())
