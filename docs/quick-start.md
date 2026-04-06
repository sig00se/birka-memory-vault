# Quick Start Guide for Birka Memory Vault

## Setup (5 minutes)

```bash
git clone git@github.com:sig00se/birka-memory-vault.git
cd birka-memory-vault
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
alembic upgrade head
python3 examples/basic_indexing.py
```

## The One-Sentence Concept

The Vault is an index layer over plain Markdown memories — it doesn't store content, it stores structure (what each memory is, who owns it, what it links to, when it was created or merged).

---

## How It Works

### Write to the Vault

Every time an OpenClaw agent creates a meaningful memory (decision, fact, lesson), it also writes a structured row:

```python
from birka_memory_vault.events import MemoryEventManager
from birka_memory_vault.schemas import MemoryEntryCreate

entry = await mgr.add_memory_entry(MemoryEntryCreate(
    type="task",
    title="Fix Lithuanian humanizer pipeline",
    content="Use self-improving loop instead of rule engine",
    tags=["lithuanian", "pipeline"],
    source_file="memory/2026-04-06.md"
))
```

### Query the Vault

Ask structured questions you can't easily answer with text files:

```bash
python3 -c "from birka_memory_vault.database import AsyncSessionLocal;
... # query code"
```

### Evolve the Schema

Add a new migration:

```bash
alembic revision --autogenerate -m "Add user_preferences column to memory_entry"
alembic upgrade head
```

---

## What's Inside

- `birka_memory_vault/` — Python package with models, schemas, and event handlers
- `alembic/` — versioned database migrations
- `examples/` — working code samples
- `docs/` — deep architecture docs

---

That's it. Clone, install, migrate, import. The Vault is ready to be integrated into any OpenClaw agent.
