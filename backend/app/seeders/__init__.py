"""Seeders module initialization."""

from app.seeders.base import BaseSeed
from app.seeders.admin import AdminSeeder
from app.seeders.app import AppSeeder

# Available seeders mapping
SEEDERS = {
    "admin": AdminSeeder,
    "app": AppSeeder,
}

__all__ = ["BaseSeed", "AdminSeeder", "AppSeeder", "SEEDERS"]
