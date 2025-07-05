"""
Main entry point for the Python backend.
This module handles Tauri native command invocations.
"""

import sys
import json
import asyncio
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        # Remove stdout handler to prevent JSON parsing issues
        # logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handles incoming commands from Tauri frontend."""
    
    def __init__(self):
        self.commands = {
            'hello': self.hello_command,
            'process_url': self.process_url,
            'get_browser_data': self.get_browser_data,
            'analyze_content': self.analyze_content,
        }
    
    async def hello_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test command to verify communication."""
        name = payload.get('name', 'World')
        return {
            'success': True,
            'message': f'Hello, {name}! Backend is working.',
            'timestamp': payload.get('timestamp')
        }
    
    async def process_url(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a URL for content extraction."""
        url = payload.get('url')
        if not url:
            return {'success': False, 'error': 'No URL provided'}
        
        # TODO: Implement web scraping logic
        return {
            'success': True,
            'url': url,
            'title': 'Example Title',
            'content': 'Extracted content will go here...'
        }
    
    async def get_browser_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get browser history or bookmarks."""
        data_type = payload.get('type', 'history')
        
        # TODO: Implement browser data extraction
        return {
            'success': True,
            'type': data_type,
            'data': [],
            'count': 0
        }
    
    async def analyze_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using LLM."""
        content = payload.get('content')
        if not content:
            return {'success': False, 'error': 'No content provided'}
        
        # TODO: Implement LLM analysis
        return {
            'success': True,
            'analysis': 'Content analysis will go here...',
            'keywords': [],
            'summary': ''
        }
    
    async def handle_command(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming command."""
        if command not in self.commands:
            return {
                'success': False,
                'error': f'Unknown command: {command}'
            }
        
        try:
            result = await self.commands[command](payload)
            logger.info(f"Command '{command}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


async def main():
    """Main entry point for command-line execution."""
    if len(sys.argv) < 3:
        print(json.dumps({
            'success': False,
            'error': 'Usage: python main.py <command> <json_payload>'
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    try:
        payload = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({
            'success': False,
            'error': f'Invalid JSON payload: {str(e)}'
        }))
        sys.exit(1)
    
    handler = CommandHandler()
    result = await handler.handle_command(command, payload)
    
    # Output result as JSON for Tauri to consume
    print(json.dumps(result))


if __name__ == '__main__':
    asyncio.run(main())
