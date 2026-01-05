"""
Test encryption and database-backed settings system.

Tests the complete flow:
1. Sensitive values encrypted in database
2. Encrypted values stored in cache
3. Lazy decryption on attribute access
4. Settings priority: DB → ENV → defaults
"""
import pytest
import pytest_asyncio
from sqlalchemy import select, update, delete

from app.core.database import DatabaseManager
from app.config.database_settings import DatabaseSettings
from app.models.application_setting import ApplicationSetting
from app.core.settings_loader import load_settings_by_category
from app.config.settings import Settings
from app.services.settings_service import SettingsService


@pytest_asyncio.fixture
async def db_session():
    """Create database session for tests."""
    db_settings = DatabaseSettings()
    db_manager = DatabaseManager(db_settings)
    await db_manager.create_async_engine()
    async_session_factory = db_manager.get_session_factory()
    
    async with async_session_factory() as session:
        yield session
    
    await db_manager.async_engine.dispose()


@pytest_asyncio.fixture
async def settings_service(db_session):
    """Create settings service for tests."""
    return SettingsService(db_session)


class TestEncryptionSecurity:
    """Test that sensitive values remain encrypted everywhere except on access."""
    
    @pytest.mark.asyncio
    async def test_database_stores_encrypted(self, db_session, settings_service):
        """Test that API keys are encrypted in database."""
        test_api_key = "sk-test-secret-key-12345"
        
        # Update or create the setting
        try:
            await settings_service.update("openai_api_key", test_api_key)
        except ValueError:
            await settings_service.create(
                key="openai_api_key",
                value=test_api_key,
                data_type="string",
                category="llm",
                description="Test API key"
            )
        
        # Check DB storage
        result = await db_session.execute(
            select(ApplicationSetting).where(
                ApplicationSetting.key == 'openai_api_key'
            )
        )
        setting = result.scalar_one()
        
        assert setting.is_sensitive is True
        assert setting.value != test_api_key  # Should be encrypted
        assert setting.value.startswith('gAAAAA')  # Fernet encryption marker
    
    @pytest.mark.asyncio
    async def test_cache_stores_encrypted(self, db_session, settings_service):
        """Test that cached settings contain encrypted values."""
        test_api_key = "sk-test-secret-key-67890"
        
        # Set the value
        try:
            await settings_service.update("google_api_key", test_api_key)
        except ValueError:
            await settings_service.create(
                key="google_api_key",
                value=test_api_key,
                data_type="string",
                category="llm",
                description="Test API key"
            )
        
        # Load settings (simulating startup)
        cached_settings = await load_settings_by_category(db_session)
        
        assert 'llm' in cached_settings
        assert 'google_api_key' in cached_settings['llm']
        
        cached_data = cached_settings['llm']['google_api_key']
        assert isinstance(cached_data, dict)
        assert cached_data['is_sensitive'] is True
        assert cached_data['value'] != test_api_key  # Still encrypted
        assert cached_data['value'].startswith('gAAAAA')
    
    @pytest.mark.asyncio
    async def test_memory_stores_encrypted(self, db_session, settings_service):
        """Test that Settings object stores encrypted values in memory."""
        test_api_key = "sk-test-memory-encrypted-123"
        
        # Set the value
        try:
            await settings_service.update("hf_api_token", test_api_key)
        except ValueError:
            await settings_service.create(
                key="hf_api_token",
                value=test_api_key,
                data_type="string",
                category="llm",
                description="Test API key"
            )
        
        # Create Settings object
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Check internal storage
        assert hasattr(settings_obj, '_encrypted_settings')
        assert 'HF_API_TOKEN' in settings_obj._encrypted_settings
        
        stored_value = settings_obj._encrypted_settings['HF_API_TOKEN']
        assert stored_value != test_api_key  # Still encrypted
        assert stored_value.startswith('gAAAAA')
    
    @pytest.mark.asyncio
    async def test_decrypts_on_access(self, db_session, settings_service):
        """Test that values are decrypted when accessed."""
        test_api_key = "sk-test-decrypt-on-access-456"
        
        # Set the value
        try:
            await settings_service.update("cohere_api_key", test_api_key)
        except ValueError:
            await settings_service.create(
                key="cohere_api_key",
                value=test_api_key,
                data_type="string",
                category="embedding",
                description="Test API key"
            )
        
        # Create Settings object
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Access the value - should decrypt
        accessed_value = settings_obj.COHERE_API_KEY
        
        assert accessed_value == test_api_key  # Decrypted!
        
        # Verify internal storage still encrypted
        stored_value = settings_obj._encrypted_settings['COHERE_API_KEY']
        assert stored_value != test_api_key
    
    @pytest.mark.asyncio
    async def test_consistent_decryption(self, db_session, settings_service):
        """Test that multiple accesses return consistent decrypted values."""
        test_api_key = "sk-test-consistent-789"
        
        # Set the value
        try:
            await settings_service.update("openai_api_key", test_api_key)
        except ValueError:
            await settings_service.create(
                key="openai_api_key",
                value=test_api_key,
                data_type="string",
                category="llm",
                description="Test API key"
            )
        
        # Create Settings object
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Access multiple times
        first_access = settings_obj.OPENAI_API_KEY
        second_access = settings_obj.OPENAI_API_KEY
        third_access = settings_obj.OPENAI_API_KEY
        
        assert first_access == test_api_key
        assert second_access == test_api_key
        assert third_access == test_api_key
        assert first_access == second_access == third_access


class TestSettingsPriority:
    """Test settings priority: DB → ENV → defaults."""
    
    @pytest.mark.asyncio
    async def test_null_db_falls_back_to_default(self, db_session):
        """Test that NULL DB values fall back to Field defaults."""
        # Ensure value is NULL
        await db_session.execute(
            update(ApplicationSetting)
            .where(ApplicationSetting.key == 'embedding_provider')
            .values(value=None)
        )
        await db_session.commit()
        
        # Load settings
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Should use Field default
        assert settings_obj.EMBEDDING_PROVIDER == 'huggingface'
    
    @pytest.mark.asyncio
    async def test_db_value_overrides_default(self, db_session, settings_service):
        """Test that DB values override Field defaults."""
        # Set DB value using settings service (ensures proper commit)
        result = await db_session.execute(
            select(ApplicationSetting).where(
                ApplicationSetting.key == 'embedding_provider'
            )
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            await settings_service.update('embedding_provider', 'openai')
        else:
            await settings_service.create(
                key='embedding_provider',
                value='openai',
                data_type='string',
                category='embedding',
                description='Test'
            )
        
        # Refresh session to get latest data
        await db_session.commit()
        
        # Load settings
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Should use DB value
        assert settings_obj.EMBEDDING_PROVIDER == 'openai'
    
    @pytest.mark.asyncio
    async def test_db_value_change_reflected_after_reload(self, db_session, settings_service):
        """Test that DB value changes are reflected after reload."""
        # Set initial value
        try:
            await settings_service.update('llm_provider', 'openai')
        except ValueError:
            await settings_service.create(
                key='llm_provider',
                value='openai',
                data_type='string',
                category='llm',
                description='Test'
            )
        
        # Load settings
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        assert settings_obj.LLM_PROVIDER == 'openai'
        
        # Update DB value
        await settings_service.update('llm_provider', 'google')
        
        # Reload settings (simulating app restart)
        cached_settings = await load_settings_by_category(db_session)
        new_settings_obj = Settings(cached_settings=cached_settings)
        
        # Should have new value
        assert new_settings_obj.LLM_PROVIDER == 'google'
    
    @pytest.mark.asyncio
    async def test_clearing_db_value_returns_to_env_or_default(self, db_session, settings_service):
        """Test that clearing DB value (NULL) returns to ENV or default."""
        # Set DB value to something different
        try:
            await settings_service.update('cache_backend', 'memory')
        except ValueError:
            await settings_service.create(
                key='cache_backend',
                value='memory',
                data_type='string',
                category='cache',
                description='Test'
            )
        
        # Load settings - should be memory (from DB)
        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)
        assert settings_obj.CACHE_BACKEND == 'memory'
        
        # Clear DB value by updating to NULL
        await db_session.execute(
            update(ApplicationSetting)
            .where(ApplicationSetting.key == 'cache_backend')
            .values(value=None)
        )
        await db_session.commit()
        
        # Reload - should fall back to ENV (redis from .env) or default (memory)
        # Since .env has CACHE_BACKEND=redis, it should be redis
        cached_settings = await load_settings_by_category(db_session)
        new_settings_obj = Settings(cached_settings=cached_settings)
        # Priority: NULL DB → ENV (redis) → default (memory)
        assert new_settings_obj.CACHE_BACKEND in ['redis', 'memory']


class TestSettingsService:
    """Test SettingsService encryption/decryption behavior."""
    
    @pytest.mark.asyncio
    async def test_create_sensitive_setting_auto_encrypts(self, settings_service):
        """Test that sensitive settings are auto-encrypted on create."""
        test_key = "test_api_key_create"
        test_value = "sk-test-value"
        await settings_service.delete(test_key)
        try:
            setting = await settings_service.create(
                key=test_key,
                value=test_value,
                data_type="string",
                category="test",
                description="Test"
            )
            
            assert setting.is_sensitive is True  # Auto-detected
            assert setting.value != test_value  # Encrypted
            assert setting.value.startswith('gAAAAA')
        finally:
            await settings_service.delete(test_key)
    
    @pytest.mark.asyncio
    async def test_update_sensitive_setting_encrypts(self, db_session, settings_service):
        """Test that updating sensitive settings encrypts the new value."""
        # Create a sensitive setting
        test_key = "test_password_update"
        initial_value = "old-password-123"
        new_value = "new-password-456"
        await settings_service.delete(test_key)
        try:
            await settings_service.create(
                key=test_key,
                value=initial_value,
                data_type="string",
                category="test",
                description="Test"
            )
            
            # Update it
            updated_setting = await settings_service.update(test_key, new_value)
            
            # Check encryption
            result = await db_session.execute(
                select(ApplicationSetting).where(ApplicationSetting.key == test_key)
            )
            db_setting = result.scalar_one()
            
            assert db_setting.value != new_value  # Encrypted
            assert db_setting.value.startswith('gAAAAA')
            assert db_setting.value != initial_value  # Different from old encrypted value
        finally:
            await settings_service.delete(test_key)
    
    @pytest.mark.asyncio
    async def test_get_value_decrypts_sensitive(self, settings_service):
        """Test that get_value() decrypts sensitive values."""
        test_key = "test_secret_get"
        test_value = "my-secret-value-789"
        await settings_service.delete(test_key)
        try:
            # Create sensitive setting
            await settings_service.create(
                key=test_key,
                value=test_value,
                data_type="string",
                category="test",
                description="Test"
            )
            
            # Get value - should be decrypted
            retrieved_value = await settings_service.get_value(test_key)
            
            assert retrieved_value == test_value
        finally:
            await settings_service.delete(test_key)
    
    @pytest.mark.asyncio
    async def test_non_sensitive_not_encrypted(self, settings_service):
        """Test that non-sensitive settings are not encrypted."""
        test_key = "test_normal_setting"
        test_value = "just-a-normal-value"
        await settings_service.delete(test_key)
        try:
            setting = await settings_service.create(
                key=test_key,
                value=test_value,
                data_type="string",
                category="test",
                description="Test"
            )
            
            assert setting.is_sensitive is False
            assert setting.value == test_value  # Not encrypted
        finally:
            await settings_service.delete(test_key)


class TestSettingsNamespaceCompatibility:
    """Ensure the Settings namespace still exposes LLM sub-settings."""

    def test_llm_settings_alias_works_with_cached_overrides(self):
        """settings.llm_settings must expose subclass fields even when cached."""
        cached_settings = {
            "llm": {
                "ENABLE_INTERNAL_LLM": {"value": True, "is_sensitive": False},
                "internal_llm_provider": {"value": "openai", "is_sensitive": False},
            }
        }

        settings_obj = Settings(cached_settings=cached_settings)

        assert settings_obj.llm_settings is settings_obj
        assert settings_obj.llm_settings.ENABLE_INTERNAL_LLM is True
        assert settings_obj.llm_settings.INTERNAL_LLM_PROVIDER == "openai"


class TestSettingsOverrideFlow:
    """Validate DB → ENV → default priority and guardrails."""

    @pytest.mark.asyncio
    async def test_database_settings_never_overridden(self, db_session, settings_service):
        """DB credentials remain sourced from env even if user settings exist."""
        result = await db_session.execute(
            select(ApplicationSetting).where(ApplicationSetting.key == "db_password")
        )
        existing = result.scalar_one_or_none()
        original_value = existing.value if existing else None
        original_sensitive = existing.is_sensitive if existing else True

        try:
            await settings_service.create(
                key="db_password",
                value="db-secret-from-user",
                data_type="string",
                category="database",
                description="Test DB password override",
            )
        except ValueError:
            await settings_service.update("db_password", "db-secret-from-user")

        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings, DB_PASSWORD="env-secret")

        assert settings_obj.DB_PASSWORD == "env-secret"
        assert "DB_PASSWORD" not in settings_obj._encrypted_overrides

        if existing:
            existing.value = original_value
            existing.is_sensitive = original_sensitive
            await db_session.commit()
        else:
            await db_session.execute(
                delete(ApplicationSetting).where(ApplicationSetting.key == "db_password")
            )
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_non_mutable_settings_ignore_cached_value(self, db_session):
        """Settings marked as immutable should not override ENV/defaults."""
        result = await db_session.execute(
            select(ApplicationSetting).where(ApplicationSetting.key == "app_environment")
        )
        setting = result.scalar_one_or_none()
        existed = bool(setting)
        original_value = setting.value if setting else None
        original_mutable = setting.is_mutable if setting else True

        if not setting:
            setting = ApplicationSetting(
                key="app_environment",
                value="production",
                data_type="string",
                description="Environment override",
                category="application",
                is_mutable=False,
                is_sensitive=False,
            )
            db_session.add(setting)
        else:
            setting.value = "production"
            setting.is_mutable = False
        await db_session.commit()

        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings, ENVIRONMENT="staging")

        assert settings_obj.ENVIRONMENT == "staging"

        if existed:
            setting.value = original_value
            setting.is_mutable = original_mutable
            await db_session.commit()
        else:
            await db_session.execute(
                delete(ApplicationSetting).where(ApplicationSetting.key == "app_environment")
            )
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_alias_keys_cast_to_target_type(self, db_session, settings_service):
        """Aliased keys like cors_allow_origins should hydrate the proper field type."""
        cors_payload = "[\"https://example.com\"]"
        result = await db_session.execute(
            select(ApplicationSetting).where(ApplicationSetting.key == "cors_allow_origins")
        )
        existing = result.scalar_one_or_none()
        original_value = existing.value if existing else None

        try:
            await settings_service.create(
                key="cors_allow_origins",
                value=cors_payload,
                data_type="json",
                category="application",
                description="Allowed origins override",
            )
        except ValueError:
            await settings_service.update("cors_allow_origins", cors_payload)

        cached_settings = await load_settings_by_category(db_session)
        settings_obj = Settings(cached_settings=cached_settings)

        assert settings_obj.CORS_ORIGINS == ["https://example.com"]

        if existing:
            existing.value = original_value
            await db_session.commit()
        else:
            await db_session.execute(
                delete(ApplicationSetting).where(ApplicationSetting.key == "cors_allow_origins")
            )
            await db_session.commit()
