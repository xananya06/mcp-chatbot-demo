#!/usr/bin/env python3
"""
Export AI Tools Database to Excel
Exports all discovered tools from the database to a comprehensive Excel file
"""

import sys
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.db.database import SessionLocal
    from app.models.chat import DiscoveredTool, ToolReport, SourceTracking
    from sqlalchemy import func, and_, or_, desc
    DATABASE_AVAILABLE = True
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"❌ Database not available: {e}")
    print("Make sure you're running this inside the Docker container:")
    print("docker compose exec agent python export_tools.py")
    sys.exit(1)

class ToolsExporter:
    """Export AI tools database to Excel with multiple sheets"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.export_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from database with comprehensive information"""
        
        print("📊 Fetching all tools from database...")
        
        tools = self.db.query(DiscoveredTool).all()
        
        tools_data = []
        for tool in tools:
            tool_data = {
                # Basic Information
                'ID': tool.id,
                'Name': tool.name,
                'Website': tool.website,
                'Description': tool.description,
                'Category': tool.category,
                'Tool Type': tool.tool_type,
                'Tool Type Detected': tool.tool_type_detected,
                'Features': tool.features,
                'Pricing': tool.pricing,
                
                # Quality Metrics
                'Activity Score': tool.activity_score,
                'Confidence Score': tool.confidence_score,
                'Is Actively Maintained': tool.is_actively_maintained,
                'Community Size Score': tool.community_size_score,
                'Usage Popularity Score': tool.usage_popularity_score,
                'Maintenance Quality Score': tool.maintenance_quality_score,
                
                # Source-Specific Metrics
                'GitHub Stars': tool.github_stars,
                'GitHub Last Commit': tool.github_last_commit.replace(tzinfo=None) if tool.github_last_commit else None,
                'GitHub Contributors': tool.github_contributors,
                'NPM Weekly Downloads': tool.npm_weekly_downloads,
                'NPM Last Version': tool.npm_last_version,
                'NPM Last Update': tool.npm_last_update.replace(tzinfo=None) if tool.npm_last_update else None,
                'PyPI Downloads': tool.pypi_downloads,
                'PyPI Last Release': tool.pypi_last_release.replace(tzinfo=None) if tool.pypi_last_release else None,
                
                # Status Information
                'Website Status': tool.website_status,
                'Last Health Check': tool.last_health_check.replace(tzinfo=None) if tool.last_health_check else None,
                'Last Activity Check': tool.last_activity_check.replace(tzinfo=None) if tool.last_activity_check else None,
                'User Reports Count': tool.user_reports,
                'Canonical URL': tool.canonical_url,
                'Company Name': tool.company_name,
                
                # Timestamps
                'Created At': tool.created_at.replace(tzinfo=None) if tool.created_at else None,
                'Updated At': tool.updated_at.replace(tzinfo=None) if tool.updated_at else None,
                
                # Additional Data
                'Source Data': tool.source_data,
            }
            tools_data.append(tool_data)
        
        print(f"✅ Retrieved {len(tools_data)} tools")
        return tools_data
    
    def get_high_activity_tools(self) -> List[Dict[str, Any]]:
        """Get tools with high activity scores (>= 0.7)"""
        
        print("🌟 Fetching high-activity tools...")
        
        high_activity_tools = self.db.query(DiscoveredTool).filter(
            DiscoveredTool.activity_score >= 0.7
        ).order_by(desc(DiscoveredTool.activity_score)).all()
        
        tools_data = []
        for tool in high_activity_tools:
            tool_data = {
                'Rank': len(tools_data) + 1,
                'Name': tool.name,
                'Website': tool.website,
                'Description': tool.description[:200] + "..." if len(tool.description or "") > 200 else tool.description,
                'Activity Score': tool.activity_score,
                'Tool Type': tool.tool_type_detected,
                'GitHub Stars': tool.github_stars,
                'NPM Downloads/Week': tool.npm_weekly_downloads,
                'Is Maintained': tool.is_actively_maintained,
                'Website Status': tool.website_status,
                'Last Check': tool.last_activity_check.replace(tzinfo=None) if tool.last_activity_check else None,
                'Category': tool.category,
                'Pricing': tool.pricing,
            }
            tools_data.append(tool_data)
        
        print(f"✅ Retrieved {len(tools_data)} high-activity tools")
        return tools_data
    
    def get_tools_by_category(self) -> List[Dict[str, Any]]:
        """Get tool statistics by category"""
        
        print("📋 Analyzing tools by category...")
        
        # Get basic category stats
        category_stats = self.db.query(
            DiscoveredTool.category,
            func.count(DiscoveredTool.id).label('total_tools'),
            func.avg(DiscoveredTool.activity_score).label('avg_activity_score'),
            func.avg(DiscoveredTool.confidence_score).label('avg_confidence_score')
        ).filter(
            DiscoveredTool.category.isnot(None)
        ).group_by(DiscoveredTool.category).all()
        
        category_data = []
        for stat in category_stats:
            # Get high activity count for this category
            high_activity_count = self.db.query(func.count(DiscoveredTool.id)).filter(
                and_(
                    DiscoveredTool.category == stat.category,
                    DiscoveredTool.activity_score >= 0.7
                )
            ).scalar()
            
            # Get actively maintained count for this category
            maintained_count = self.db.query(func.count(DiscoveredTool.id)).filter(
                and_(
                    DiscoveredTool.category == stat.category,
                    DiscoveredTool.is_actively_maintained == True
                )
            ).scalar()
            
            category_info = {
                'Category': stat.category,
                'Total Tools': stat.total_tools,
                'High Activity Tools': high_activity_count,
                'High Activity %': round((high_activity_count / stat.total_tools) * 100, 1) if stat.total_tools > 0 else 0,
                'Avg Activity Score': round(float(stat.avg_activity_score), 3) if stat.avg_activity_score else 0,
                'Avg Confidence Score': round(float(stat.avg_confidence_score), 3) if stat.avg_confidence_score else 0,
                'Actively Maintained': maintained_count,
                'Maintenance %': round((maintained_count / stat.total_tools) * 100, 1) if stat.total_tools > 0 else 0,
            }
            category_data.append(category_info)
        
        # Sort by total tools descending
        category_data.sort(key=lambda x: x['Total Tools'], reverse=True)
        
        print(f"✅ Analyzed {len(category_data)} categories")
        return category_data
    
    def get_tools_by_type(self) -> List[Dict[str, Any]]:
        """Get tool statistics by detected type"""
        
        print("🔍 Analyzing tools by detected type...")
        
        # Get basic type stats
        type_stats = self.db.query(
            DiscoveredTool.tool_type_detected,
            func.count(DiscoveredTool.id).label('total_tools'),
            func.avg(DiscoveredTool.activity_score).label('avg_activity_score')
        ).filter(
            DiscoveredTool.tool_type_detected.isnot(None)
        ).group_by(DiscoveredTool.tool_type_detected).all()
        
        type_data = []
        for stat in type_stats:
            # Get high activity count for this type
            high_activity_count = self.db.query(func.count(DiscoveredTool.id)).filter(
                and_(
                    DiscoveredTool.tool_type_detected == stat.tool_type_detected,
                    DiscoveredTool.activity_score >= 0.7
                )
            ).scalar()
            
            type_info = {
                'Tool Type': stat.tool_type_detected,
                'Total Tools': stat.total_tools,
                'High Activity Tools': high_activity_count,
                'High Activity %': round((high_activity_count / stat.total_tools) * 100, 1) if stat.total_tools > 0 else 0,
                'Avg Activity Score': round(float(stat.avg_activity_score), 3) if stat.avg_activity_score else 0,
            }
            type_data.append(type_info)
        
        # Sort by total tools descending
        type_data.sort(key=lambda x: x['Total Tools'], reverse=True)
        
        print(f"✅ Analyzed {len(type_data)} tool types")
        return type_data
    
    def get_github_tools(self) -> List[Dict[str, Any]]:
        """Get GitHub repositories with detailed metrics"""
        
        print("🐙 Fetching GitHub repositories...")
        
        github_tools = self.db.query(DiscoveredTool).filter(
            DiscoveredTool.tool_type_detected == 'github_repo'
        ).order_by(desc(DiscoveredTool.github_stars)).all()
        
        tools_data = []
        for tool in github_tools:
            tool_data = {
                'Name': tool.name,
                'Repository URL': tool.website,
                'Description': tool.description,
                'Stars': tool.github_stars,
                'Contributors': tool.github_contributors,
                'Last Commit': tool.github_last_commit.replace(tzinfo=None) if tool.github_last_commit else None,
                'Activity Score': tool.activity_score,
                'Is Maintained': tool.is_actively_maintained,
                'Category': tool.category,
                'Features': tool.features,
                'Last Check': tool.last_activity_check.replace(tzinfo=None) if tool.last_activity_check else None,
            }
            tools_data.append(tool_data)
        
        print(f"✅ Retrieved {len(tools_data)} GitHub repositories")
        return tools_data
    
    def get_npm_tools(self) -> List[Dict[str, Any]]:
        """Get NPM packages with detailed metrics"""
        
        print("📦 Fetching NPM packages...")
        
        npm_tools = self.db.query(DiscoveredTool).filter(
            DiscoveredTool.tool_type_detected == 'npm_package'
        ).order_by(desc(DiscoveredTool.npm_weekly_downloads)).all()
        
        tools_data = []
        for tool in npm_tools:
            tool_data = {
                'Package Name': tool.name,
                'NPM URL': tool.website,
                'Description': tool.description,
                'Weekly Downloads': tool.npm_weekly_downloads,
                'Last Version': tool.npm_last_version,
                'Last Update': tool.npm_last_update.replace(tzinfo=None) if tool.npm_last_update else None,
                'Activity Score': tool.activity_score,
                'Is Maintained': tool.is_actively_maintained,
                'Category': tool.category,
                'Features': tool.features,
            }
            tools_data.append(tool_data)
        
        print(f"✅ Retrieved {len(tools_data)} NPM packages")
        return tools_data
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        
        print("📊 Calculating summary statistics...")
        
        total_tools = self.db.query(func.count(DiscoveredTool.id)).scalar()
        
        high_activity = self.db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.activity_score >= 0.7
        ).scalar()
        
        actively_maintained = self.db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.is_actively_maintained == True
        ).scalar()
        
        with_scores = self.db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.activity_score.isnot(None)
        ).scalar()
        
        github_repos = self.db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.tool_type_detected == 'github_repo'
        ).scalar()
        
        npm_packages = self.db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.tool_type_detected == 'npm_package'
        ).scalar()
        
        web_apps = self.db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.tool_type_detected == 'web_application'
        ).scalar()
        
        avg_activity = self.db.query(func.avg(DiscoveredTool.activity_score)).scalar()
        avg_confidence = self.db.query(func.avg(DiscoveredTool.confidence_score)).scalar()
        
        return {
            'Total Tools': total_tools,
            'High Activity Tools (≥0.7)': high_activity,
            'High Activity %': round((high_activity / total_tools) * 100, 1) if total_tools > 0 else 0,
            'Actively Maintained': actively_maintained,
            'Maintenance %': round((actively_maintained / total_tools) * 100, 1) if total_tools > 0 else 0,
            'Tools with Activity Scores': with_scores,
            'Scoring Coverage %': round((with_scores / total_tools) * 100, 1) if total_tools > 0 else 0,
            'Average Activity Score': round(float(avg_activity), 3) if avg_activity else 0,
            'Average Confidence Score': round(float(avg_confidence), 3) if avg_confidence else 0,
            'GitHub Repositories': github_repos,
            'NPM Packages': npm_packages,
            'Web Applications': web_apps,
            'Export Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    def export_to_excel(self, filename: Optional[str] = None) -> str:
        """Export all data to Excel file with multiple sheets"""
        
        if filename is None:
            filename = f"ai_tools_database_{self.export_time}.xlsx"
        
        print(f"📊 Starting export to {filename}...")
        
        try:
            # Get all data
            all_tools = self.get_all_tools()
            high_activity = self.get_high_activity_tools()
            by_category = self.get_tools_by_category()
            by_type = self.get_tools_by_type()
            github_tools = self.get_github_tools()
            npm_tools = self.get_npm_tools()
            summary = self.get_summary_stats()
            
            # Create DataFrames
            df_all = pd.DataFrame(all_tools)
            df_high_activity = pd.DataFrame(high_activity)
            df_categories = pd.DataFrame(by_category)
            df_types = pd.DataFrame(by_type)
            df_github = pd.DataFrame(github_tools)
            df_npm = pd.DataFrame(npm_tools)
            df_summary = pd.DataFrame([summary])
            
            # Write to Excel with multiple sheets
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Summary sheet (most important first)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # High activity tools (most important)
                df_high_activity.to_excel(writer, sheet_name='High Activity Tools', index=False)
                
                # Statistics sheets
                df_categories.to_excel(writer, sheet_name='By Category', index=False)
                df_types.to_excel(writer, sheet_name='By Type', index=False)
                
                # Source-specific sheets
                if not df_github.empty:
                    df_github.to_excel(writer, sheet_name='GitHub Repos', index=False)
                if not df_npm.empty:
                    df_npm.to_excel(writer, sheet_name='NPM Packages', index=False)
                
                # All tools (comprehensive data)
                df_all.to_excel(writer, sheet_name='All Tools', index=False)
            
            print(f"✅ Export completed successfully!")
            print(f"📁 File saved as: {filename}")
            print(f"📊 Total records exported: {len(all_tools)}")
            print(f"🌟 High-activity tools: {len(high_activity)}")
            print(f"📋 Categories analyzed: {len(by_category)}")
            print(f"🔍 Tool types analyzed: {len(by_type)}")
            
            # Show copy command
            print(f"\n💡 To copy to your computer:")
            print(f"docker compose cp agent:/app/{filename} ./{filename}")
            
            return filename
            
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
            raise
        finally:
            self.db.close()

def main():
    """Main function with CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export AI Tools Database to Excel')
    parser.add_argument('--filename', '-f', type=str, help='Output filename (default: auto-generated)')
    parser.add_argument('--high-activity-only', action='store_true', help='Export only high-activity tools')
    parser.add_argument('--summary-only', action='store_true', help='Export only summary statistics')
    
    args = parser.parse_args()
    
    if not DATABASE_AVAILABLE:
        print("❌ Database not available. Run this script inside the Docker container:")
        print("docker compose exec agent python export_tools.py")
        return
    
    exporter = ToolsExporter()
    
    try:
        if args.summary_only:
            print("📊 Database Summary Statistics:")
            print("=" * 50)
            summary = exporter.get_summary_stats()
            for key, value in summary.items():
                print(f"  • {key}: {value}")
        
        elif args.high_activity_only:
            print("🌟 Exporting high-activity tools only...")
            filename = args.filename or f"high_activity_tools_{exporter.export_time}.xlsx"
            
            high_activity = exporter.get_high_activity_tools()
            if high_activity:
                df = pd.DataFrame(high_activity)
                df.to_excel(filename, index=False)
                print(f"✅ Exported {len(high_activity)} high-activity tools to {filename}")
                print(f"💡 To copy: docker compose cp agent:/app/{filename} ./{filename}")
            else:
                print("❌ No high-activity tools found")
        
        else:
            # Full export
            filename = exporter.export_to_excel(args.filename)
            
            print(f"\n🎉 Excel Export Complete!")
            print(f"📁 File: {filename}")
            print(f"📊 Contains 7 sheets:")
            print(f"   • Summary: Overall database statistics")
            print(f"   • High Activity Tools: Quality tools (score ≥ 0.7)")
            print(f"   • By Category: Category analysis")
            print(f"   • By Type: Tool type analysis")
            print(f"   • GitHub Repos: Repository details with stars")
            print(f"   • NPM Packages: Package details with downloads")
            print(f"   • All Tools: Complete database (all fields)")
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Export interrupted by user")
    except Exception as e:
        print(f"\n❌ Export failed: {str(e)}")
        # Check if it's a pandas/openpyxl issue
        if "pandas" in str(e).lower() or "openpyxl" in str(e).lower():
            print(f"\n💡 Try installing dependencies first:")
            print(f"docker compose exec agent pip install pandas openpyxl")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()