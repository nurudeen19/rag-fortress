"""Seeders module initialization."""

from app.seeders.base import BaseSeed
from app.seeders.admin import AdminSeeder
from app.seeders.roles_permissions import RolesPermissionsSeeder
from app.seeders.departments import DepartmentsSeeder
from app.seeders.knowledge_base import KnowledgeBaseSeeder
from app.seeders.jobs import JobsSeeder
from app.seeders.conversation import ConversationSeeder

# Available seeders mapping
SEEDERS = {
    "admin": AdminSeeder,
    "roles_permissions": RolesPermissionsSeeder,
    "departments": DepartmentsSeeder,
    "knowledge_base": KnowledgeBaseSeeder,
    "jobs": JobsSeeder,
    "conversations": ConversationSeeder,
}

__all__ = ["BaseSeed", "AdminSeeder", "RolesPermissionsSeeder", "DepartmentsSeeder", "KnowledgeBaseSeeder", "JobsSeeder", "ConversationSeeder", "SEEDERS"]
