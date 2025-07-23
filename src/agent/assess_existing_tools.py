#!/usr/bin/env python3
"""
Unified Activity Assessment Script
Processes all existing tools in the database with the new activity assessment system
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import SessionLocal
from app.models.chat import DiscoveredTool
from app.services.unified_activity_service import unified_activity_service

class ActivityAssessmentRunner:
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        
    def get_tools_to_assess(self, db, limit: int = None) -> List[DiscoveredTool]:
        """Get tools that need assessment"""
        query = db.query(DiscoveredTool).filter(
            # Never assessed OR assessed more than 7 days ago
            DiscoveredTool.last_activity_check.is_(None) |
            (DiscoveredTool.last_activity_check < datetime.utcnow() - timedelta(days=7))
        ).filter(
            # Has a website to check
            DiscoveredTool.website.isnot(None),
            DiscoveredTool.website != ""
        )
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    async def assess_single_tool(self, tool: DiscoveredTool, db) -> Dict[str, Any]:
        """Assess a single tool and update database"""
        try:
            print(f"  📊 Assessing: {tool.name[:50]}...")
            
            # Run the unified assessment
            assessment = await unified_activity_service.assess_tool_activity(tool)
            
            # Update the tool with assessment results
            tool.tool_type_detected = assessment.get('tool_type_detected', 'unknown')
            tool.activity_score = assessment.get('activity_score', 0.0)
            tool.last_activity_check = datetime.utcnow()
            
            # Update source-specific metrics
            if 'github_stars' in assessment:
                tool.github_stars = assessment['github_stars']
                tool.github_forks = assessment.get('github_forks')
                tool.github_recent_commits = assessment.get('github_recent_commits')
                
            if 'npm_version_count' in assessment:
                tool.npm_weekly_downloads = assessment.get('npm_weekly_downloads')
                tool.npm_last_update = assessment.get('npm_last_update')
                
            if 'pypi_release_count' in assessment:
                tool.pypi_last_release = assessment.get('pypi_last_release')
                
            if 'website_status' in assessment:
                tool.website_status = assessment['website_status']
                
            if 'is_actively_maintained' in assessment:
                tool.is_actively_maintained = assessment['is_actively_maintained']
            
            # Calculate quality scores
            self._calculate_quality_scores(tool, assessment)
            
            self.processed_count += 1
            
            return {
                "success": True,
                "tool_name": tool.name,
                "tool_type": assessment.get('tool_type_detected'),
                "activity_score": assessment.get('activity_score'),
                "assessment": assessment
            }
            
        except Exception as e:
            self.error_count += 1
            print(f"    ❌ Error assessing {tool.name}: {str(e)}")
            return {
                "success": False,
                "tool_name": tool.name,
                "error": str(e)
            }
    
    def _calculate_quality_scores(self, tool: DiscoveredTool, assessment: Dict[str, Any]):
        """Calculate additional quality scores"""
        
        # Community size score (based on stars, downloads, etc.)
        community_score = 0.0
        if tool.github_stars:
            community_score = min(tool.github_stars / 1000, 1.0) * 0.6
        if tool.npm_weekly_downloads:
            community_score += min(tool.npm_weekly_downloads / 10000, 1.0) * 0.4
        tool.community_size_score = community_score
        
        # Usage popularity score
        tool.usage_popularity_score = assessment.get('activity_score', 0.0)
        
        # Maintenance quality score
        maintenance_score = 0.5  # Base score
        if tool.is_actively_maintained:
            maintenance_score += 0.3
        if tool.website_status == 200:
            maintenance_score += 0.2
        tool.maintenance_quality_score = min(maintenance_score, 1.0)
    
    async def process_batch(self, tools: List[DiscoveredTool], batch_num: int) -> Dict[str, Any]:
        """Process a batch of tools"""
        print(f"\n🚀 Processing Batch {batch_num}: {len(tools)} tools")
        batch_start = time.time()
        
        db = SessionLocal()
        results = []
        
        try:
            for i, tool in enumerate(tools):
                # Assess the tool
                result = await self.assess_single_tool(tool, db)
                results.append(result)
                
                # Show progress within batch
                if (i + 1) % 10 == 0:
                    print(f"    📈 Batch progress: {i + 1}/{len(tools)}")
                
                # Small delay to be respectful to APIs
                await asyncio.sleep(0.2)
            
            # Commit all changes for this batch
            db.commit()
            batch_time = time.time() - batch_start
            
            successful = len([r for r in results if r.get('success')])
            failed = len([r for r in results if not r.get('success')])
            
            print(f"✅ Batch {batch_num} Complete:")
            print(f"    • Successful: {successful}")
            print(f"    • Failed: {failed}")
            print(f"    • Time: {batch_time:.1f}s")
            print(f"    • Total processed: {self.processed_count}")
            
            return {
                "batch_number": batch_num,
                "successful": successful,
                "failed": failed,
                "processing_time": batch_time,
                "results": results
            }
            
        except Exception as e:
            db.rollback()
            print(f"❌ Batch {batch_num} failed: {str(e)}")
            return {
                "batch_number": batch_num,
                "error": str(e),
                "successful": 0,
                "failed": len(tools)
            }
        finally:
            db.close()
    
    async def run_full_assessment(self, max_tools: int = None, dry_run: bool = False):
        """Run the complete assessment process"""
        self.start_time = time.time()
        
        print("🎯 UNIFIED ACTIVITY ASSESSMENT STARTING")
        print("=" * 60)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No database changes will be made")
        
        # Get tools to assess
        db = SessionLocal()
        try:
            tools_to_assess = self.get_tools_to_assess(db, max_tools)
            total_tools = len(tools_to_assess)
            
            print(f"📊 Found {total_tools} tools needing assessment")
            
            if total_tools == 0:
                print("✅ All tools are up to date!")
                return
                
            if dry_run:
                print("📋 First 10 tools that would be assessed:")
                for i, tool in enumerate(tools_to_assess[:10]):
                    print(f"  {i+1}. {tool.name} - {tool.website}")
                return
                
        finally:
            db.close()
        
        # Process in batches
        batch_results = []
        batch_num = 0
        
        for i in range(0, total_tools, self.batch_size):
            batch_num += 1
            batch_tools = tools_to_assess[i:i + self.batch_size]
            
            # Process this batch
            batch_result = await self.process_batch(batch_tools, batch_num)
            batch_results.append(batch_result)
            
            # Progress update
            progress = (i + len(batch_tools)) / total_tools * 100
            estimated_remaining = self._estimate_remaining_time(progress)
            
            print(f"📊 Overall Progress: {progress:.1f}% | ETA: {estimated_remaining}")
            
            # Cooldown between batches
            if i + self.batch_size < total_tools:
                print("⏳ Cooling down 3 seconds...")
                await asyncio.sleep(3)
        
        # Final summary
        self._print_final_summary(batch_results, total_tools)
    
    def _estimate_remaining_time(self, progress_percent: float) -> str:
        """Estimate remaining time"""
        if progress_percent <= 0:
            return "Unknown"
            
        elapsed = time.time() - self.start_time
        total_estimated = elapsed / (progress_percent / 100)
        remaining = total_estimated - elapsed
        
        if remaining < 60:
            return f"{remaining:.0f}s"
        elif remaining < 3600:
            return f"{remaining/60:.1f}m"
        else:
            return f"{remaining/3600:.1f}h"
    
    def _print_final_summary(self, batch_results: List[Dict], total_tools: int):
        """Print final summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("🎊 UNIFIED ACTIVITY ASSESSMENT COMPLETE!")
        print("=" * 60)
        
        total_successful = sum(batch.get('successful', 0) for batch in batch_results)
        total_failed = sum(batch.get('failed', 0) for batch in batch_results)
        
        print(f"📈 FINAL RESULTS:")
        print(f"   • Total tools processed: {total_tools}")
        print(f"   • Successful assessments: {total_successful}")
        print(f"   • Failed assessments: {total_failed}")
        print(f"   • Success rate: {(total_successful/total_tools)*100:.1f}%")
        print(f"   • Total time: {total_time/60:.1f} minutes")
        print(f"   • Average per tool: {total_time/total_tools:.1f}s")
        
        print(f"\n🎯 DATABASE UPDATES:")
        print(f"   • Tools now have activity_score (0.0-1.0)")
        print(f"   • Tool types detected and classified")
        print(f"   • Source-specific metrics updated")
        print(f"   • Maintenance status determined")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"   • Check high-activity tools: /ai-tools/high-activity")
        print(f"   • Review activity status: /admin/activity-status")
        print(f"   • Agent can now prioritize quality tools!")


async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run unified activity assessment on existing tools')
    parser.add_argument('--batch-size', type=int, default=50, help='Tools per batch (default: 50)')
    parser.add_argument('--max-tools', type=int, help='Maximum tools to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making changes')
    
    args = parser.parse_args()
    
    runner = ActivityAssessmentRunner(batch_size=args.batch_size)
    
    try:
        await runner.run_full_assessment(
            max_tools=args.max_tools,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        print(f"\n⚠️  Assessment interrupted by user")
        print(f"📊 Processed {runner.processed_count} tools before interruption")
    except Exception as e:
        print(f"\n❌ Assessment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Fix import issues
    from datetime import timedelta
    
    asyncio.run(main())