# RAG Fortress — Initial Backlog

## Core Setup
- [ ] Initialize FastAPI backend and folder structure.
- [ ] Add README with basic architecture diagram.
- [ ] Connect frontend (Vue or React) scaffold.
- [ ] Integrate simple environment config (`.env`).

## Document Security & Authorization
- [ ] Implement user model with `security_level`.
- [ ] Build admin upload endpoint with metadata (title, source, level).
- [ ] Restrict query access based on security level.
- [ ] Add audit logs (lightweight JSON or SQLite).

## Retrieval and Storage
- [ ] Integrate Qdrant for vector storage (local Docker or HF Spaces).
- [ ] Embedding pipeline using open model (`sentence-transformers/all-MiniLM-L6-v2`).
- [ ] Versioning: replace old datapoints with updated content.
- [ ] Caching (in-memory LRU per session).
- [ ] Reranking pipeline using cross-encoder or hybrid search.

## Frontend
- [ ] Public query interface (guest-level).
- [ ] Authenticated interface (user-level).
- [ ] Admin dashboard for doc uploads and version control.
- [ ] Loading indicator and error UI.

## Deployment
- [ ] Deploy full app on Hugging Face Spaces.
- [ ] Document environment variables and Space setup.

## Documentation
- [ ] System diagram (RAG + auth + caching).
- [ ] Example prompts for testing.
- [ ] Architecture README update.
