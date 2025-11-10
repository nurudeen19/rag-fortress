"""Seeders module initialization."""

from app.seeders.base import BaseSeed
from app.seeders.admin import AdminSeeder
from app.seeders.roles_permissions import RolesPermissionsSeeder
from app.seeders.departments import DepartmentsSeeder
from app.seeders.knowledge_base import KnowledgeBaseSeeder

# Available seeders mapping
SEEDERS = {
    "admin": AdminSeeder,
    "roles_permissions": RolesPermissionsSeeder,
    "departments": DepartmentsSeeder,
    "knowledge_base": KnowledgeBaseSeeder,
}

__all__ = ["BaseSeed", "AdminSeeder", "RolesPermissionsSeeder", "DepartmentsSeeder", "KnowledgeBaseSeeder", "SEEDERS"]
