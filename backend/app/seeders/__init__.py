"""Seeders module initialization."""

from app.seeders.base import BaseSeed
from app.seeders.admin import AdminSeeder
from app.seeders.roles_permissions import RolesPermissionsSeeder

# Available seeders mapping
SEEDERS = {
    "admin": AdminSeeder,
    "roles_permissions": RolesPermissionsSeeder,
}

__all__ = ["BaseSeed", "AdminSeeder", "RolesPermissionsSeeder", "SEEDERS"]
