# src/agent/app/services/unified_activity_service.py
import asyncio
import aiohttp
import re
import json
import hashlib
import os
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.database import SessionLocal
from app.models.chat import DiscoveredTool

class UnifiedActivityAssessment:
    """
    Unified tool assessment system that replaces separate health checkers
    Assesses tools based on their type: GitHub repos, NPM packages, web apps, etc.
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'User-Agent': 'AI Tools Activity Assessment v2.0'
        }
        
        # Tool type detection patterns
        self.type_patterns = {
            'github_repo': r'github\.com/[\w\-\.]+/[\w\-\.]+',
            'npm_package': r'npmjs\.com/package/[\w\-\.]+',
            'pypi_package': r'pypi\.org/project/[\w\-\.]+',
            'docker_image': r'hub\.docker\.com',
            'gitlab_repo': r'gitlab\.com/[\w\-\.]+/[\w\-\.]+',
            'bitbucket_repo': r'bitbucket\.org/[\w\-\.]+/[\w\-\.]+',
            'huggingface_model': r'huggingface\.co/[\w\-\.]+/[\w\-\.]+'
        }
    
    def detect_tool_type(self, tool: DiscoveredTool) -> str:
        """Automatically detect tool type based on URL and description"""
        
        url = tool.website or ""
        description = (tool.description or "").lower()
        
        # Direct URL pattern matching (most reliable)
        for tool_type, pattern in self.type_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                return tool_type
        
        # Description-based detection for CLI/library tools
        cli_keywords = ['command line', 'cli', 'terminal', 'bash', 'shell']
        library_keywords = ['library', 'framework', 'sdk', 'package', 'module']
        api_keywords = ['api', 'endpoint', 'rest', 'graphql', 'webhook']
        
        if any(keyword in description for keyword in cli_keywords):
            return 'cli_tool'
        elif any(keyword in description for keyword in library_keywords):
            return 'library_package'
        elif any(keyword in description for keyword in api_keywords):
            return 'api_service'
        elif url and self._is_web_domain(url):
            return 'web_application'
        
        return 'unknown'
    
    def _is_web_domain(self, url: str) -> bool:
        """Check if URL is a regular website (not code repository)"""
        try:
            domain = urlparse(url).netloc.lower()
            code_domains = ['github.com', 'gitlab.com', 'bitbucket.org', 'npmjs.com', 'pypi.org']
            return not any(code_domain in domain for code_domain in code_domains)
        except:
            return False
    
    async def assess_tool_activity(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Main assessment method - routes to appropriate checker based on tool type"""
        
        tool_type = self.detect_tool_type(tool)
        
        try:
            if tool_type == 'github_repo':
                result = await self._assess_github_activity(tool)
            elif tool_type == 'npm_package':
                result = await self._assess_npm_activity(tool)
            elif tool_type == 'pypi_package':
                result = await self._assess_pypi_activity(tool)
            elif tool_type == 'web_application':
                result = await self._assess_webapp_activity(tool)
            else:
                result = await self._assess_generic_activity(tool)
            
            result['tool_type_detected'] = tool_type
            result['assessment_timestamp'] = datetime.utcnow().isoformat()
            return result
            
        except Exception as e:
            return {
                'tool_type_detected': tool_type,
                'activity_score': 0.0,
                'error': str(e),
                'assessment_timestamp': datetime.utcnow().isoformat()
            }
    
    async def _assess_github_activity(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Assess GitHub repository activity"""
        
        github_url = tool.website
        repo_match = re.search(r'github\.com/([\w\-\.]+)/([\w\-\.]+)', github_url)
        
        if not repo_match:
            return {'activity_score': 0.0, 'error': 'Invalid GitHub URL'}
        
        owner, repo = repo_match.groups()
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            headers = self.headers.copy()
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            try:
                # Get repository information
                repo_url = f'https://api.github.com/repos/{owner}/{repo}'
                
                async with session.get(repo_url, headers=headers) as response:
                    if response.status != 200:
                        return {'activity_score': 0.0, 'error': f'GitHub API error: {response.status}'}
                    
                    repo_data = await response.json()
                    
                    # Get recent commits
                    commits_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
                    params = {'since': (datetime.utcnow() - timedelta(days=90)).isoformat()}
                    
                    recent_commits = []
                    try:
                        async with session.get(commits_url, headers=headers, params=params) as commits_response:
                            if commits_response.status == 200:
                                recent_commits = await commits_response.json()
                    except:
                        pass  # Continue without recent commits data
                    
                    # Calculate activity score
                    activity_score = self._calculate_github_score(repo_data, recent_commits)
                    
                    return {
                        'activity_score': activity_score,
                        'github_stars': repo_data.get('stargazers_count', 0),
                        'github_forks': repo_data.get('forks_count', 0),
                        'github_recent_commits': len(recent_commits),
                        'is_actively_maintained': len(recent_commits) > 0,
                    }
            except Exception as e:
                return {'activity_score': 0.0, 'error': str(e)}
    
    def _calculate_github_score(self, repo_data: dict, recent_commits: list) -> float:
        """Simple GitHub scoring using math.log10 instead of numpy"""
        score = 0.0
        
        # Stars contribution (max 0.4)
        stars = repo_data.get('stargazers_count', 0)
        if stars > 1000:
            score += 0.4
        elif stars > 100:
            score += 0.3
        elif stars > 10:
            score += 0.2
        elif stars > 0:
            score += 0.1
        
        # Recent activity (max 0.4)
        commits = len(recent_commits)
        if commits > 20:
            score += 0.4
        elif commits > 10:
            score += 0.3
        elif commits > 5:
            score += 0.2
        elif commits > 0:
            score += 0.1
        
        # Basic repo health (max 0.2)
        if not repo_data.get('archived', False):
            score += 0.1
        if repo_data.get('updated_at'):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _assess_npm_activity(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Assess NPM package activity"""
        
        npm_match = re.search(r'npmjs\.com/package/([\w\-\.@/]+)', tool.website)
        if not npm_match:
            return {'activity_score': 0.0, 'error': 'Invalid NPM URL'}
        
        package_name = npm_match.group(1)
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Get package info
                package_url = f'https://registry.npmjs.org/{package_name}'
                
                async with session.get(package_url, headers=self.headers) as response:
                    if response.status != 200:
                        return {'activity_score': 0.0, 'error': f'NPM API error: {response.status}'}
                    
                    package_data = await response.json()
                    
                    # Simple NPM scoring
                    score = 0.5  # Base score for existing package
                    
                    # Check if recently updated
                    last_modified = package_data.get('time', {}).get('modified')
                    if last_modified:
                        try:
                            modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                            days_old = (datetime.now(timezone.utc) - modified_date).days
                            if days_old < 365:
                                score += 0.3
                        except:
                            pass
                    
                    # Version count indicates activity
                    versions = len(package_data.get('versions', {}))
                    if versions > 10:
                        score += 0.2
                    
                    return {
                        'activity_score': min(score, 1.0),
                        'npm_version_count': versions,
                        'npm_last_update': last_modified,
                        'is_actively_maintained': score > 0.6,
                    }
        except Exception as e:
            return {'activity_score': 0.0, 'error': str(e)}
    
    async def _assess_pypi_activity(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Assess PyPI package activity"""
        
        pypi_match = re.search(r'pypi\.org/project/([\w\-\.]+)', tool.website)
        if not pypi_match:
            return {'activity_score': 0.0, 'error': 'Invalid PyPI URL'}
        
        package_name = pypi_match.group(1)
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                package_url = f'https://pypi.org/pypi/{package_name}/json'
                
                async with session.get(package_url, headers=self.headers) as response:
                    if response.status != 200:
                        return {'activity_score': 0.0, 'error': f'PyPI API error: {response.status}'}
                    
                    package_data = await response.json()
                    
                    # Simple PyPI scoring
                    score = 0.5  # Base score
                    
                    # Check upload time
                    upload_time = package_data.get('info', {}).get('upload_time')
                    if upload_time:
                        try:
                            upload_date = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                            days_old = (datetime.now(timezone.utc) - upload_date).days
                            if days_old < 730:  # Less than 2 years
                                score += 0.3
                        except:
                            pass
                    
                    # Release count
                    releases = len(package_data.get('releases', {}))
                    if releases > 5:
                        score += 0.2
                    
                    return {
                        'activity_score': min(score, 1.0),
                        'pypi_release_count': releases,
                        'pypi_last_release': upload_time,
                        'is_actively_maintained': score > 0.6,
                    }
        except Exception as e:
            return {'activity_score': 0.0, 'error': str(e)}
    
    async def _assess_webapp_activity(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Assess web application activity"""
        
        if not tool.website:
            return {'activity_score': 0.0, 'error': 'No website URL'}
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(tool.website, headers=self.headers) as response:
                    is_healthy = response.status == 200
                    has_ssl = str(response.url).startswith('https://')
                    
                    score = 0.0
                    if is_healthy:
                        score += 0.6
                    if has_ssl:
                        score += 0.2
                    
                    # Basic content check
                    if is_healthy:
                        try:
                            content = await response.text()
                            if len(content) > 1000:
                                score += 0.1
                            if any(word in content.lower() for word in ['ai', 'machine learning', 'automation']):
                                score += 0.1
                        except:
                            pass
                    
                    return {
                        'activity_score': min(score, 1.0),
                        'website_status': response.status,
                        'has_ssl': has_ssl,
                        'is_actively_maintained': is_healthy,
                    }
        except Exception as e:
            return {
                'activity_score': 0.0,
                'website_status': 0,
                'error': str(e),
                'is_actively_maintained': False
            }
    
    async def _assess_generic_activity(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Fallback assessment"""
        if tool.website:
            return await self._assess_webapp_activity(tool)
        else:
            return {
                'activity_score': 0.1,
                'error': 'Unable to determine assessment method',
                'is_actively_maintained': False
            }
    
    def sync_assess_single_tool(self, tool: DiscoveredTool) -> Dict[str, Any]:
        """Synchronous wrapper for single tool assessment"""
        return asyncio.run(self.assess_tool_activity(tool))

# Global service instance
unified_activity_service = UnifiedActivityAssessment()