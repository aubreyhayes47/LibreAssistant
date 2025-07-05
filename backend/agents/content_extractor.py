"""
Content extraction agent for LibreAssistant
Handles web page content extraction and processing
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Agent for extracting and processing web page content"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure session is available"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    async def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a web page
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            await self._ensure_session()
            
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
            
            # Set headers to appear as a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Fetch the page
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}: {response.reason}'
                    }
                
                # Read content
                content = await response.text()
                content_type = response.headers.get('content-type', '')
                
                # Parse HTML
                if 'html' in content_type.lower():
                    extracted = self._extract_html_content(content, url)
                else:
                    extracted = {
                        'title': f'Non-HTML content from {url}',
                        'text': content[:1000] + '...' if len(content) > 1000 else content,
                        'description': f'Content type: {content_type}',
                        'links': [],
                        'images': [],
                        'headings': []
                    }
                
                return {
                    'success': True,
                    'url': url,
                    'status_code': response.status,
                    'content_type': content_type,
                    'size': len(content),
                    **extracted
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error extracting content from {url}: {e}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                'success': False,
                'error': f'Extraction failed: {str(e)}'
            }
    
    def _extract_html_content(self, html: str, base_url: str) -> Dict[str, Any]:
        """Extract structured content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else 'No title'
            
            # Extract meta description
            description_elem = soup.find('meta', attrs={'name': 'description'})
            description = ''
            if description_elem:
                description = description_elem.get('content', '').strip()
            
            # Extract main text content
            text_content = soup.get_text()
            # Clean up whitespace
            text_lines = [line.strip() for line in text_content.splitlines()]
            text_content = '\n'.join(line for line in text_lines if line)
            
            # Limit text length
            if len(text_content) > 5000:
                text_content = text_content[:5000] + '...'
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text().strip()
                if href and link_text:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    
                    links.append({
                        'text': link_text[:100],  # Limit link text length
                        'url': href
                    })
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                src = img['src']
                alt = img.get('alt', '').strip()
                
                # Convert relative URLs to absolute
                if src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                
                images.append({
                    'src': src,
                    'alt': alt
                })
            
            # Extract headings
            headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': int(heading.name[1]),
                        'text': text[:200]  # Limit heading length
                    })
            
            return {
                'title': title,
                'description': description,
                'text': text_content,
                'links': links[:20],  # Limit number of links
                'images': images[:10],  # Limit number of images
                'headings': headings[:10]  # Limit number of headings
            }
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return {
                'title': 'Error parsing content',
                'description': '',
                'text': 'Failed to parse HTML content',
                'links': [],
                'images': [],
                'headings': []
            }
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
