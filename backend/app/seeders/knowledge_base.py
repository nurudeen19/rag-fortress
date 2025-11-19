"""Knowledge base file seeder for demo files."""

import logging
import hashlib
import csv
import json
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.file_upload import FileUpload, FileStatus, SecurityLevel
from app.models.department import Department
from app.seeders.base import BaseSeed
from app.services.file_upload import FileStorage

logger = logging.getLogger(__name__)

# Demo data path - relative to backend directory
DEMO_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_base" / "demo_data"

# Base files directory where all files are stored
FILES_BASE_DIR = Path(__file__).parent.parent.parent / "data" / "files"

# Department mapping: folder name -> department code
DEPARTMENT_MAPPING = {
    "hr": "HR",
    "engineering": "ENG",
    "sales": "SALES",
    "finance": "FIN",
}

# Security level mapping based on file location/type
# Note: These are defaults; actual security level can vary per department
SECURITY_LEVEL_MAPPING = {
    "confidential": SecurityLevel.HIGHLY_CONFIDENTIAL,  # Executive files - highest security
    "departments": SecurityLevel.RESTRICTED,           # Department files - restricted to dept
    "root": SecurityLevel.GENERAL,                     # Company-wide - general access
}


class FileInfo:
    """Represents a file to be seeded into the knowledge base."""
    
    def __init__(self, file_path: Path, file_type: str, security_level: SecurityLevel, 
                 department_id: int = None, is_department_only: bool = False, 
                 field_selection: list = None, file_purpose: str = None):
        self.file_path = file_path
        self.file_type = file_type
        self.security_level = security_level
        self.department_id = department_id
        self.is_department_only = is_department_only  # True = dept-only access, False = org-wide
        self.field_selection = field_selection  # For CSV files
        self.file_purpose = file_purpose  # Why this file is being ingested
        self.file_hash = None
        
    def compute_hash(self) -> str:
        """Compute SHA256 hash of file for deduplication."""
        if self.file_hash:
            return self.file_hash
            
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        self.file_hash = sha256_hash.hexdigest()
        return self.file_hash


class KnowledgeBaseSeeder(BaseSeed):
    """Seeder for populating knowledge base with demo files."""
    
    name = "knowledge_base"
    description = "Loads demo files from knowledge_base/demo_data into file_uploads"
    required_tables = ["file_uploads", "departments"]  # Required tables
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Load demo knowledge base files into the database."""
        try:
            # Validate required tables exist
            tables_exist, missing_tables = await self.validate_tables_exist(session)
            if not tables_exist:
                error_msg = (
                    f"Required table(s) missing: {', '.join(missing_tables)}. "
                    "Please run migrations first: python migrate.py"
                )
                logger.error(error_msg)
                return {"success": False, "message": error_msg}
            
            # Check if demo_data exists
            if not DEMO_DATA_PATH.exists():
                error_msg = f"Demo data path not found: {DEMO_DATA_PATH}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}
            
            logger.info(f"Scanning demo data path: {DEMO_DATA_PATH}")
            
            # Load departments from database for mapping
            dept_map = await self._load_department_mapping(session)
            logger.debug(f"Department mapping: {dept_map}")
            
            # Discover all files to seed
            files_to_seed = await self._discover_files(dept_map)
            logger.info(f"Discovered {len(files_to_seed)} files to seed")
            
            if not files_to_seed:
                return {"success": True, "message": "No demo files found to seed"}
            
            # Create FileUpload records
            created_count = 0
            for file_info in files_to_seed:
                # Check if file already exists by hash
                file_hash = file_info.compute_hash()
                stmt = select(FileUpload).where(FileUpload.file_hash == file_hash)
                result = await session.execute(stmt)
                if result.scalars().first():
                    logger.debug(f"File already exists (hash: {file_hash[:8]}...): {file_info.file_path.name}")
                    continue
                
                # Create FileUpload record
                try:
                    file_upload = await self._create_file_upload_record(file_info, session)
                    session.add(file_upload)
                    created_count += 1
                    logger.debug(f"Added file: {file_info.file_path.name}")
                except Exception as e:
                    logger.error(f"Error processing file {file_info.file_path}: {e}")
                    continue
            
            if created_count > 0:
                await session.commit()
                message = f"Created {created_count} knowledge base file records"
                logger.info(f"✓ {message}")
                return {"success": True, "message": message}
            
            return {"success": True, "message": "All knowledge base files already exist"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed knowledge base: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
    
    async def _load_department_mapping(self, session: AsyncSession) -> dict:
        """Load department codes to IDs mapping from database."""
        stmt = select(Department).where(Department.code.in_(DEPARTMENT_MAPPING.values()))
        result = await session.execute(stmt)
        departments = result.scalars().all()
        
        mapping = {}
        for dept in departments:
            mapping[dept.code] = dept.id
        
        return mapping
    
    async def _discover_files(self, dept_map: dict) -> list:
        """Discover all files in demo_data folder and create FileInfo objects."""
        files_to_seed = []
        
        # 1. Company-wide files (root of demo_data)
        # These are org-wide, not department-specific
        for file_path in DEMO_DATA_PATH.glob("*.md"):
            file_info = FileInfo(
                file_path=file_path,
                file_type=self._get_file_type(file_path),
                security_level=SecurityLevel.GENERAL,
                department_id=None,
                is_department_only=False,  # Org-wide access
                field_selection=None,
                file_purpose="Company-wide knowledge base"
            )
            files_to_seed.append(file_info)
            logger.debug(f"Added company-wide file: {file_path.name}")
        
        # 2. Confidential files
        # These are org-wide but restricted to high-level access
        confidential_dir = DEMO_DATA_PATH / "confidential"
        if confidential_dir.exists():
            for file_path in confidential_dir.glob("*"):
                if file_path.is_file():
                    file_info = FileInfo(
                        file_path=file_path,
                        file_type=self._get_file_type(file_path),
                        security_level=SecurityLevel.HIGHLY_CONFIDENTIAL,
                        department_id=None,
                        is_department_only=False,  # Org-wide but confidential
                        field_selection=None,
                        file_purpose="Executive confidential knowledge base"
                    )
                    files_to_seed.append(file_info)
                    logger.debug(f"Added confidential file: {file_path.name}")
        
        # 3. Department-specific files
        # These can have varying security levels but are marked as department-only access
        depts_dir = DEMO_DATA_PATH / "departments"
        if depts_dir.exists():
            for dept_dir in depts_dir.iterdir():
                if not dept_dir.is_dir():
                    continue
                
                dept_name = dept_dir.name.lower()
                if dept_name not in DEPARTMENT_MAPPING:
                    logger.warning(f"Unknown department folder: {dept_name}")
                    continue
                
                dept_code = DEPARTMENT_MAPPING[dept_name]
                dept_id = dept_map.get(dept_code)
                
                if not dept_id:
                    logger.warning(f"Department not found in database: {dept_code}")
                    continue
                
                # Process all files in department folder
                for file_path in dept_dir.glob("*"):
                    if not file_path.is_file():
                        continue
                    
                    file_type = self._get_file_type(file_path)
                    
                    # Extract field selection for CSV files
                    field_selection = None
                    if file_type == "csv":
                        field_selection = await self._extract_csv_fields(file_path)
                    
                    # Department files can have different security levels (GENERAL, RESTRICTED, etc.)
                    # but are marked as department-only for access control
                    file_info = FileInfo(
                        file_path=file_path,
                        file_type=file_type,
                        security_level=SecurityLevel.RESTRICTED,  # Default for dept files
                        department_id=dept_id,
                        is_department_only=True,  # Restrict access to this department
                        field_selection=field_selection,
                        file_purpose=f"{dept_code} department knowledge base"
                    )
                    files_to_seed.append(file_info)
                    logger.debug(f"Added {dept_name} file (dept-only): {file_path.name}")
        
        return files_to_seed
    
    async def _extract_csv_fields(self, csv_path: Path) -> str:
        """Extract field names from CSV file and return as JSON."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    # Return as JSON string
                    return json.dumps(list(reader.fieldnames))
        except Exception as e:
            logger.error(f"Error extracting CSV fields from {csv_path}: {e}")
        
        return None
    
    def _get_file_type(self, file_path: Path) -> str:
        """Get file type from extension."""
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return "csv"
        elif suffix == ".md":
            return "markdown"
        elif suffix == ".txt":
            return "text"
        elif suffix == ".json":
            return "json"
        elif suffix == ".pdf":
            return "pdf"
        else:
            return "unknown"
    
    async def _create_file_upload_record(self, file_info: FileInfo, session: AsyncSession) -> FileUpload:
        """Create a FileUpload record from FileInfo.
        
        Copies file to unified storage location (data/files/knowledge_base/).
        Stores relative path like 'knowledge_base/filename.md'.
        """
        try:
            # Ensure knowledge_base directory exists
            kb_storage_dir = FILES_BASE_DIR / "knowledge_base"
            kb_storage_dir.mkdir(parents=True, exist_ok=True)
            
            file_size = file_info.file_path.stat().st_size
            file_name = file_info.file_path.name
            
            # Generate unique token
            import uuid
            upload_token = f"kb_{uuid.uuid4().hex[:16]}"
            
            # Copy file to unified storage location
            dest_path = kb_storage_dir / file_name
            with open(file_info.file_path, "rb") as src:
                with open(dest_path, "wb") as dst:
                    dst.write(src.read())
            
            # Store relative path from data/files/
            rel_path = f"knowledge_base/{file_name}"
            
            # Calculate hash of the actual file
            file_hash = file_info.compute_hash()
            
            file_upload = FileUpload(
                upload_token=upload_token,
                file_name=file_name,
                file_type=file_info.file_type,
                file_size=file_size,
                file_path=rel_path,  # Relative path: knowledge_base/filename.md
                file_hash=file_hash,
                status=FileStatus.APPROVED,  # Pre-approved for seeding
                security_level=file_info.security_level,
                department_id=file_info.department_id,
                is_department_only=file_info.is_department_only,
                field_selection=file_info.field_selection,
                file_purpose=file_info.file_purpose,
                approval_reason="Demo knowledge base seed - pre-approved",
                uploaded_by_id=None,  # Seeder system user
            )
            
            logger.debug(f"Created file record: {rel_path}")
            return file_upload
        
        except Exception as e:
            logger.error(f"Error creating file upload record: {e}", exc_info=True)
            raise
