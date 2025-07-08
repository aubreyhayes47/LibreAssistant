"""
Ollama client wrapper for LibreAssistant.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from urllib.parse import urljoin

# Use absolute imports when running as main module
try:
    from ..utils.config import get_config
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.config import get_config
    from utils.logger import get_logger

logger = get_logger('llm')


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, host: Optional[str] = None):
        """Initialize Ollama client."""
        config = get_config()
        self.host = host or config.llm.ollama_host
        self.timeout = aiohttp.ClientTimeout(total=config.llm.timeout_seconds)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure session is available."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def health_check(self) -> bool:
        """Check if Ollama server is available."""
        try:
            await self._ensure_session()
            if not await self.health_check():
                return {
                    'success': False,
                    'error': 'Ollama service unavailable',
                    'message': {}
                }

            if not await self.check_model_exists(model):
                pulled = await self.pull_model(model)
                if not pulled:
                    return {
                        'success': False,
                        'error': f'Model not available: {model}',
                        'message': {}
                    }
            url = urljoin(self.host, '/api/chat')
            url = urljoin(self.host, '/api/tags')
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            await self._ensure_session()
            url = urljoin(self.host, '/api/tags')
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('models', [])
                else:
                    logger.error(f"Failed to list models: HTTP {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            await self._ensure_session()
            url = urljoin(self.host, '/api/pull')
            payload = {'name': model_name}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    # Stream the response to show progress
                    async for line in response.content:
                        if line:
                            try:
                                progress = json.loads(line.decode('utf-8'))
                                if 'status' in progress:
                                    logger.info(f"Pull progress: {progress['status']}")
                            except json.JSONDecodeError:
                                continue
                    return True
                else:
                    logger.error(f"Failed to pull model: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return False
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate a response from the LLM."""
        config = get_config()
        
        # Use defaults from config if not provided
        model = model or config.llm.default_model
        temperature = temperature if temperature is not None else config.llm.temperature

        try:
            await self._ensure_session()
            if not await self.health_check():
                return {
                    'success': False,
                    'error': 'Ollama service unavailable',
                    'response': ''
                }

            if not await self.check_model_exists(model):
                pulled = await self.pull_model(model)
                if not pulled:
                    return {
                        'success': False,
                        'error': f'Model not available: {model}',
                        'response': ''
                    }
            url = urljoin(self.host, '/api/generate')
            
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': stream,
                'options': {
                    'temperature': temperature,
                }
            }
            
            if system_prompt:
                payload['system'] = system_prompt
            
            if max_tokens:
                payload['options']['num_predict'] = max_tokens
            
            logger.info(f"Generating response with model {model}")
            
            if stream:
                return await self._stream_response(url, payload)
            else:
                return await self._non_stream_response(url, payload)
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': ''
            }
    
    async def _non_stream_response(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle non-streaming response."""
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'response': data.get('response', ''),
                    'model': payload['model'],
                    'done': data.get('done', True),
                    'context': data.get('context', []),
                    'total_duration': data.get('total_duration', 0),
                    'load_duration': data.get('load_duration', 0),
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': data.get('eval_count', 0)
                }
            else:
                error_text = await response.text()
                logger.error(f"Ollama API error: HTTP {response.status} - {error_text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status}: {error_text}",
                    'response': ''
                }
    
    async def _stream_response(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle streaming response."""
        full_response = ""
        context = []
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'response' in chunk:
                                full_response += chunk['response']
                            if chunk.get('done'):
                                context = chunk.get('context', [])
                                break
                        except json.JSONDecodeError:
                            continue
                
                return {
                    'success': True,
                    'response': full_response,
                    'model': payload['model'],
                    'done': True,
                    'context': context
                }
            else:
                error_text = await response.text()
                logger.error(f"Ollama streaming error: HTTP {response.status} - {error_text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status}: {error_text}",
                    'response': ''
                }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Chat completion with conversation history."""
        config = get_config()
        model = model or config.llm.default_model
        temperature = temperature if temperature is not None else config.llm.temperature
        
        try:
            await self._ensure_session()
            if not await self.health_check():
                return {
                    'success': False,
                    'error': 'Ollama service unavailable',
                    'message': {}
                }

            if not await self.check_model_exists(model):
                pulled = await self.pull_model(model)
                if not pulled:
                    return {
                        'success': False,
                        'error': f'Model not available: {model}',
                        'message': {}
                    }

            url = urljoin(self.host, '/api/chat')
            
            payload = {
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': temperature,
                }
            }
            
            if max_tokens:
                payload['options']['num_predict'] = max_tokens
            
            logger.info(f"Chat completion with model {model}, {len(messages)} messages")
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': data.get('message', {}),
                        'model': model,
                        'done': data.get('done', True),
                        'total_duration': data.get('total_duration', 0),
                        'load_duration': data.get('load_duration', 0),
                        'prompt_eval_count': data.get('prompt_eval_count', 0),
                        'eval_count': data.get('eval_count', 0)
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Chat completion error: HTTP {response.status} - {error_text}")
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}: {error_text}",
                        'message': {}
                    }
        
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': {}
            }
    
    async def check_model_exists(self, model_name: str) -> bool:
        """Check if a specific model exists locally."""
        models = await self.list_models()
        return any(model.get('name') == model_name for model in models)
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        try:
            await self._ensure_session()
            url = urljoin(self.host, '/api/show')
            payload = {'name': model_name}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get model info: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return None
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None


# Global client instance for reuse
_ollama_client: Optional[OllamaClient] = None


async def get_ollama_client() -> OllamaClient:
    """Get global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


async def close_ollama_client():
    """Close global Ollama client."""
    global _ollama_client
    if _ollama_client:
        await _ollama_client.close()
        _ollama_client = None
