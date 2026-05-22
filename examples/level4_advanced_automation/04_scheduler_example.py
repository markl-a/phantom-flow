#!/usr/bin/env python3
"""
Task Scheduler Example
Demonstrates cron-like task scheduling
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_automation_framework.tools.scheduler_and_testing import TaskScheduler


def demo_task_scheduler():
    """Demonstrate task scheduling capabilities."""
    print("=" * 60)
    print("TASK SCHEDULER DEMO")
    print("=" * 60)

    scheduler = TaskScheduler()

    # Define task functions
    def backup_task():
        """Simulated backup task."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 Running backup task...")

    def report_task():
        """Simulated report generation task."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Generating report...")

    def cleanup_task():
        """Simulated cleanup task."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧹 Running cleanup...")

    def health_check():
        """Simulated health check."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💓 Health check: OK")

    print("\n1. SCHEDULING TASKS")
    print("-" * 60)

    # Schedule task every 3 seconds
    result = scheduler.schedule_task(health_check, 'seconds', interval=3)
    print(f"✓ Health check every 3 seconds: {result}")

    # Schedule task every 5 seconds
    result = scheduler.schedule_task(backup_task, 'seconds', interval=5)
    print(f"✓ Backup every 5 seconds: {result}")

    # Schedule task every 7 seconds
    result = scheduler.schedule_task(cleanup_task, 'seconds', interval=7)
    print(f"✓ Cleanup every 7 seconds: {result}")

    print("\n2. LISTING SCHEDULED JOBS")
    print("-" * 60)
    jobs = scheduler.list_jobs()
    print(f"Total jobs: {jobs['job_count']}")
    for i, job in enumerate(jobs['jobs'], 1):
        print(f"  Job {i}: Next run at {job['next_run']}")

    print("\n3. STARTING SCHEDULER")
    print("-" * 60)
    result = scheduler.start()
    print(f"Scheduler started: {result}")

    print("\n4. RUNNING TASKS FOR 15 SECONDS...")
    print("-" * 60)
    print("Watch the tasks execute below:\n")

    time.sleep(15)

    print("\n5. STOPPING SCHEDULER")
    print("-" * 60)
    result = scheduler.stop()
    print(f"Scheduler stopped: {result}")

    print("\n6. CLEARING ALL JOBS")
    print("-" * 60)
    result = scheduler.clear_all()
    print(f"All jobs cleared: {result}")

    print("\n7. PRACTICAL USE CASES")
    print("-" * 60)
    print("\nExample 1: Daily Report Generation")
    print("  scheduler.schedule_task(generate_report, 'daily', at_time='09:00')")

    print("\nExample 2: Hourly Data Sync")
    print("  scheduler.schedule_task(sync_data, 'hours', interval=1)")

    print("\nExample 3: Weekly Backup")
    print("  scheduler.schedule_task(backup_database, 'weekly')")

    print("\nExample 4: Every 5 Minutes Health Check")
    print("  scheduler.schedule_task(check_health, 'minutes', interval=5)")

    print("\n8. ADVANCED SCHEDULING PATTERNS")
    print("-" * 60)

    patterns = [
        ("Every 30 seconds", "seconds", 30),
        ("Every 15 minutes", "minutes", 15),
        ("Every 2 hours", "hours", 2),
        ("Every 3 days", "days", 3),
        ("Daily at specific time", "daily", "09:00"),
        ("Weekly", "weekly", 1)
    ]

    print("\nSupported Schedule Types:")
    for description, schedule_type, interval in patterns:
        print(f"  • {description}: schedule_task(func, '{schedule_type}', interval={interval})")


def production_example():
    """Show production-ready example."""
    print("\n\n" + "=" * 60)
    print("PRODUCTION EXAMPLE")
    print("=" * 60)

    code = '''
# Production scheduler setup
import logging
from task_scheduler import TaskScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = TaskScheduler()

# Define robust tasks with error handling
def daily_report():
    try:
        logger.info("Generating daily report...")
        # Your report logic here
        send_email_report()
        logger.info("Daily report sent successfully")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        notify_admin(e)

# Schedule tasks
scheduler.schedule_task(daily_report, 'daily', at_time='08:00')
scheduler.schedule_task(backup_db, 'hours', interval=6)
scheduler.schedule_task(cleanup_logs, 'days', interval=1)

# Start scheduler
scheduler.start()
logger.info("Scheduler started successfully")

# Keep running (in production, this would be in a service)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Shutting down scheduler...")
    scheduler.stop()
'''

    print(code)


if __name__ == "__main__":
    demo_task_scheduler()
    production_example()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ Flexible scheduling (seconds, minutes, hours, days)")
    print("  ✓ Specific time scheduling (daily/weekly)")
    print("  ✓ Background execution")
    print("  ✓ Job management (list, clear)")
    print("  ✓ Production-ready error handling")
