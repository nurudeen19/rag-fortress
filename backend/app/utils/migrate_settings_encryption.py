"""
Migration utility to re-encrypt existing settings from legacy SETTINGS_ENCRYPTION_KEY 
to new HKDF-based master key derivation.

This script migrates sensitive settings to use versioned encryption with the master key.

Usage:
    # Dry run (preview changes)
    python -m app.utils.migrate_settings_encryption --dry-run
    
    # Execute migration
    python -m app.utils.migrate_settings_encryption
"""

import asyncio
from sqlalchemy import select

from app.core.database import get_async_session_factory
from app.models.application_setting import ApplicationSetting
from app.utils.encryption import encrypt_settings_value, decrypt_value
from app.core import get_logger

logger = get_logger(__name__)


async def is_new_format(encrypted_value: str) -> bool:
    """
    Check if value is already in new versioned format.
    
    Args:
        encrypted_value: The encrypted string to check
        
    Returns:
        True if already in new format (has version prefix like "v1:")
    """
    if not encrypted_value or not isinstance(encrypted_value, str):
        return False
    
    # New format has version prefix
    if ":" in encrypted_value:
        version_part = encrypted_value.split(":", 1)[0]
        return version_part.startswith("v") and version_part[1:].isdigit()
    
    return False


async def migrate_settings(dry_run: bool = False):
    """
    Migrate sensitive settings to new HKDF-based encryption.
    
    Args:
        dry_run: If True, only show what would be migrated without making changes
    """
    session_factory = get_async_session_factory()
    
    async with session_factory() as session:
        try:
            # Get all sensitive settings
            stmt = select(ApplicationSetting).where(ApplicationSetting.is_sensitive == True)
            result = await session.execute(stmt)
            settings = result.scalars().all()
            
            total_count = len(settings)
            migrated_count = 0
            already_new_count = 0
            failed_count = 0
            
            logger.info(f"Found {total_count} sensitive settings to check")
            
            for setting in settings:
                try:
                    if not setting.value:
                        logger.debug(f"Skipping setting '{setting.key}' (no value)")
                        continue
                    
                    # Check if already in new format
                    if await is_new_format(setting.value):
                        already_new_count += 1
                        logger.debug(f"Setting '{setting.key}' already in new format")
                        continue
                    
                    # Decrypt with legacy format
                    try:
                        decrypted = decrypt_value(setting.value)
                    except Exception as e:
                        logger.error(
                            f"Failed to decrypt setting '{setting.key}': {type(e).__name__}: {str(e)}. "
                            f"Skipping this setting.",
                            exc_info=True
                        )
                        failed_count += 1
                        continue
                    
                    # Re-encrypt with new HKDF format
                    new_encrypted = encrypt_settings_value(decrypted, version=1)
                    
                    if dry_run:
                        logger.info(
                            f"[DRY RUN] Would migrate setting '{setting.key}' "
                            f"(old: {len(setting.value)} chars, new: {len(new_encrypted)} chars)"
                        )
                    else:
                        setting.value = new_encrypted
                        logger.info(f"Migrated setting '{setting.key}' to new HKDF format")
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(
                        f"Failed to process setting '{setting.key}': {type(e).__name__}: {str(e)}",
                        exc_info=True
                    )
                    failed_count += 1
                    continue
            
            if not dry_run and migrated_count > 0:
                await session.commit()
                logger.info("Committed all setting migrations to database")
            
            # Summary
            logger.info("=" * 60)
            logger.info("Settings Encryption Migration Summary")
            logger.info("=" * 60)
            logger.info(f"Total sensitive settings: {total_count}")
            logger.info(f"Already in new format: {already_new_count}")
            logger.info(f"{'Would migrate' if dry_run else 'Migrated'}: {migrated_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info("=" * 60)
            
            if dry_run and migrated_count > 0:
                logger.info("This was a DRY RUN. No changes were made.")
                logger.info("Run without --dry-run flag to execute migration.")
            
        except Exception as e:
            logger.error(f"Settings migration failed: {type(e).__name__}: {str(e)}", exc_info=True)
            await session.rollback()
            raise


async def verify_encryption():
    """
    Verify all sensitive settings are properly encrypted with new format.
    
    Returns:
        True if all sensitive settings use new format, False otherwise
    """
    session_factory = get_async_session_factory()
    
    async with session_factory() as session:
        try:
            # Get all sensitive settings
            stmt = select(ApplicationSetting).where(ApplicationSetting.is_sensitive == True)
            result = await session.execute(stmt)
            settings = result.scalars().all()
            
            total_count = len(settings)
            new_format_count = 0
            legacy_format_count = 0
            
            for setting in settings:
                if not setting.value:
                    continue
                
                if await is_new_format(setting.value):
                    new_format_count += 1
                else:
                    legacy_format_count += 1
                    logger.warning(f"Setting '{setting.key}' still in legacy format")
            
            logger.info("=" * 60)
            logger.info("Settings Encryption Verification")
            logger.info("=" * 60)
            logger.info(f"Total sensitive settings: {total_count}")
            logger.info(f"New HKDF format: {new_format_count}")
            logger.info(f"Legacy format: {legacy_format_count}")
            logger.info("=" * 60)
            
            if legacy_format_count == 0:
                logger.info("✓ All sensitive settings are using new HKDF encryption format!")
                return True
            else:
                logger.warning(
                    f"✗ {legacy_format_count} settings still using legacy encryption. "
                    f"Run migration to update."
                )
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {type(e).__name__}: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    import sys
    
    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    verify_only = "--verify" in sys.argv
    
    if verify_only:
        asyncio.run(verify_encryption())
    else:
        asyncio.run(migrate_settings(dry_run=dry_run))
