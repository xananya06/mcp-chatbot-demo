import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class FreshnessChecker:
    """Check if web pages have been updated since last visit"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.headers = {
            'User-Agent': 'AI Tools Discovery Bot 1.0 (checking for updates)'
        }
    
    async def check_page_freshness(self, url: str, last_modified: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Check if a web page has been modified since last visit
        
        Returns:
        {
            'should_scan': bool,
            'reason': str,
            'last_modified': datetime or None,
            'etag': str or None,
            'status_code': int,
            'error': str or None
        }
        """
        
        result = {
            'should_scan': True,
            'reason': 'unknown',
            'last_modified': None,
            'etag': None,
            'status_code': None,
            'error': None
        }
        
        try:
            # Prepare conditional headers
            conditional_headers = self.headers.copy()
            
            # Add If-Modified-Since header if we have last_modified
            if last_modified:
                # Convert to HTTP date format
                http_date = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
                conditional_headers['If-Modified-Since'] = http_date
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Make HEAD request first (faster, less bandwidth)
                async with session.head(url, headers=conditional_headers) as response:
                    result['status_code'] = response.status
                    
                    # Handle 304 Not Modified
                    if response.status == 304:
                        result['should_scan'] = False
                        result['reason'] = 'not_modified_since_last_check'
                        return result
                    
                    # Handle successful responses
                    if response.status == 200:
                        # Get Last-Modified header
                        last_mod_header = response.headers.get('Last-Modified')
                        if last_mod_header:
                            try:
                                result['last_modified'] = datetime.strptime(
                                    last_mod_header, '%a, %d %b %Y %H:%M:%S %Z'
                                ).replace(tzinfo=timezone.utc)
                            except ValueError:
                                # Try alternative format
                                try:
                                    result['last_modified'] = datetime.strptime(
                                        last_mod_header, '%a, %d %b %Y %H:%M:%S GMT'
                                    ).replace(tzinfo=timezone.utc)
                                except ValueError:
                                    logger.warning(f"Could not parse Last-Modified header: {last_mod_header}")
                        
                        # Get ETag
                        result['etag'] = response.headers.get('ETag')
                        
                        # Determine if we should scan
                        if last_modified and result['last_modified']:
                            if result['last_modified'] <= last_modified:
                                result['should_scan'] = False
                                result['reason'] = 'not_modified_according_to_headers'
                            else:
                                result['should_scan'] = True
                                result['reason'] = 'modified_since_last_check'
                        else:
                            # No reliable modification info, scan to be safe
                            result['should_scan'] = True
                            result['reason'] = 'no_modification_headers_available'
                    
                    # Handle other status codes
                    elif response.status == 404:
                        result['should_scan'] = False
                        result['reason'] = 'page_not_found'
                    elif response.status >= 500:
                        result['should_scan'] = False
                        result['reason'] = 'server_error'
                    else:
                        result['should_scan'] = True
                        result['reason'] = f'unexpected_status_{response.status}'
                        
        except aiohttp.ClientError as e:
            result['error'] = f"Network error: {str(e)}"
            result['should_scan'] = True  # Scan if we can't check freshness
            result['reason'] = 'network_error_assume_updated'
            
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            result['should_scan'] = True  # Scan if we can't check freshness
            result['reason'] = 'error_assume_updated'
        
        return result
    
    async def check_multiple_pages(self, urls_with_timestamps: Dict[str, Optional[datetime]]) -> Dict[str, Dict[str, Any]]:
        """
        Check freshness for multiple pages concurrently
        
        Args:
            urls_with_timestamps: Dict of {url: last_modified_datetime}
            
        Returns:
            Dict of {url: freshness_result}
        """
        
        tasks = []
        for url, last_modified in urls_with_timestamps.items():
            task = self.check_page_freshness(url, last_modified)
            tasks.append((url, task))
        
        results = {}
        for url, task in tasks:
            try:
                result = await task
                results[url] = result
            except Exception as e:
                results[url] = {
                    'should_scan': True,
                    'reason': 'check_failed',
                    'error': str(e)
                }
        
        return results
    
    def check_ai_directory_freshness(self, source_name: str, source_url: str, last_checked: Optional[datetime]) -> Dict[str, Any]:
        """
        Check if an AI directory has been updated
        Synchronous wrapper for AI directory checking
        """
        
        async def _check():
            return await self.check_page_freshness(source_url, last_checked)
        
        return asyncio.run(_check())
    
    def get_content_hash(self, content: str) -> str:
        """
        Generate a hash of page content for change detection
        Useful when Last-Modified headers aren't available
        """
        import hashlib
        
        # Clean content (remove timestamps, dynamic elements)
        cleaned = content
        
        # Remove common dynamic elements
        import re
        patterns_to_remove = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamps
            r'timestamp.*?\d+',  # Timestamp fields
            r'updated.*?\d+',    # Updated fields
            r'cache.*?\d+',      # Cache busters
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Generate hash
        return hashlib.sha256(cleaned.encode()).hexdigest()

# Example usage for AI directories
class AIDirectoryFreshnessChecker:
    """Specialized freshness checker for AI directories"""
    
    def __init__(self):
        self.checker = FreshnessChecker()
        
        # Known AI directories with their characteristics
        self.ai_directories = {
            'theresanaiforthat': {
                'url': 'https://theresanaiforthat.com',
                'check_path': '/api/tools',  # If they have an API
                'update_frequency': 'daily'
            },
            'futurepedia': {
                'url': 'https://www.futurepedia.io',
                'check_path': '/tools',
                'update_frequency': 'daily'
            },
            'aitools_fyi': {
                'url': 'https://aitools.fyi',
                'check_path': '/',
                'update_frequency': 'weekly'
            },
            'toolify_ai': {
                'url': 'https://www.toolify.ai',
                'check_path': '/browse',
                'update_frequency': 'weekly'
            }
        }
    
    async def should_scan_ai_directory(self, source_name: str, last_checked: Optional[datetime]) -> Dict[str, Any]:
        """Check if we should scan a specific AI directory"""
        
        if source_name not in self.ai_directories:
            return {
                'should_scan': True,
                'reason': 'unknown_directory',
                'source_name': source_name
            }
        
        directory_info = self.ai_directories[source_name]
        check_url = directory_info['url'] + directory_info['check_path']
        
        # Check page freshness
        freshness_result = await self.checker.check_page_freshness(check_url, last_checked)
        
        # Add directory-specific logic
        freshness_result['source_name'] = source_name
        freshness_result['check_url'] = check_url
        freshness_result['expected_frequency'] = directory_info['update_frequency']
        
        # Override based on expected frequency if no modification headers
        if freshness_result['reason'] == 'no_modification_headers_available' and last_checked:
            hours_since_check = (datetime.now(timezone.utc) - last_checked).total_seconds() / 3600
            
            if directory_info['update_frequency'] == 'daily' and hours_since_check < 20:
                freshness_result['should_scan'] = False
                freshness_result['reason'] = 'recently_checked_daily_source'
            elif directory_info['update_frequency'] == 'weekly' and hours_since_check < 144:  # 6 days
                freshness_result['should_scan'] = False
                freshness_result['reason'] = 'recently_checked_weekly_source'
        
        return freshness_result
    
    def sync_should_scan_ai_directory(self, source_name: str, last_checked: Optional[datetime]) -> Dict[str, Any]:
        """Synchronous wrapper"""
        return asyncio.run(self.should_scan_ai_directory(source_name, last_checked))

# Global instances
freshness_checker = FreshnessChecker()
ai_directory_checker = AIDirectoryFreshnessChecker()