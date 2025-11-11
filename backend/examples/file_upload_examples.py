"""
Example: Using FileUploadService with form data from frontend.
Demonstrates how the service handles file uploads with all fields.
"""

from app.services.file_upload_service import FileUploadService, FileUploadData
from app.models.file_upload import SecurityLevel


# Example 1: From FastAPI route with form submission
async def handle_file_upload(
    session,
    # Form fields from frontend
    file_path: str,
    file_name: str,
    file_type: str,
    file_size: int,
    user_id: int,
    department_id: int = None,
    is_department_only: bool = False,
    security_level: int = 1,
    file_purpose: str = None,
    field_selection: list = None,
):
    """
    Handle file upload from frontend form.
    
    Frontend sends JSON:
    {
        "file_path": "/uploads/data.csv",
        "file_name": "data.csv",
        "file_type": "csv",
        "file_size": 102400,
        "department_id": 5,
        "is_department_only": true,
        "security_level": 2,  # RESTRICTED
        "file_purpose": "Q4 sales data for analysis",
        "field_selection": ["name", "amount", "date"]
    }
    """
    service = FileUploadService(session)
    
    # Create data model from form submission
    data = FileUploadData(
        file_path=file_path,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        uploaded_by_id=user_id,
        department_id=department_id,
        is_department_only=is_department_only,
        security_level=security_level,
        file_purpose=file_purpose,
        field_selection=field_selection,
    )
    
    # Create upload record
    file_upload = await service.create_from_data(data)
    
    return {
        "id": file_upload.id,
        "token": file_upload.upload_token,
        "file_name": file_upload.file_name,
        "status": file_upload.status.value,
    }


# Example 2: Different security levels
async def create_with_security_levels(session, user_id):
    """Show different security level usage."""
    service = FileUploadService(session)
    
    # General - anyone can access
    general = await service.create_from_data(FileUploadData(
        file_path="/data/public.txt",
        file_name="public.txt",
        file_type="txt",
        file_size=1000,
        uploaded_by_id=user_id,
        security_level=SecurityLevel.GENERAL.value,
        file_purpose="Public documentation",
    ))
    
    # Restricted - internal only
    restricted = await service.create_from_data(FileUploadData(
        file_path="/data/internal.csv",
        file_name="internal.csv",
        file_type="csv",
        file_size=5000,
        uploaded_by_id=user_id,
        security_level=SecurityLevel.RESTRICTED.value,
        file_purpose="Internal metrics",
    ))
    
    # Confidential - specific department only
    confidential = await service.create_from_data(FileUploadData(
        file_path="/data/finance.xlsx",
        file_name="finance.xlsx",
        file_type="xlsx",
        file_size=10000,
        uploaded_by_id=user_id,
        department_id=3,  # Finance dept
        is_department_only=True,
        security_level=SecurityLevel.CONFIDENTIAL.value,
        file_purpose="Quarterly financial reports",
    ))
    
    # Highly confidential
    highly_confidential = await service.create_from_data(FileUploadData(
        file_path="/data/executive.pdf",
        file_name="executive.pdf",
        file_type="pdf",
        file_size=2000,
        uploaded_by_id=user_id,
        department_id=1,  # Executive dept
        is_department_only=True,
        security_level=SecurityLevel.HIGHLY_CONFIDENTIAL.value,
        file_purpose="Executive summary - confidential",
    ))
    
    return {
        "general": general.id,
        "restricted": restricted.id,
        "confidential": confidential.id,
        "highly_confidential": highly_confidential.id,
    }


# Example 3: Structured data extraction
async def create_with_field_extraction(session, user_id):
    """Create file with specific field extraction config."""
    service = FileUploadService(session)
    
    # CSV file with field selection
    csv_upload = await service.create_from_data(FileUploadData(
        file_path="/data/customers.csv",
        file_name="customers.csv",
        file_type="csv",
        file_size=50000,
        uploaded_by_id=user_id,
        security_level=SecurityLevel.RESTRICTED.value,
        file_purpose="Customer database for ingestion",
        field_selection=["id", "email", "company", "country"],  # Only extract these
    ))
    
    # JSON file with nested field extraction
    json_upload = await service.create_from_data(FileUploadData(
        file_path="/data/orders.json",
        file_name="orders.json",
        file_type="json",
        file_size=100000,
        uploaded_by_id=user_id,
        security_level=SecurityLevel.GENERAL.value,
        file_purpose="Order history for analysis",
        field_selection=["order_id", "customer.name", "total", "status"],
    ))
    
    return {
        "csv": csv_upload.id,
        "json": json_upload.id,
    }


# Example 4: Using individual parameters (backward compatible)
async def create_with_individual_params(session, user_id):
    """Alternative approach using individual parameters."""
    service = FileUploadService(session)
    
    # Using individual parameters instead of data model
    file_upload = await service.create_upload(
        file_path="/data/report.pdf",
        file_name="report.pdf",
        file_type="pdf",
        file_size=5000,
        uploaded_by_id=user_id,
        department_id=2,
        is_department_only=True,
        security_level=SecurityLevel.CONFIDENTIAL,
        file_purpose="Monthly report",
        field_selection=None,
    )
    
    return file_upload.id


# Example 5: FastAPI route integration
def fastapi_route_example():
    """
    FastAPI route showing real integration:
    
    @router.post("/upload")
    async def upload_file(
        session: AsyncSession,
        current_user: User,
        file_data: FileUploadData,  # Pydantic model from request body
    ):
        service = FileUploadService(session)
        file_data.uploaded_by_id = current_user.id
        
        file_upload = await service.create_from_data(file_data)
        await session.commit()
        
        return {
            "id": file_upload.id,
            "token": file_upload.upload_token,
            "status": "pending_approval"
        }
    """
    pass


# Security Level Reference
SECURITY_LEVELS = {
    1: "GENERAL",           # No restrictions
    2: "RESTRICTED",        # Internal use only
    3: "CONFIDENTIAL",      # Restricted access (often department-specific)
    4: "HIGHLY_CONFIDENTIAL", # Highly restricted (executive level)
}
