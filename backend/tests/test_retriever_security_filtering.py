"""
Test file for retriever security filtering functionality.

Tests the _filter_by_security() method that filters documents post-retrieval
based on user's security clearance and department access.
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from app.services.vector_store.retriever import RetrieverService
from app.models.user_permission import PermissionLevel


@pytest.fixture
def mock_retriever():
    """Create a RetrieverService with mocked dependencies."""
    with patch('app.services.vector_store.retriever.get_retriever') as mock_get_retriever, \
         patch('app.services.vector_store.retriever.get_cache') as mock_cache, \
         patch('app.services.vector_store.retriever.get_reranker_service'):
        
        mock_get_retriever.return_value = MagicMock()
        mock_cache.return_value = MagicMock()
        
        retriever = RetrieverService()
        yield retriever


class TestSecurityFiltering:
    """Test post-retrieval security filtering logic."""
    
    def test_filter_by_security_level_general(self, mock_retriever):
        """Test that GENERAL user can only access GENERAL documents."""
        documents = [
            Document(page_content="Public info", metadata={"security_level": "GENERAL", "source": "doc1.pdf"}),
            Document(page_content="Restricted info", metadata={"security_level": "RESTRICTED", "source": "doc2.pdf"}),
            Document(page_content="Confidential info", metadata={"security_level": "CONFIDENTIAL", "source": "doc3.pdf"}),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        
        assert len(filtered_docs) == 1
        assert filtered_docs[0].metadata["security_level"] == "GENERAL"
        assert max_level == PermissionLevel.GENERAL.value
        assert blocked_depts is None or blocked_depts == []
    
    def test_filter_by_security_level_restricted(self, mock_retriever):
        """Test that RESTRICTED user can access GENERAL and RESTRICTED documents."""
        documents = [
            Document(page_content="Public info", metadata={"security_level": "GENERAL", "source": "doc1.pdf"}),
            Document(page_content="Restricted info", metadata={"security_level": "RESTRICTED", "source": "doc2.pdf"}),
            Document(page_content="Confidential info", metadata={"security_level": "CONFIDENTIAL", "source": "doc3.pdf"}),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=None
        )
        
        assert len(filtered_docs) == 2
        assert filtered_docs[0].metadata["security_level"] == "GENERAL"
        assert filtered_docs[1].metadata["security_level"] == "RESTRICTED"
        assert max_level == PermissionLevel.RESTRICTED.value
    
    def test_filter_by_security_level_highly_confidential(self, mock_retriever):
        """Test that HIGHLY_CONFIDENTIAL user can access all documents."""
        documents = [
            Document(page_content="Public info", metadata={"security_level": "GENERAL", "source": "doc1.pdf"}),
            Document(page_content="Restricted info", metadata={"security_level": "RESTRICTED", "source": "doc2.pdf"}),
            Document(page_content="Confidential info", metadata={"security_level": "CONFIDENTIAL", "source": "doc3.pdf"}),
            Document(page_content="Highly confidential info", metadata={"security_level": "HIGHLY_CONFIDENTIAL", "source": "doc4.pdf"}),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.HIGHLY_CONFIDENTIAL.value,
            user_department_id=None
        )
        
        assert len(filtered_docs) == 4
        assert max_level == PermissionLevel.HIGHLY_CONFIDENTIAL.value
    
    def test_department_filtering_user_without_department(self, mock_retriever):
        """Test that user without department can only access non-department documents."""
        documents = [
            Document(page_content="Public info", metadata={
                "security_level": "GENERAL",
                "source": "doc1.pdf",
                "is_department_only": False
            }),
            Document(page_content="Sales dept info", metadata={
                "security_level": "GENERAL",
                "source": "doc2.pdf",
                "is_department_only": True,
                "department_id": 5,
                "department": "Sales"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None  # No department
        )
        
        assert len(filtered_docs) == 1
        assert filtered_docs[0].metadata["is_department_only"] is False
        assert blocked_depts == ["Sales"]
    
    def test_department_filtering_user_with_department_access(self, mock_retriever):
        """Test that user with department can access their department documents."""
        documents = [
            Document(page_content="Public info", metadata={
                "security_level": "GENERAL",
                "source": "doc1.pdf",
                "is_department_only": False
            }),
            Document(page_content="Sales dept info", metadata={
                "security_level": "GENERAL",
                "source": "doc2.pdf",
                "is_department_only": True,
                "department_id": 5,
                "department": "Sales"
            }),
            Document(page_content="Engineering dept info", metadata={
                "security_level": "GENERAL",
                "source": "doc3.pdf",
                "is_department_only": True,
                "department_id": 10,
                "department": "Engineering"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=5,  # Sales department
            user_department_security_level=PermissionLevel.GENERAL.value
        )
        
        assert len(filtered_docs) == 2
        assert any(doc.metadata.get("department_id") == 5 for doc in filtered_docs)
        assert not any(doc.metadata.get("department_id") == 10 for doc in filtered_docs)
        assert blocked_depts == ["Engineering"]
    
    def test_department_filtering_insufficient_department_clearance(self, mock_retriever):
        """Test that user without sufficient department clearance is blocked."""
        documents = [
            Document(page_content="Restricted Sales info", metadata={
                "security_level": "RESTRICTED",
                "source": "doc1.pdf",
                "is_department_only": True,
                "department_id": 5,
                "department": "Sales"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.RESTRICTED.value,  # Has org clearance
            user_department_id=5,  # In Sales department
            user_department_security_level=PermissionLevel.GENERAL.value  # But insufficient dept clearance
        )
        
        assert len(filtered_docs) == 0
        assert blocked_depts == ["Sales"]
    
    def test_combined_security_and_department_filtering(self, mock_retriever):
        """Test combined security level and department filtering."""
        documents = [
            # Accessible: Public + non-dept
            Document(page_content="Public info", metadata={
                "security_level": "GENERAL",
                "source": "doc1.pdf",
                "is_department_only": False
            }),
            # Accessible: Public + user's dept
            Document(page_content="Sales public info", metadata={
                "security_level": "GENERAL",
                "source": "doc2.pdf",
                "is_department_only": True,
                "department_id": 5,
                "department": "Sales"
            }),
            # Blocked: Too high security level
            Document(page_content="Confidential info", metadata={
                "security_level": "CONFIDENTIAL",
                "source": "doc3.pdf",
                "is_department_only": False
            }),
            # Blocked: Different department
            Document(page_content="Engineering info", metadata={
                "security_level": "GENERAL",
                "source": "doc4.pdf",
                "is_department_only": True,
                "department_id": 10,
                "department": "Engineering"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=5,
            user_department_security_level=PermissionLevel.RESTRICTED.value
        )
        
        assert len(filtered_docs) == 2
        assert max_level == PermissionLevel.GENERAL.value
        assert "Engineering" in blocked_depts
    
    def test_empty_documents_list(self, mock_retriever):
        """Test filtering with empty documents list."""
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=[],
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        
        assert len(filtered_docs) == 0
        assert max_level is None
        assert blocked_depts is None or blocked_depts == []
    
    def test_invalid_security_level_skipped(self, mock_retriever):
        """Test that documents with invalid security levels are skipped."""
        documents = [
            Document(page_content="Valid doc", metadata={
                "security_level": "GENERAL",
                "source": "doc1.pdf"
            }),
            Document(page_content="Invalid doc", metadata={
                "security_level": "INVALID_LEVEL",
                "source": "doc2.pdf"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        
        # Only valid document should be included
        assert len(filtered_docs) == 1
        assert filtered_docs[0].metadata["source"] == "doc1.pdf"
    
    def test_integer_security_levels(self, mock_retriever):
        """Test that integer security levels are handled correctly."""
        documents = [
            Document(page_content="Info 1", metadata={
                "security_level": 1,  # Integer instead of string
                "source": "doc1.pdf"
            }),
            Document(page_content="Info 2", metadata={
                "security_level": 2,
                "source": "doc2.pdf"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=None
        )
        
        # Should handle integer levels correctly
        assert len(filtered_docs) == 2
    
    def test_max_security_level_tracking(self, mock_retriever):
        """Test that max security level is correctly tracked."""
        documents = [
            Document(page_content="Public", metadata={"security_level": "GENERAL", "source": "doc1.pdf"}),
            Document(page_content="Restricted", metadata={"security_level": "RESTRICTED", "source": "doc2.pdf"}),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.CONFIDENTIAL.value,
            user_department_id=None
        )
        
        # Max level should be the highest accessed (RESTRICTED)
        assert max_level == PermissionLevel.RESTRICTED.value
        assert len(filtered_docs) == 2
    
    def test_multiple_blocked_departments(self, mock_retriever):
        """Test that multiple blocked departments are tracked."""
        documents = [
            Document(page_content="Sales info", metadata={
                "security_level": "GENERAL",
                "source": "doc1.pdf",
                "is_department_only": True,
                "department_id": 5,
                "department": "Sales"
            }),
            Document(page_content="Engineering info", metadata={
                "security_level": "GENERAL",
                "source": "doc2.pdf",
                "is_department_only": True,
                "department_id": 10,
                "department": "Engineering"
            }),
            Document(page_content="Marketing info", metadata={
                "security_level": "GENERAL",
                "source": "doc3.pdf",
                "is_department_only": True,
                "department_id": 15,
                "department": "Marketing"
            }),
        ]
        
        filtered_docs, max_level, blocked_depts = mock_retriever._filter_by_security(
            documents=documents,
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None  # No department
        )
        
        assert len(filtered_docs) == 0
        assert set(blocked_depts) == {"Sales", "Engineering", "Marketing"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
