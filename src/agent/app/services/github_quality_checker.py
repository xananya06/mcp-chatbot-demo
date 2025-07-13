import asyncio
import aiohttp
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class GitHubQualityChecker:
    """Enhanced quality checking for GitHub repositories"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.base_url = "https://api.github.com"
        
        self.headers = {
            'User-Agent': 'AI Tools Quality Checker v1.0',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    async def check_github_repo_quality(self, github_url: str) -> Dict[str, Any]:
        """
        Comprehensive GitHub repository quality assessment
        
        Returns quality score and detailed metrics
        """
        
        # Extract owner/repo from URL
        repo_info = self.parse_github_url(github_url)
        if not repo_info:
            return {
                'quality_score': 0.0,
                'is_quality_repo': False,
                'error': 'Invalid GitHub URL'
            }
        
        owner, repo_name = repo_info
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                # Get repository data
                repo_data = await self.get_repo_data(session, owner, repo_name)
                if not repo_data:
                    return {
                        'quality_score': 0.0,
                        'is_quality_repo': False,
                        'error': 'Repository not found or private'
                    }
                
                # Get additional metrics
                languages = await self.get_repo_languages(session, owner, repo_name)
                recent_activity = await self.get_recent_activity(session, owner, repo_name)
                readme_quality = await self.assess_readme_quality(session, owner, repo_name)
                
                # Calculate quality score
                quality_metrics = self.calculate_quality_metrics(
                    repo_data, languages, recent_activity, readme_quality
                )
                
                return quality_metrics
                
        except Exception as e:
            logger.error(f"Error checking GitHub repo {github_url}: {e}")
            return {
                'quality_score': 0.0,
                'is_quality_repo': False,
                'error': str(e)
            }
    
    def parse_github_url(self, url: str) -> Optional[tuple]:
        """Extract owner/repo from GitHub URL"""
        try:
            parsed = urlparse(url)
            if 'github.com' not in parsed.netloc:
                return None
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1]
            return None
        except:
            return None
    
    async def get_repo_data(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Optional[Dict]:
        """Get basic repository information"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except:
            return None
    
    async def get_repo_languages(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict:
        """Get programming languages used in the repository"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except:
            return {}
    
    async def get_recent_activity(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict:
        """Get recent commit activity"""
        try:
            # Get recent commits (last 30)
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {'per_page': 30}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    commits = await response.json()
                    return self.analyze_commit_activity(commits)
                return {'recent_commits': 0, 'days_since_last_commit': 9999}
        except:
            return {'recent_commits': 0, 'days_since_last_commit': 9999}
    
    def analyze_commit_activity(self, commits: list) -> Dict:
        """Analyze commit patterns for quality indicators"""
        if not commits:
            return {'recent_commits': 0, 'days_since_last_commit': 9999}
        
        now = datetime.now(timezone.utc)
        recent_commits = 0
        last_commit_date = None
        
        for commit in commits:
            commit_date_str = commit['commit']['author']['date']
            commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
            
            if not last_commit_date:
                last_commit_date = commit_date
            
            # Count commits in last 90 days
            days_ago = (now - commit_date).days
            if days_ago <= 90:
                recent_commits += 1
        
        days_since_last = (now - last_commit_date).days if last_commit_date else 9999
        
        return {
            'recent_commits': recent_commits,
            'days_since_last_commit': days_since_last,
            'total_commits_checked': len(commits)
        }
    
    async def assess_readme_quality(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict:
        """Assess README quality and documentation"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            
            async with session.get(url) as response:
                if response.status == 200:
                    readme_data = await response.json()
                    
                    # Decode content (it's base64 encoded)
                    import base64
                    content = base64.b64decode(readme_data['content']).decode('utf-8')
                    
                    return self.analyze_readme_content(content)
                    
                return {'has_readme': False, 'readme_quality_score': 0.0}
        except:
            return {'has_readme': False, 'readme_quality_score': 0.0}
    
    def analyze_readme_content(self, content: str) -> Dict:
        """Analyze README content for quality indicators"""
        
        quality_indicators = {
            'has_readme': True,
            'length': len(content),
            'sections': 0,
            'has_installation': False,
            'has_usage': False,
            'has_examples': False,
            'has_ai_keywords': False,
            'readme_quality_score': 0.0
        }
        
        content_lower = content.lower()
        
        # Check for important sections
        section_indicators = [
            '##', '###', '####',  # Markdown headers
            'installation', 'install',
            'usage', 'how to use', 'getting started',
            'example', 'examples', 'demo',
            'api', 'documentation', 'docs'
        ]
        
        for indicator in section_indicators:
            if indicator in content_lower:
                quality_indicators['sections'] += 1
        
        # Check for specific sections
        quality_indicators['has_installation'] = any(
            word in content_lower for word in ['install', 'pip install', 'npm install', 'setup']
        )
        
        quality_indicators['has_usage'] = any(
            word in content_lower for word in ['usage', 'how to', 'example', 'getting started']
        )
        
        quality_indicators['has_examples'] = any(
            word in content_lower for word in ['example', 'demo', '```', 'code']
        )
        
        # Check for AI/ML keywords
        ai_keywords = [
            'artificial intelligence', 'ai', 'machine learning', 'ml', 'deep learning',
            'neural network', 'tensorflow', 'pytorch', 'scikit-learn', 'opencv',
            'nlp', 'computer vision', 'gpt', 'transformer', 'model', 'dataset'
        ]
        
        quality_indicators['has_ai_keywords'] = any(
            keyword in content_lower for keyword in ai_keywords
        )
        
        # Calculate README quality score
        score = 0.0
        
        # Length score (0-3 points)
        if quality_indicators['length'] > 1000:
            score += 3
        elif quality_indicators['length'] > 500:
            score += 2
        elif quality_indicators['length'] > 200:
            score += 1
        
        # Sections score (0-2 points)
        if quality_indicators['sections'] >= 5:
            score += 2
        elif quality_indicators['sections'] >= 3:
            score += 1
        
        # Essential sections (0-3 points)
        if quality_indicators['has_installation']:
            score += 1
        if quality_indicators['has_usage']:
            score += 1
        if quality_indicators['has_examples']:
            score += 1
        
        # AI relevance (0-2 points)
        if quality_indicators['has_ai_keywords']:
            score += 2
        
        quality_indicators['readme_quality_score'] = min(score / 10.0, 1.0)  # Normalize to 0-1
        
        return quality_indicators
    
    def calculate_quality_metrics(self, repo_data: Dict, languages: Dict, 
                                activity: Dict, readme: Dict) -> Dict[str, Any]:
        """Calculate overall repository quality score"""
        
        metrics = {
            'quality_score': 0.0,
            'is_quality_repo': False,
            'quality_factors': {},
            'recommendations': [],
            'repo_stats': {
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'open_issues': repo_data.get('open_issues_count', 0),
                'size_kb': repo_data.get('size', 0),
                'created_at': repo_data.get('created_at'),
                'updated_at': repo_data.get('updated_at'),
                'language': repo_data.get('language'),
                'is_archived': repo_data.get('archived', False),
                'is_fork': repo_data.get('fork', False)
            }
        }
        
        # Quality factors with weights
        factors = {}
        
        # 1. Popularity (0-25 points)
        stars = repo_data.get('stargazers_count', 0)
        if stars >= 1000:
            factors['popularity'] = 25
        elif stars >= 100:
            factors['popularity'] = 15 + (stars - 100) * 10 / 900
        elif stars >= 10:
            factors['popularity'] = 5 + (stars - 10) * 10 / 90
        elif stars >= 1:
            factors['popularity'] = stars * 5
        else:
            factors['popularity'] = 0
        
        # 2. Recent activity (0-20 points)
        days_since_last = activity.get('days_since_last_commit', 9999)
        recent_commits = activity.get('recent_commits', 0)
        
        if days_since_last <= 30:
            factors['recency'] = 20
        elif days_since_last <= 90:
            factors['recency'] = 15
        elif days_since_last <= 180:
            factors['recency'] = 10
        elif days_since_last <= 365:
            factors['recency'] = 5
        else:
            factors['recency'] = 0
        
        # Bonus for active development
        if recent_commits >= 10:
            factors['recency'] = min(factors['recency'] + 5, 20)
        
        # 3. Documentation quality (0-20 points)
        factors['documentation'] = readme.get('readme_quality_score', 0) * 20
        
        # 4. Repository maturity (0-15 points)
        size_kb = repo_data.get('size', 0)
        if size_kb >= 1000:  # > 1MB
            factors['maturity'] = 15
        elif size_kb >= 100:  # > 100KB
            factors['maturity'] = 10
        elif size_kb >= 10:   # > 10KB
            factors['maturity'] = 5
        else:
            factors['maturity'] = 0
        
        # 5. Community engagement (0-10 points)
        forks = repo_data.get('forks_count', 0)
        if forks >= 50:
            factors['community'] = 10
        elif forks >= 10:
            factors['community'] = 7
        elif forks >= 1:
            factors['community'] = 3
        else:
            factors['community'] = 0
        
        # 6. AI relevance (0-10 points)
        if readme.get('has_ai_keywords', False):
            factors['ai_relevance'] = 10
        elif 'machine learning' in repo_data.get('description', '').lower():
            factors['ai_relevance'] = 8
        elif repo_data.get('language') in ['Python', 'Jupyter Notebook', 'R']:
            factors['ai_relevance'] = 5
        else:
            factors['ai_relevance'] = 0
        
        # Penalties
        penalties = 0
        
        if repo_data.get('archived', False):
            penalties += 30
            metrics['recommendations'].append("Repository is archived")
        
        if repo_data.get('fork', False) and stars < 10:
            penalties += 15
            metrics['recommendations'].append("Fork with low engagement")
        
        if days_since_last > 730:  # 2 years
            penalties += 20
            metrics['recommendations'].append("No recent activity (2+ years)")
        
        # Calculate total score
        total_score = sum(factors.values()) - penalties
        quality_score = max(0.0, min(total_score / 100.0, 1.0))
        
        metrics['quality_score'] = quality_score
        metrics['quality_factors'] = factors
        metrics['penalties'] = penalties
        
        # Determine if it's a quality repo
        metrics['is_quality_repo'] = (
            quality_score >= 0.4 and 
            not repo_data.get('archived', False) and
            days_since_last <= 730
        )
        
        # Quality classification
        if quality_score >= 0.8:
            metrics['quality_tier'] = 'excellent'
        elif quality_score >= 0.6:
            metrics['quality_tier'] = 'good'
        elif quality_score >= 0.4:
            metrics['quality_tier'] = 'acceptable'
        else:
            metrics['quality_tier'] = 'poor'
        
        return metrics
    
    def sync_check_github_repo_quality(self, github_url: str) -> Dict[str, Any]:
        """Synchronous wrapper for GitHub quality checking"""
        return asyncio.run(self.check_github_repo_quality(github_url))

# Global instance
github_quality_checker = GitHubQualityChecker()