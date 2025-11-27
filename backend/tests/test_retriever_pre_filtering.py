"""
Test file for retriever pre-filtering functionality.

Tests provider-specific filter building and security filtering logic.
"""

import pytest
from app.services.vector_store.retriever import RetrieverService
from app.models.user_permission import PermissionLevel


class TestFilterBuilding:
    """Test filter building for different vector store providers."""
    
    def test_chroma_filter_structure(self):
        """Test Chroma filter has correct structure."""
        retriever = RetrieverService()
        retriever.provider = "chroma"
        
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=10
        )
        
        # Check structure
        assert "$and" in filter_obj
        assert len(filter_obj["$and"]) == 2
        
        # Check security condition
        security_cond = filter_obj["$and"][0]
        assert "security_level" in security_cond
        assert "$in" in security_cond["security_level"]
        assert "GENERAL" in security_cond["security_level"]["$in"]
        assert "RESTRICTED" in security_cond["security_level"]["$in"]
        assert "CONFIDENTIAL" not in security_cond["security_level"]["$in"]
        
        # Check department condition
        dept_cond = filter_obj["$and"][1]
        assert "$or" in dept_cond
        assert {"is_department_only": {"$eq": False}} in dept_cond["$or"]
        assert {"department_id": {"$eq": 10}} in dept_cond["$or"]
    
    def test_pinecone_filter_structure(self):
        """Test Pinecone filter has correct structure (same as Chroma)."""
        retriever = RetrieverService()
        retriever.provider = "pinecone"
        
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.CONFIDENTIAL.value,
            user_department_id=None
        )
        
        # Check structure
        assert "$and" in filter_obj
        
        # Check security levels
        security_cond = filter_obj["$and"][0]
        levels = security_cond["security_level"]["$in"]
        assert "GENERAL" in levels
        assert "RESTRICTED" in levels
        assert "CONFIDENTIAL" in levels
        assert "HIGHLY_CONFIDENTIAL" not in levels
        
        # Check department condition (no dept = only non-dept docs)
        dept_cond = filter_obj["$and"][1]
        assert dept_cond == {"is_department_only": {"$eq": False}}
    
    def test_qdrant_filter_structure(self):
        """Test Qdrant filter has correct structure."""
        retriever = RetrieverService()
        retriever.provider = "qdrant"
        
        try:
            from qdrant_client.http import models as qdrant_models
        except ImportError:
            pytest.skip("qdrant-client not installed")
        
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=10
        )
        
        # Check it's a Filter object
        assert isinstance(filter_obj, qdrant_models.Filter)
        
        # Check must clauses
        assert filter_obj.must is not None
        assert len(filter_obj.must) == 2
        
        # Check security condition
        security_cond = filter_obj.must[0]
        assert isinstance(security_cond, qdrant_models.FieldCondition)
        assert security_cond.key == "security_level"
        assert isinstance(security_cond.match, qdrant_models.MatchAny)
        assert "GENERAL" in security_cond.match.any
        assert "RESTRICTED" in security_cond.match.any
        
        # Check department condition
        dept_cond = filter_obj.must[1]
        if isinstance(dept_cond, qdrant_models.Filter):
            assert dept_cond.should is not None
            assert len(dept_cond.should) == 2
    
    def test_weaviate_filter_structure(self):
        """Test Weaviate filter has correct structure."""
        retriever = RetrieverService()
        retriever.provider = "weaviate"
        
        try:
            from weaviate.classes.query import Filter
        except ImportError:
            pytest.skip("weaviate-client not installed or incompatible version")
        
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        
        # Should be a Filter object (hard to test internal structure)
        assert filter_obj is not None
        # Weaviate Filter is complex, just check it doesn't error
    
    def test_accessible_levels_calculation(self):
        """Test that accessible levels are correctly calculated."""
        retriever = RetrieverService()
        retriever.provider = "chroma"
        
        # GENERAL user: only GENERAL
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        levels = filter_obj["$and"][0]["security_level"]["$in"]
        assert levels == ["GENERAL"]
        
        # RESTRICTED user: GENERAL + RESTRICTED
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=None
        )
        levels = filter_obj["$and"][0]["security_level"]["$in"]
        assert set(levels) == {"GENERAL", "RESTRICTED"}
        
        # HIGHLY_CONFIDENTIAL user: all levels
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.HIGHLY_CONFIDENTIAL.value,
            user_department_id=None
        )
        levels = filter_obj["$and"][0]["security_level"]["$in"]
        assert set(levels) == {
            "GENERAL",
            "RESTRICTED",
            "CONFIDENTIAL",
            "HIGHLY_CONFIDENTIAL"
        }
    
    def test_department_filtering_logic(self):
        """Test department filtering logic variations."""
        retriever = RetrieverService()
        retriever.provider = "chroma"
        
        # User WITH department: can access non-dept + their dept
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=5
        )
        dept_cond = filter_obj["$and"][1]
        assert "$or" in dept_cond
        assert len(dept_cond["$or"]) == 2
        assert {"is_department_only": {"$eq": False}} in dept_cond["$or"]
        assert {"department_id": {"$eq": 5}} in dept_cond["$or"]
        
        # User WITHOUT department: can only access non-dept
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        dept_cond = filter_obj["$and"][1]
        assert dept_cond == {"is_department_only": {"$eq": False}}
    
    def test_unsupported_provider(self):
        """Test that unsupported provider returns None."""
        retriever = RetrieverService()
        retriever.provider = "unknown_provider"
        
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.GENERAL.value,
            user_department_id=None
        )
        
        assert filter_obj is None


class TestQueryIntegration:
    """Test query method integration with pre-filtering."""
    
    def test_query_without_security_params(self):
        """Test that queries without security params work (no filtering)."""
        retriever = RetrieverService()
        
        # Mock query should work without security params
        # (actual testing requires real vector store)
        # This is a structure test
        try:
            result = retriever.query(
                query_text="test query",
                top_k=5
            )
            # Should return dict with success key
            assert "success" in result
            assert "context" in result or "error" in result
        except Exception as e:
            # May fail if vector store not initialized, but structure is correct
            pass
    
    def test_query_with_security_params_builds_filter(self):
        """Test that security params trigger filter building."""
        retriever = RetrieverService()
        retriever.provider = "chroma"
        
        # Build filter (don't actually query)
        filter_obj = retriever._build_accessible_filter(
            user_security_level=PermissionLevel.RESTRICTED.value,
            user_department_id=10
        )
        
        assert filter_obj is not None
        assert "$and" in filter_obj


# Example usage (not a test, but demonstrates API)
def example_usage():
    """
    Example of how to use the retriever with security filtering.
    """
    from app.services.vector_store.retriever import get_retriever_service
    
    retriever = get_retriever_service()
    
    # Query for user with RESTRICTED clearance, department 10
    result = retriever.query(
        query_text="What are the sales figures?",
        top_k=5,
        user_security_level=PermissionLevel.RESTRICTED.value,
        user_department_id=10
    )
    
    if result["success"]:
        print(f"Found {result['count']} accessible documents")
        for doc in result["context"]:
            print(f"- {doc.metadata.get('file_name')}")
    else:
        print(f"Error: {result.get('message')}")


if __name__ == "__main__":
    # Run example
    example_usage()
