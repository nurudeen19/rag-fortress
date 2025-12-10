# RAG Fortress Documentation

Complete documentation for RAG Fortress - Enterprise-grade RAG platform with role-based access control and multi-provider support.

## 📖 Table of Contents

### Getting Started
- [Installation Guide](installation-guide.md) - Setup, dependencies, and first-time configuration
- [Quick Start: Ingestion](quick-start-ingestion.md) - Upload and process your first documents

### Core Guides

#### Configuration & Settings
- [Settings Guide](SETTINGS_GUIDE.md) - Complete configuration reference (covers application, LLMs, embeddings, vector DBs, databases, prompts, email, cache, demo mode, and seeder control)

- [Fallback LLM Guide](FALLBACK_LLM_GUIDE.md) - Automatic failover configuration

#### Document Management
- [Document Management Guide](DOCUMENT_MANAGEMENT_GUIDE.md) - Complete document lifecycle
  - File upload system
  - Processing pipeline (Load → Chunk → Embed → Store)
  - File status tracking
  - Department-based access control
  - Security levels and metadata
  - Reprocessing and error handling

- [Structured Data Filtering](structured-data-filtering.md) - Filter JSON/CSV/XLSX fields during ingestion

#### Retrieval & Search
- [Retrieval Guide](RETRIEVAL_GUIDE.md) - Document retrieval system
  - Adaptive retrieval with quality scoring
  - Reranking system (cross-encoder)
  - Security-aware caching
  - Fallback strategies
  - Service architecture

- [Reranker Implementation](RERANKER_IMPLEMENTATION.md) - Cross-encoder reranking details

- [Intent Classifier Guide](INTENT_CLASSIFIER_GUIDE.md) - Smart query routing system
  - Rule-based intent classification
  - Template responses for pleasantries
  - Confidence scoring and thresholds
  - Performance optimization
  - Pattern customization

#### Vector Stores & Embeddings
- [Vector Stores Guide](VECTOR_STORES_GUIDE.md) - Vector databases and embeddings
  - Embedding providers comparison
  - Vector database comparison
  - Provider selection guide
  - Metadata filtering
  - Migration between providers

#### Access Control & Security
- [Permissions Guide](PERMISSIONS_GUIDE.md) - Complete RBAC system
  - Role-based access control
  - Security clearance levels
  - Permission overrides with automatic expiry
  - Permission override request workflow
  - Approval authority matrix
  - Audit trails

### System Operations

#### Database
- [Migrations Guide](MIGRATIONS_GUIDE.md) - Database migrations
  - Alembic setup
  - Creating migrations
  - Running migrations
  - Multi-provider compatibility (PostgreSQL, MySQL, SQLite)
  - Provider-agnostic patterns

- [Seeders Guide](SEEDERS_GUIDE.md) - Database seeding
  - Idempotent seeding strategy
  - Configuration options
  - Available seeders
  - Adding new seeders

- [Installation Guide](installation-guide.md) - Includes `uv` package manager usage and seeder execution examples

#### Background Jobs
- [Jobs Guide](JOBS_GUIDE.md) - Background task management
  - APScheduler integration
  - Database job queue
  - Job status tracking
  - Automatic retry logic
  - Recovery after restart

#### Logging & Monitoring
- [Logging Guide](LOGGING_GUIDE.md) - Application logging
  - Colored console output
  - Rotating file logs
  - Environment-aware formats
  - Log levels
  - Common patterns

#### Error Handling
- [Exception Handling Guide](EXCEPTION_HANDLING_GUIDE.md) - Error handling
  - Custom exception hierarchy
  - HTTP status code mappings
  - Structured error responses
  - Best practices

#### Caching
- [Caching Guide](CACHING_GUIDE.md) - Query result caching
  - Redis backend
  - In-memory backend
  - Cache-aside pattern
  - TTL configuration
  - Invalidation strategies

#### Email & Notifications
- [Email System](EMAIL_SYSTEM.md) - Email notifications
  - fastapi-mail integration
  - Email types (activation, invitations, etc.)
  - SMTP configuration
  - HTML templates

## 🎯 Quick Reference by Use Case

### I want to...

**Set up the application**
1. [Installation Guide](installation-guide.md)
2. [Settings Guide](SETTINGS_GUIDE.md)
3. Run `python setup.py`

**Configure providers**
- LLMs: [Settings Guide](SETTINGS_GUIDE.md#llmsettings)
- Embeddings: [Vector Stores Guide](VECTOR_STORES_GUIDE.md#embedding-providers)
- Vector DBs: [Vector Stores Guide](VECTOR_STORES_GUIDE.md#vector-databases)
- Databases: [Settings Guide](SETTINGS_GUIDE.md#databasesettings)

**Upload and process documents**
1. [Document Management Guide](DOCUMENT_MANAGEMENT_GUIDE.md)
2. [Structured Data Filtering](structured-data-filtering.md) - For JSON/CSV/XLSX

**Improve search quality**
1. [Retrieval Guide](RETRIEVAL_GUIDE.md)
2. [Reranker Implementation](RERANKER_IMPLEMENTATION.md)

**Manage permissions**
1. [Permissions Guide](PERMISSIONS_GUIDE.md)
2. Configure security levels and department access

**Run database migrations**
1. [Migrations Guide](MIGRATIONS_GUIDE.md)
2. Run `alembic upgrade head`

**Seed the database**
1. [Seeders Guide](SEEDERS_GUIDE.md)
2. Run `python setup.py`

**Handle background jobs**
1. [Jobs Guide](JOBS_GUIDE.md)
2. Use APScheduler for immediate/scheduled tasks

**Debug issues**
- [Logging Guide](LOGGING_GUIDE.md) - Check logs
- [Exception Handling Guide](EXCEPTION_HANDLING_GUIDE.md) - Understand errors

**Enable caching**
1. [Caching Guide](CACHING_GUIDE.md)
2. Set `ENABLE_CACHING=True`

**Send emails**
1. [Email System](EMAIL_SYSTEM.md)
2. Configure SMTP settings

## 📚 Documentation Organization

### By Topic

**Configuration**
- Settings Guide
- Fallback LLM Guide
- Vector Stores Guide

**Development**
- Installation Guide
- Exception Handling Guide
- Logging Guide
- Migrations Guide
- Seeders Guide

**Features**
- Document Management Guide
- Permissions Guide
- Retrieval Guide
- Caching Guide
- Email System
- Structured Data Filtering

**Operations**
- Jobs Guide
- Reranker Implementation

### By Role

**System Administrator**
- Installation Guide
- Settings Guide
- Migrations Guide
- Seeders Guide
- Jobs Guide

**Developer**
- All guides (comprehensive reference)
- Exception Handling Guide
- Logging Guide
- Caching Guide

**Data Administrator**
- Document Management Guide
- Structured Data Filtering
- Retrieval Guide

**Security Administrator**
- Permissions Guide
- Settings Guide (security section)

## 🔗 External Resources

- **Main README**: `../../README.md` - Project overview
- **Frontend Docs**: `../../frontend/docs/` - Vue.js documentation
- **Root Docs**: `../../docs/` - RBAC and Multi-Tier Invitation docs
- **API Docs**: `http://localhost:8000/docs` (Swagger)
- **ReDoc**: `http://localhost:8000/redoc`

## 📝 Documentation Standards

All documentation follows these standards:
- **Concise**: No verbose explanations
- **Practical**: Code examples and commands
- **Up-to-date**: Reflects current implementation
- **Comprehensive**: Covers common use cases
- **Well-organized**: Clear sections and navigation

## 🤝 Contributing to Docs

When updating documentation:
1. Keep it concise and practical
2. Include working code examples
3. Update the index if adding new files
4. Cross-reference related guides
5. Test all commands and examples

## 📞 Need Help?

- Check the relevant guide above
- Search documentation using Ctrl+F
- Check API docs at `/docs` endpoint
- Review code examples in guides

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Status**: Production Ready
