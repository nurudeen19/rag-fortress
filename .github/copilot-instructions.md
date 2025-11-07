# 🧭 Copilot Instructions for `rag-fortress`

This document defines how GitHub Copilot (and other AI coding assistants) should behave when generating or completing code for the **RAG-Fortress** project.

---

## 🧱 Core Development Philosophy

- **Keep it simple, readable, and modular.**
- **Prefer clarity over cleverness.**
- **Favor proven libraries over custom abstractions.**
- **Respect LangChain conventions — don’t reinvent what already exists.**

Copilot’s primary goal in this repository is to *assist* the developer, not to *outsmart* the design.

---

## 🧩 Framework & Libraries

RAG-Fortress uses the following as core dependencies:

- **LangChain** → chaining, retrieval, RAG pipelines  
- **Hugging Face (Transformers)** → local models and embeddings  
- **Vector DBs:** Chroma, Qdrant, Pinecone, Weaviate (plug-in support)  
- **LLM Providers:** OpenAI, Google, Hugging Face, Cohere, others as configured  
- **FastAPI** → backend service and API endpoints  
- **Pydantic** → request/response schemas and configuration models  
- **SQLAlchemy** → metadata, configs, and access control persistence layer

Copilot should **always try to use LangChain or these preferred tools first**, instead of writing low-level logic from scratch.

---

## 💡 General Guidelines

1. **Keep code human-readable.**  
   - Write explicit variable names, avoid nested logic and unnecessary abstraction.  
   - Do not over-engineer small tasks (e.g., chunking, retrieval, or prompt creation).

2. **Use LangChain for LLM, retrieval, and chain logic.**  
   - ✅ Use `langchain.llms`, `langchain.embeddings`, `langchain.vectorstores`.  
   - ✅ Use `RetrievalQA`, `ConversationalRetrievalChain`, or `RunnableSequence`.  
   - ❌ Do not manually build tokenizers, attention windows, or RAG pipelines unless required.

3. **Prioritize performance through simplicity.**  
   - Favor fewer moving parts and lightweight operations.  
   - Avoid repeatedly reloading models or embeddings; use caching or reuse chains.

4. **Prefer existing integrations.**  
   - If LangChain already provides a wrapper for a provider (e.g., Qdrant, Pinecone), use it.  
   - Only build custom logic if there’s a functional gap **and** check online docs first.

5. **Respect configuration-driven design.**  
   - Use the configuration layer (YAML, `.env`, or `config.py`) instead of hardcoding values.  
   - Do not embed API keys, model names, or paths directly in code.

6. **Error handling > silent failure.**  
   - Use clear exceptions or FastAPI HTTP errors when something fails.  
   - Log failures with enough context for debugging (no generic “something went wrong”).

7. **Write modular, testable functions.**  
   - Each function should do one thing well and be easily unit-tested.  
   - Avoid large monolithic functions that mix concerns.

---

## 🧠 Behavior Expectations for Copilot

- ✅ **Ask itself:** “Does LangChain already have this?” before implementing.  
- ✅ **Reference LangChain, FastAPI, and HF documentation** when unsure.  
- ✅ **Follow RAG best practices:** chunk documents efficiently, cache embeddings, reuse retrievers.  
- ✅ **Keep inference lightweight:** load models once and reuse pipelines.  
- ✅ **Generate composable utilities:** each function should do one thing well.

- ❌ **Do not create unnecessary frameworks or abstractions.**  
- ❌ **Do not build deep class hierarchies** where a single function is sufficient.  
- ❌ **Do not use experimental or obscure libraries** unless justified and documented.  
- ❌ **Do not assume GPU-heavy inference** — performance and portability come first.

---

## ⚙️ Example Expectations

**Bad:**
```python
# Overengineered retrieval logic
retriever = CustomRetrieverWithTokenMergingAndSemanticCache(model, db)
```

**Good:**
```python
# Use LangChain’s built-in retriever
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)
```

---

## 🧩 Code Style & Structure

- **Backend modules:**  
  - `app/config` – App options and settings  
  - `app/models` – SQLAlchemy models 
  - `app/core` – Config, security, logging  
  - `app/services` – Business logic and service layer   
  - `app/utils` – Common helpers 
  - `app/jobs` – Background tasks and schedulers
  - `app/routes` – FastAPI route definitions
  - `app/schemas` – Pydantic request/response models
  - `app/handlers` – Event handlers
  - `app/middlewares` – Custom FastAPI middlewares
  - `app/main.py` – Application entrypoint

- Use **type hints** everywhere.  
- Stick to **black** and **ruff** style formatting.  
- Maintain a **consistent docstring style** (Google or NumPy format).

---

## 🧩 If Copilot Is Unsure

If Copilot isn’t certain about a specific implementation:  
1. It should **look up recent LangChain documentation** for the feature.  
2. It should **suggest a minimal placeholder** (e.g., `# TODO: Implement using langchain retriever`)  
3. It should **avoid hallucinating** complex or unverified code.

---

## 🧠 Final Reminder

> RAG-Fortress is not about showing technical complexity.  
> It’s about **building a clear, modular, and maintainable RAG system** that’s easy to extend and deploy securely.

Simplicity, consistency, and correctness come first.
