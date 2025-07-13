import sys
sys.path.append('/app')

from app.services.github_quality_checker import github_quality_checker
from app.db.database import SessionLocal
from app.models.chat import DiscoveredTool
from datetime import datetime
import json
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/github_quality.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_comprehensive_github_quality_assessment():
    """Process ALL GitHub repositories for quality assessment"""
    
    logger.info('🚀 Starting Comprehensive GitHub Quality Assessment')
    
    db = SessionLocal()
    try:
        # Get total count first
        total_github = db.query(DiscoveredTool).filter(
            DiscoveredTool.website.ilike('%github.com%')
        ).count()
        
        already_assessed = db.query(DiscoveredTool).filter(
            DiscoveredTool.website.ilike('%github.com%'),
            DiscoveredTool.source_data.contains('github_quality_tier')
        ).count()
        
        remaining = total_github - already_assessed
        
        logger.info(f'📊 GitHub Repository Status:')
        logger.info(f'   • Total GitHub repos: {total_github}')
        logger.info(f'   • Already assessed: {already_assessed}')
        logger.info(f'   • Remaining to assess: {remaining}')
        
        if remaining == 0:
            logger.info('🎉 All GitHub repositories already assessed!')
            return
        
        # Process in batches to avoid memory issues
        batch_size = 200
        total_processed = 0
        
        stats = {
            'excellent': 0, 'good': 0, 'acceptable': 0, 'poor': 0,
            'errors': 0, 'rate_limited': 0, 'archived': 0, 'forks': 0
        }
        
        # Process all remaining repos in batches
        while True:
            # Get next batch of unassessed repos
            github_repos = db.query(DiscoveredTool).filter(
                DiscoveredTool.website.ilike('%github.com%'),
                ~DiscoveredTool.source_data.contains('github_quality_tier')
            ).limit(batch_size).all()
            
            if not github_repos:
                logger.info('✅ All repositories processed!')
                break
            
            logger.info(f'🔄 Processing batch: {len(github_repos)} repositories')
            
            batch_stats = process_github_batch(github_repos, db)
            
            # Update overall stats
            for key, value in batch_stats.items():
                stats[key] += value
            
            total_processed += len(github_repos)
            
            logger.info(f'📈 Progress: {total_processed}/{remaining} repositories processed')
            logger.info(f'📊 Current stats: Excellent: {stats["excellent"]}, Good: {stats["good"]}, Acceptable: {stats["acceptable"]}, Poor: {stats["poor"]}')
            
            # Brief pause between batches to be respectful to GitHub API
            time.sleep(5)
        
        # Final summary
        logger.info(f'🎉 COMPREHENSIVE GITHUB QUALITY ASSESSMENT COMPLETE!')
        logger.info(f'📊 FINAL RESULTS:')
        logger.info(f'   • Total processed: {total_processed}')
        logger.info(f'   • Excellent quality: {stats["excellent"]} ({stats["excellent"]/total_processed*100:.1f}%)')
        logger.info(f'   • Good quality: {stats["good"]} ({stats["good"]/total_processed*100:.1f}%)')
        logger.info(f'   • Acceptable quality: {stats["acceptable"]} ({stats["acceptable"]/total_processed*100:.1f}%)')
        logger.info(f'   • Poor quality: {stats["poor"]} ({stats["poor"]/total_processed*100:.1f}%)')
        logger.info(f'   • Errors/Rate limited: {stats["errors"]} + {stats["rate_limited"]}')
        logger.info(f'   • Archived repos: {stats["archived"]}')
        logger.info(f'   • Fork repos: {stats["forks"]}')
        
        return stats
        
    finally:
        db.close()

def process_github_batch(github_repos, db):
    """Process a batch of GitHub repositories"""
    
    batch_stats = {
        'excellent': 0, 'good': 0, 'acceptable': 0, 'poor': 0,
        'errors': 0, 'rate_limited': 0, 'archived': 0, 'forks': 0
    }
    
    for i, tool in enumerate(github_repos):
        try:
            # Add small delay to be respectful to GitHub API
            if i > 0 and i % 10 == 0:
                time.sleep(2)
            
            result = github_quality_checker.sync_check_github_repo_quality(tool.website)
            
            if result.get('error'):
                error_msg = result.get('error', '').lower()
                if 'rate limit' in error_msg or '403' in error_msg:
                    batch_stats['rate_limited'] += 1
                    logger.warning(f'Rate limited on {tool.name}, adding delay...')
                    time.sleep(10)  # Longer delay for rate limiting
                else:
                    batch_stats['errors'] += 1
                    logger.error(f'Error assessing {tool.name}: {result.get("error")}')
                continue
            
            # Extract quality information
            quality_tier = result.get('quality_tier', 'poor')
            quality_score = result.get('quality_score', 0)
            repo_stats = result.get('repo_stats', {})
            
            batch_stats[quality_tier] += 1
            
            # Track special cases
            if repo_stats.get('is_archived'):
                batch_stats['archived'] += 1
            if repo_stats.get('is_fork'):
                batch_stats['forks'] += 1
            
            # Update tool confidence based on GitHub quality
            confidence_adjustments = {
                'excellent': 0.20,  # Boost excellent repos significantly
                'good': 0.15,       # Good boost for good repos
                'acceptable': 0.05, # Small boost for acceptable
                'poor': -0.20       # Significant penalty for poor quality
            }
            
            adjustment = confidence_adjustments.get(quality_tier, 0)
            
            # Extra penalties for archived/fork repos
            if repo_stats.get('is_archived'):
                adjustment -= 0.15
            if repo_stats.get('is_fork') and repo_stats.get('stars', 0) < 10:
                adjustment -= 0.10
            
            if tool.confidence_score:
                new_confidence = tool.confidence_score + adjustment
                tool.confidence_score = max(0.1, min(0.95, new_confidence))
            
            # Store comprehensive quality data
            quality_data = {
                'github_quality_score': quality_score,
                'github_quality_tier': quality_tier,
                'github_stars': repo_stats.get('stars', 0),
                'github_forks': repo_stats.get('forks', 0),
                'github_open_issues': repo_stats.get('open_issues', 0),
                'github_language': repo_stats.get('language'),
                'github_size_kb': repo_stats.get('size_kb', 0),
                'github_created_at': repo_stats.get('created_at'),
                'github_last_update': repo_stats.get('updated_at'),
                'github_is_archived': repo_stats.get('is_archived', False),
                'github_is_fork': repo_stats.get('is_fork', False),
                'quality_check_date': datetime.utcnow().isoformat(),
                'quality_factors': result.get('quality_factors', {}),
                'is_quality_repo': result.get('is_quality_repo', False)
            }
            
            # Update source_data with quality information
            existing_data = {}
            if tool.source_data:
                try:
                    existing_data = json.loads(tool.source_data)
                except:
                    pass
            
            existing_data.update(quality_data)
            tool.source_data = json.dumps(existing_data)
            
        except Exception as e:
            batch_stats['errors'] += 1
            logger.error(f'Exception processing {tool.name}: {e}')
            time.sleep(1)
    
    # Commit the batch
    try:
        db.commit()
        logger.info(f'✅ Batch committed successfully')
    except Exception as e:
        db.rollback()
        logger.error(f'Failed to commit batch: {e}')
    
    return batch_stats

if __name__ == '__main__':
    run_comprehensive_github_quality_assessment()
