"""
Migration utility to encrypt existing unencrypted conversation messages.

This script is for one-time migration of legacy unencrypted messages
to the new encrypted format with version prefixes.

Usage:
    python -m app.utils.migrate_message_encryption
"""

import asyncio
from sqlalchemy import select, text

from app.core.database import get_session
from app.models.message import Message
from app.utils.encryption import encrypt_conversation_message
from app.core import get_logger

logger = get_logger(__name__)


async def is_encrypted(content: str) -> bool:
    """
    Check if message content is already encrypted.
    
    Encrypted messages have version prefix: "v1:gAAAAAB..."
    """
    return content.startswith("v") and ":" in content and content.split(":", 1)[0].startswith("v")


async def migrate_messages(batch_size: int = 100, dry_run: bool = False):
    """
    Migrate unencrypted messages to encrypted format.
    
    Args:
        batch_size: Number of messages to process per batch
        dry_run: If True, only report what would be done without making changes
    """
    total_messages = 0
    encrypted_count = 0
    already_encrypted = 0
    failed_count = 0
    
    async for session in get_session():
        try:
            # Count total messages
            result = await session.execute(select(Message))
            all_messages = result.scalars().all()
            total_messages = len(all_messages)
            
            logger.info(f"Found {total_messages} total messages")
            
            # Process in batches
            for i in range(0, total_messages, batch_size):
                batch = all_messages[i:i + batch_size]
                
                for message in batch:
                    # Access _content directly to get raw DB value
                    raw_content = message._content
                    
                    # Check if already encrypted
                    if await is_encrypted(raw_content):
                        already_encrypted += 1
                        logger.debug(f"Message {message.id} already encrypted, skipping")
                        continue
                    
                    try:
                        if dry_run:
                            logger.info(f"[DRY RUN] Would encrypt message {message.id}")
                            encrypted_count += 1
                        else:
                            # Encrypt the plaintext content
                            encrypted = encrypt_conversation_message(raw_content, version=1)
                            
                            # Update directly in database to bypass property setter
                            await session.execute(
                                text("UPDATE messages SET content = :content WHERE id = :id"),
                                {"content": encrypted, "id": message.id}
                            )
                            
                            encrypted_count += 1
                            logger.info(f"Encrypted message {message.id}")
                    
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Failed to encrypt message {message.id}: {e}")
                
                # Commit batch
                if not dry_run:
                    await session.commit()
                    logger.info(f"Committed batch {i // batch_size + 1}")
            
            # Summary
            logger.info("=" * 60)
            logger.info("Migration Summary:")
            logger.info(f"  Total messages: {total_messages}")
            logger.info(f"  Already encrypted: {already_encrypted}")
            logger.info(f"  Newly encrypted: {encrypted_count}")
            logger.info(f"  Failed: {failed_count}")
            logger.info("=" * 60)
            
            if dry_run:
                logger.info("DRY RUN complete - no changes made to database")
            else:
                logger.info("Migration complete!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if not dry_run:
                await session.rollback()
            raise
        finally:
            await session.close()


async def verify_encryption():
    """
    Verify that all messages are properly encrypted.
    
    Returns count of unencrypted messages (should be 0 after migration).
    """
    unencrypted_count = 0
    
    async for session in get_session():
        try:
            result = await session.execute(select(Message))
            messages = result.scalars().all()
            
            for message in messages:
                raw_content = message._content
                if not await is_encrypted(raw_content):
                    unencrypted_count += 1
                    logger.warning(f"Message {message.id} is NOT encrypted!")
            
            logger.info(f"Verification complete: {unencrypted_count} unencrypted messages found")
            return unencrypted_count
            
        finally:
            await session.close()


if __name__ == "__main__":
    import sys
    
    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        logger.info("Running in DRY RUN mode - no changes will be made")
    
    # Run migration
    asyncio.run(migrate_messages(dry_run=dry_run))
    
    # Verify if not dry run
    if not dry_run:
        unencrypted = asyncio.run(verify_encryption())
        if unencrypted == 0:
            logger.info("✓ All messages are encrypted!")
        else:
            logger.error(f"✗ {unencrypted} messages are still unencrypted")
            sys.exit(1)
