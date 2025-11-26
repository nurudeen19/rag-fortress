"""
Test script to verify that sensitive keys remain encrypted in cache/memory
and are only decrypted when accessed (lazy decryption).

SECURITY TEST: Ensures API keys don't sit in plain text in Redis/memory.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_encryption_security():
    """Test that sensitive values are encrypted everywhere except on access."""
    
    print("=" * 80)
    print("ENCRYPTION SECURITY TEST")
    print("=" * 80)
    
    from app.core.database import DatabaseManager
    from app.config.database_settings import DatabaseSettings
    from app.models.application_setting import ApplicationSetting
    from app.core.settings_loader import load_settings_by_category
    from app.config.settings import Settings
    from app.services.settings_service import SettingsService
    from sqlalchemy import select, update
    
    # Initialize DB
    db_settings = DatabaseSettings()
    db_manager = DatabaseManager(db_settings)
    await db_manager.create_async_engine()
    async_session_factory = db_manager.get_session_factory()
    
    # ===== STEP 1: Set a test API key =====
    print("\n📝 STEP 1: Setting test API key in database")
    print("-" * 80)
    
    test_api_key = "sk-test-secret-key-12345"
    
    async with async_session_factory() as session:
        settings_service = SettingsService(session)
        
        # Update openai_api_key
        try:
            await settings_service.update("openai_api_key", test_api_key)
            print(f"✓ Set openai_api_key = '{test_api_key}'")
        except ValueError:
            # Might not exist, create it
            await settings_service.create(
                key="openai_api_key",
                value=test_api_key,
                data_type="string",
                category="llm",
                description="Test API key"
            )
            print(f"✓ Created openai_api_key = '{test_api_key}'")
    
    # ===== STEP 2: Check DB storage (should be encrypted) =====
    print("\n🔒 STEP 2: Verify DB storage is ENCRYPTED")
    print("-" * 80)
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(ApplicationSetting).where(
                ApplicationSetting.key == 'openai_api_key'
            )
        )
        setting = result.scalar_one()
        
        print(f"Database value: {setting.value[:50]}...")
        print(f"Is sensitive: {setting.is_sensitive}")
        print(f"Is encrypted: {setting.value != test_api_key}")
        
        encrypted_in_db = setting.value != test_api_key
        print(f"\n{'✅' if encrypted_in_db else '❌'} TEST 1: Value encrypted in database")
    
    # ===== STEP 3: Check cached settings (should be encrypted) =====
    print("\n🔒 STEP 3: Verify cached settings are ENCRYPTED")
    print("-" * 80)
    
    async with async_session_factory() as session:
        cached_settings = await load_settings_by_category(session)
        
        if 'llm' in cached_settings and 'openai_api_key' in cached_settings['llm']:
            cached_data = cached_settings['llm']['openai_api_key']
            
            print(f"Cached data structure: {type(cached_data)}")
            print(f"Cached value: {cached_data.get('value', '')[:50]}...")
            print(f"Is sensitive flag: {cached_data.get('is_sensitive', False)}")
            
            cached_value = cached_data.get('value', '')
            encrypted_in_cache = cached_value != test_api_key
            
            print(f"\n{'✅' if encrypted_in_cache else '❌'} TEST 2: Value encrypted in cache")
        else:
            print("❌ openai_api_key not found in cached settings")
            encrypted_in_cache = False
    
    # ===== STEP 4: Check Settings object internal storage =====
    print("\n🔒 STEP 4: Verify Settings object stores values ENCRYPTED")
    print("-" * 80)
    
    async with async_session_factory() as session:
        cached_settings = await load_settings_by_category(session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Check internal _encrypted_settings
        if hasattr(settings_obj, '_encrypted_settings'):
            encrypted_dict = settings_obj._encrypted_settings
            
            if 'OPENAI_API_KEY' in encrypted_dict:
                stored_value = encrypted_dict['OPENAI_API_KEY']
                print(f"Stored in _encrypted_settings: {stored_value[:50]}...")
                
                encrypted_in_memory = stored_value != test_api_key
                print(f"\n{'✅' if encrypted_in_memory else '❌'} TEST 3: Value encrypted in Settings object")
            else:
                print("❌ OPENAI_API_KEY not in _encrypted_settings")
                encrypted_in_memory = False
        else:
            print("❌ _encrypted_settings attribute not found")
            encrypted_in_memory = False
    
    # ===== STEP 5: Access value (should be decrypted) =====
    print("\n🔓 STEP 5: Access value via settings.OPENAI_API_KEY (should decrypt)")
    print("-" * 80)
    
    async with async_session_factory() as session:
        cached_settings = await load_settings_by_category(session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        # Access the API key - should trigger decryption
        accessed_value = settings_obj.OPENAI_API_KEY
        
        print(f"Accessed value: {accessed_value}")
        print(f"Matches original: {accessed_value == test_api_key}")
        
        decrypted_on_access = accessed_value == test_api_key
        print(f"\n{'✅' if decrypted_on_access else '❌'} TEST 4: Value decrypted on access")
    
    # ===== STEP 6: Verify decryption works in app usage =====
    print("\n🔓 STEP 6: Verify decryption works in application usage")
    print("-" * 80)
    
    async with async_session_factory() as session:
        # Load settings with our encrypted test key
        cached_settings = await load_settings_by_category(session)
        settings_obj = Settings(cached_settings=cached_settings)
        
        try:
            # Test 1: Direct access decrypts
            api_key_direct = settings_obj.OPENAI_API_KEY
            print(f"Direct access (settings.OPENAI_API_KEY): {api_key_direct}")
            print(f"✓ Matches test key: {api_key_direct == test_api_key}")
            
            # Test 2: Multiple accesses return same decrypted value
            api_key_second = settings_obj.OPENAI_API_KEY
            print(f"\nSecond access: {api_key_second}")
            print(f"✓ Consistent: {api_key_direct == api_key_second}")
            
            # Test 3: Check internal storage still encrypted
            encrypted_val = settings_obj._encrypted_settings.get('OPENAI_API_KEY', '')
            print(f"\nInternal _encrypted_settings value: {encrypted_val[:50]}...")
            print(f"✓ Still encrypted internally: {encrypted_val != test_api_key}")
            
            config_correct = (api_key_direct == test_api_key and 
                            api_key_direct == api_key_second and
                            encrypted_val != test_api_key)
            
            print(f"\n{'✅' if config_correct else '❌'} TEST 5: Lazy decryption works correctly")
        except Exception as e:
            print(f"❌ Failed verification: {e}")
            import traceback
            traceback.print_exc()
            config_correct = False
    
    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("SECURITY TEST SUMMARY")
    print("=" * 80)
    
    all_pass = (encrypted_in_db and encrypted_in_cache and 
                encrypted_in_memory and decrypted_on_access and config_correct)
    
    print(f"\n{'✅' if encrypted_in_db else '❌'} Database stores encrypted")
    print(f"{'✅' if encrypted_in_cache else '❌'} Cache stores encrypted")
    print(f"{'✅' if encrypted_in_memory else '❌'} Memory stores encrypted")
    print(f"{'✅' if decrypted_on_access else '❌'} Decrypts on access")
    print(f"{'✅' if config_correct else '❌'} Works in application code")
    
    if all_pass:
        print("\n" + "=" * 80)
        print("🎉 ALL SECURITY TESTS PASSED!")
        print("=" * 80)
        print("\n✅ API keys are SECURE:")
        print("  • Encrypted in PostgreSQL database")
        print("  • Encrypted in Redis cache")
        print("  • Encrypted in application memory")
        print("  • Decrypted ONLY when accessed (in-process)")
        print("  • No plain text keys stored anywhere")
        print("\n🔒 Attack scenarios mitigated:")
        print("  • Redis dump/backup stolen → Keys encrypted")
        print("  • Memory dump → Keys encrypted until accessed")
        print("  • DB backup stolen → Keys encrypted")
        print("  • Only process memory during access has plain text (unavoidable)")
    else:
        print("\n❌ SECURITY ISSUES DETECTED - Check implementation!")
    
    print("=" * 80)
    
    await db_manager.async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_encryption_security())
