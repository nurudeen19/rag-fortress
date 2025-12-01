"""
Seeder for populating the activity_logs table with sample data.
Generates a variety of activity log entries to simulate real-world scenarios.
"""

from datetime import datetime, timedelta
import random
import json
from app.seeders.base import BaseSeed
from app.models.activity_log import ActivityLog

class ActivityLogsSeeder(BaseSeed):
    """Seeder for the activity_logs table."""

    name = "activity_logs"
    description = "Seeder for populating the activity_logs table with sample data."
    required_tables = ["activity_logs"]

    async def run(self, session):
        """Run the seeder."""
        incident_types = [
            "malicious_query_blocked",
            "document_access_granted",
            "document_access_denied",
            "insufficient_clearance",
            "clearance_override_used",
            "bulk_document_request",
            "suspicious_activity",
            "access_pattern_anomaly",
            "query_validation_failed",
            "sensitive_data_access",
        ]

        severities = ["info", "warning", "critical"]

        clearance_levels = [
            "GENERAL",
            "RESTRICTED",
            "CONFIDENTIAL",
            "HIGHLY_CONFIDENTIAL",
        ]

        for _ in range(100):  # Generate 100 entries
            log = ActivityLog(
                user_id=1,
                incident_type=random.choice(incident_types),
                severity=random.choice(severities),
                description=f"Sample description for incident {_}",
                details=json.dumps({"key": f"value_{_}"}),
                user_clearance_level=random.choice(clearance_levels),
                required_clearance_level=random.choice(clearance_levels),
                access_granted=random.choice([True, False]),
                user_query=f"SELECT * FROM table_{_}",
                threat_type=random.choice(["prompt_injection", "sql_injection", None]),
                ip_address=f"192.168.1.{random.randint(1, 255)}",
                user_agent=f"UserAgent {_}",
                created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
            )
            session.add(log)

        await session.commit()
        return {"success": True, "message": "Seeded activity_logs table with sample data."}