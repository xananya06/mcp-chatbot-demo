from app.services.health_check_service import health_check_service
import logging

logging.basicConfig(level=logging.INFO)
print('🚀 Starting full database health check...')
result = health_check_service.sync_run_daily_health_checks(batch_size=200, max_tools=None)
print('🎉 COMPLETE!')
print(f'Tools checked: {result.get("total_tools_checked", 0)}')
print(f'Healthy: {result.get("healthy_tools", 0)}')
print(f'Unhealthy: {result.get("unhealthy_tools", 0)}')
print(f'Time: {result.get("processing_time", 0)} seconds')
