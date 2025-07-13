from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, case

from app.db.database import SessionLocal
from app.models.chat import DiscoveredTool, SourceTracking, ToolReport

class QualityDashboardService:
    """Quality dashboard implementing PDF requirements"""
    
    def get_health_check_metrics(self, db: Session) -> Dict[str, Any]:
        """Health check metrics for dashboard"""
        
        # Total tools with websites
        total_tools = db.query(func.count(DiscoveredTool.id)).filter(
            and_(
                DiscoveredTool.website.isnot(None),
                DiscoveredTool.website != ""
            )
        ).scalar()
        
        # Tools with working websites (200 status)
        healthy_tools = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.website_status == 200
        ).scalar()
        
        # Tools with recent health check failures (last 24 hours)
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        recent_failures = db.query(func.count(DiscoveredTool.id)).filter(
            and_(
                DiscoveredTool.last_health_check >= cutoff_24h,
                DiscoveredTool.website_status != 200,
                DiscoveredTool.website_status.isnot(None)
            )
        ).scalar()
        
        # Average confidence score
        avg_confidence = db.query(func.avg(DiscoveredTool.confidence_score)).filter(
            DiscoveredTool.confidence_score.isnot(None)
        ).scalar()
        
        # Tools never health checked
        never_checked = db.query(func.count(DiscoveredTool.id)).filter(
            and_(
                DiscoveredTool.last_health_check.is_(None),
                DiscoveredTool.website.isnot(None),
                DiscoveredTool.website != ""
            )
        ).scalar()
        
        # Status code distribution
        status_distribution = db.query(
            DiscoveredTool.website_status,
            func.count(DiscoveredTool.id).label('count')
        ).filter(
            DiscoveredTool.website_status.isnot(None)
        ).group_by(DiscoveredTool.website_status).all()
        
        return {
            "total_tools_with_websites": total_tools,
            "healthy_tools": healthy_tools,
            "health_percentage": round((healthy_tools / total_tools) * 100, 1) if total_tools > 0 else 0,
            "recent_failures_24h": recent_failures,
            "average_confidence_score": round(float(avg_confidence), 2) if avg_confidence else 0,
            "never_checked": never_checked,
            "status_code_distribution": {
                str(item.website_status): item.count for item in status_distribution
            }
        }
    
    def get_coverage_metrics(self, db: Session) -> Dict[str, Any]:
        """Coverage metrics for dashboard"""
        
        # Tools per category
        category_stats = db.query(
            DiscoveredTool.tool_type,
            func.count(DiscoveredTool.id).label('count'),
            func.avg(DiscoveredTool.confidence_score).label('avg_confidence')
        ).group_by(DiscoveredTool.tool_type).all()
        
        # Sources monitored
        sources = db.query(SourceTracking).all()
        active_sources = len([s for s in sources if s.is_active])
        
        # Geographic/pricing distribution
        pricing_distribution = db.query(
            case(
                (DiscoveredTool.pricing.ilike('%free%'), 'Free'),
                (DiscoveredTool.pricing.ilike('%freemium%'), 'Freemium'),
                (DiscoveredTool.pricing.ilike('%paid%'), 'Paid'),
                (DiscoveredTool.pricing.ilike('%enterprise%'), 'Enterprise'),
                else_='Other'
            ).label('pricing_category'),
            func.count(DiscoveredTool.id).label('count')
        ).group_by('pricing_category').all()
        
        return {
            "tools_per_category": {
                item.tool_type: {
                    "count": item.count,
                    "avg_confidence": round(float(item.avg_confidence), 2) if item.avg_confidence else 0
                }
                for item in category_stats
            },
            "total_categories": len(category_stats),
            "sources_monitored": len(sources),
            "active_sources": active_sources,
            "pricing_distribution": {
                item.pricing_category: item.count for item in pricing_distribution
            }
        }
    
    def get_discovery_metrics(self, db: Session) -> Dict[str, Any]:
        """Discovery metrics for dashboard"""
        
        # New tools found per day (last 7 days)
        daily_stats = []
        for i in range(7):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            daily_count = db.query(func.count(DiscoveredTool.id)).filter(
                and_(
                    DiscoveredTool.created_at >= day_start,
                    DiscoveredTool.created_at < day_end
                )
            ).scalar()
            
            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "tools_discovered": daily_count
            })
        
        # Duplicate detection rate (recent tools)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        total_recent = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.created_at >= recent_cutoff
        ).scalar()
        
        # Tools with canonical URLs (indicates duplicate detection ran)
        with_canonical = db.query(func.count(DiscoveredTool.id)).filter(
            and_(
                DiscoveredTool.created_at >= recent_cutoff,
                DiscoveredTool.canonical_url.isnot(None)
            )
        ).scalar()
        
        # Source productivity
        source_productivity = []
        for source in db.query(SourceTracking).all():
            hours_since_check = None
            if source.last_checked:
                hours_since_check = (datetime.utcnow() - source.last_checked).total_seconds() / 3600
            
            source_productivity.append({
                "source_name": source.source_name,
                "tools_found_last_run": source.new_tools_count,
                "is_active": source.is_active,
                "hours_since_check": round(hours_since_check, 1) if hours_since_check else None,
                "last_checked": source.last_checked
            })
        
        return {
            "new_tools_per_day_7d": daily_stats,
            "total_tools_last_7d": total_recent,
            "duplicate_detection_coverage": round((with_canonical / total_recent) * 100, 1) if total_recent > 0 else 0,
            "source_productivity": sorted(source_productivity, key=lambda x: x['tools_found_last_run'], reverse=True)
        }
    
    def get_user_feedback_metrics(self, db: Session) -> Dict[str, Any]:
        """User feedback metrics for dashboard"""
        
        # Total reports by type
        report_types = db.query(
            ToolReport.report_type,
            func.count(ToolReport.id).label('count')
        ).group_by(ToolReport.report_type).all()
        
        # Reports by status
        report_status = db.query(
            ToolReport.status,
            func.count(ToolReport.id).label('count')
        ).group_by(ToolReport.status).all()
        
        # Recent reports (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_reports = db.query(func.count(ToolReport.id)).filter(
            ToolReport.created_at >= recent_cutoff
        ).scalar()
        
        # Tools with most reports
        tools_with_reports = db.query(
            DiscoveredTool.name,
            DiscoveredTool.website,
            DiscoveredTool.user_reports,
            DiscoveredTool.confidence_score
        ).filter(
            DiscoveredTool.user_reports > 0
        ).order_by(desc(DiscoveredTool.user_reports)).limit(10).all()
        
        # Average resolution time for resolved reports
        resolved_reports = db.query(ToolReport).filter(
            and_(
                ToolReport.status == 'resolved',
                ToolReport.resolved_at.isnot(None)
            )
        ).all()
        
        avg_resolution_hours = None
        if resolved_reports:
            total_hours = sum([
                (report.resolved_at - report.created_at).total_seconds() / 3600 
                for report in resolved_reports
            ])
            avg_resolution_hours = round(total_hours / len(resolved_reports), 1)
        
        return {
            "total_reports": sum(item.count for item in report_types),
            "reports_by_type": {item.report_type: item.count for item in report_types},
            "reports_by_status": {item.status: item.count for item in report_status},
            "recent_reports_7d": recent_reports,
            "tools_with_most_reports": [
                {
                    "name": tool.name,
                    "website": tool.website,
                    "report_count": tool.user_reports,
                    "confidence_score": tool.confidence_score
                }
                for tool in tools_with_reports
            ],
            "average_resolution_time_hours": avg_resolution_hours
        }
    
    def get_confidence_distribution(self, db: Session) -> Dict[str, Any]:
        """Confidence score distribution for dashboard"""
        
        # Confidence ranges
        confidence_ranges = [
            (0.9, 1.0, "Excellent (0.9-1.0)"),
            (0.8, 0.9, "High (0.8-0.9)"),
            (0.7, 0.8, "Good (0.7-0.8)"),
            (0.6, 0.7, "Medium (0.6-0.7)"),
            (0.0, 0.6, "Low (0.0-0.6)")
        ]
        
        confidence_dist = {}
        total_with_confidence = 0
        
        for min_conf, max_conf, label in confidence_ranges:
            count = db.query(func.count(DiscoveredTool.id)).filter(
                and_(
                    DiscoveredTool.confidence_score >= min_conf,
                    DiscoveredTool.confidence_score < max_conf if max_conf < 1.0 else DiscoveredTool.confidence_score <= max_conf
                )
            ).scalar()
            
            confidence_dist[label] = count
            total_with_confidence += count
        
        # Tools without confidence scores
        no_confidence = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.confidence_score.is_(None)
        ).scalar()
        
        return {
            "confidence_distribution": confidence_dist,
            "total_tools_with_confidence": total_with_confidence,
            "tools_without_confidence": no_confidence,
            "high_confidence_percentage": round(
                (confidence_dist.get("Excellent (0.9-1.0)", 0) + confidence_dist.get("High (0.8-0.9)", 0)) / 
                total_with_confidence * 100, 1
            ) if total_with_confidence > 0 else 0
        }
    
    def get_comprehensive_dashboard(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard data as specified in PDF"""
        
        return {
            "dashboard_generated": datetime.utcnow().isoformat(),
            "health_check_metrics": self.get_health_check_metrics(db),
            "coverage_metrics": self.get_coverage_metrics(db),
            "discovery_metrics": self.get_discovery_metrics(db),
            "user_feedback_metrics": self.get_user_feedback_metrics(db),
            "confidence_distribution": self.get_confidence_distribution(db),
            "system_status": self._get_system_status(db)
        }
    
    def _get_system_status(self, db: Session) -> Dict[str, Any]:
        """Get overall system health status"""
        
        # Calculate system health indicators
        total_tools = db.query(func.count(DiscoveredTool.id)).scalar()
        healthy_tools = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.website_status == 200
        ).scalar()
        
        high_confidence_tools = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.confidence_score >= 0.8
        ).scalar()
        
        pending_reports = db.query(func.count(ToolReport.id)).filter(
            ToolReport.status == 'pending'
        ).scalar()
        
        active_sources = db.query(func.count(SourceTracking.id)).filter(
            SourceTracking.is_active == True
        ).scalar()
        
        # System health score (0-100)
        health_score = 0
        if total_tools > 0:
            health_percentage = (healthy_tools / total_tools) * 100
            confidence_percentage = (high_confidence_tools / total_tools) * 100
            
            health_score = (
                health_percentage * 0.4 +  # 40% weight on health
                confidence_percentage * 0.4 +  # 40% weight on confidence
                min(active_sources * 10, 20)  # 20% weight on active sources (max 20 points)
            )
        
        return {
            "overall_health_score": round(health_score, 1),
            "total_tools": total_tools,
            "healthy_tools": healthy_tools,
            "high_confidence_tools": high_confidence_tools,
            "pending_user_reports": pending_reports,
            "active_discovery_sources": active_sources,
            "system_alerts": self._generate_system_alerts(db)
        }
    
    def _generate_system_alerts(self, db: Session) -> List[Dict[str, str]]:
        """Generate system alerts for dashboard"""
        
        alerts = []
        
        # Check for high number of pending reports
        pending_reports = db.query(func.count(ToolReport.id)).filter(
            ToolReport.status == 'pending'
        ).scalar()
        
        if pending_reports > 10:
            alerts.append({
                "level": "warning",
                "message": f"{pending_reports} pending user reports need attention",
                "action": "Review and resolve user feedback"
            })
        
        # Check for tools with many user reports
        problematic_tools = db.query(func.count(DiscoveredTool.id)).filter(
            DiscoveredTool.user_reports >= 5
        ).scalar()
        
        if problematic_tools > 0:
            alerts.append({
                "level": "warning", 
                "message": f"{problematic_tools} tools have 5+ user reports",
                "action": "Review and update problematic tools"
            })
        
        # Check for stale health checks
        stale_cutoff = datetime.utcnow() - timedelta(days=7)
        stale_tools = db.query(func.count(DiscoveredTool.id)).filter(
            and_(
                DiscoveredTool.website.isnot(None),
                or_(
                    DiscoveredTool.last_health_check.is_(None),
                    DiscoveredTool.last_health_check < stale_cutoff
                )
            )
        ).scalar()
        
        if stale_tools > 1000:
            alerts.append({
                "level": "info",
                "message": f"{stale_tools} tools need health checks (>7 days old)",
                "action": "Run health check batch job"
            })
        
        # Check for inactive sources
        inactive_sources = db.query(func.count(SourceTracking.id)).filter(
            SourceTracking.is_active == False
        ).scalar()
        
        if inactive_sources > 0:
            alerts.append({
                "level": "info",
                "message": f"{inactive_sources} discovery sources are inactive",
                "action": "Review and reactivate sources"
            })
        
        return alerts
    
    def sync_get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Synchronous wrapper for FastAPI"""
        db = SessionLocal()
        try:
            return self.get_comprehensive_dashboard(db)
        finally:
            db.close()

# Global service instance
quality_dashboard_service = QualityDashboardService()