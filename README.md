# Birka Memory Vault

Persistent, structured memory for LLM agents.

SQLAlchemy 2.0 + SQLite/PostgreSQL memory layer that gives autonomous agents queryable long-term memory across sessions. No embeddings. No RAG. No vector databases.

Built March 2026 — before Karpathy's LLM knowledge base paper, this solved the stateless session problem.

---

## The Problem

LLM agents are stateless. Every session restart = memory gone.
You can't ask "what did the agent decide last week?" or "which tasks failed?" without parsing raw logs.

---

## Core Idea

Keep raw Markdown as the source of truth. Add a **parallel structured index** that remembers relationships, tags, lineages, and audit trails. The Vault doesn't store content — it stores *structure* about the content. Dual-write, never replace.

---

## Why This Exists

- **Queryable agent memory** — find all decisions, tasks, artifacts by project, date, or type
- **Graph relationships** — see which agent produced which artifact, which mission spawned which memory, dependency chains
- **Compaction trace** — track how daily logs were merged into curated summaries (full lineage)
- **Capability orchestration** — know which Birka instance can run which tools; route work accordingly
- **State persistence across restarts** — solves the core LLM agent statelessness problem without retraining

This is **agentic memory management** for production autonomous systems.

---

## Schema (at a glance)

Three foundation tables + nine orchestrator tables:

- **memory_entry** — indexed memories with tags, source file, created_at
- **compaction_index** — which raw entries merged into which curated memory
- **snapshot_index** — periodic memory state checkpoints (hash + entry list)

- **nodes** — universal typed entities (agent, mission, artifact, memory, context, file, user)
- **edges** — typed relations (SPAWNED_BY, PRODUCES, REFERENCES, CONTAINS, DERIVED_FROM, BLOCKS, DEPENDS_ON)
- **missions** — dispatched work units (status, priority, result, error, token count)
- **birka_fleet** — all running agent instances (model, capabilities, heartbeats, spawn depth)
- **spawn_tree** — full delegation tree with depth limits
- **resource_manifest** — declared capabilities parsed from TOOLS.md/SOUL.md
- **control_commands** — signed commands (PAUSE, KILL, OVERRIDE_MODEL, DRAIN, SYNC)
- **safeguard_events** — circuit breaker events (loops, cost ceiling, timeout, error rate)
- **events** — append-only audit log (spawn, dispatch, command, safeguard, state_change, error, metric)

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

Default database: SQLite (`sqlite+aiosqlite:///./birka_memory.db`). For production, set `DATABASE_URL` to PostgreSQL (`postgresql+asyncpg://...`).

---

## Integration

```python
from sqlalchemy.ext.asyncio import async_sessionmaker
from birka_memory_vault.database import AsyncSessionLocal, init_db
from birka_memory_vault.events import MemoryEventManager
from birka_memory_vault.schemas import MemoryEntryCreate, NodeCreate, EdgeCreate
from birka_memory_vault.models import NodeType, EdgeType

await init_db()

# Index a memory entry
async with AsyncSessionLocal() as session:
    mgr = MemoryEventManager(session)
    await mgr.add_memory_entry(MemoryEntryCreate(
        type="decision",
        title="Pivot to self-improving loop",
        content="We will capture manual edits to drafts and learn automatically.",
        tags=["architecture", "learning"],
        source_file="memory/2026-04-06.md"
    ))

# Create node and edge
file_node = await mgr.create_node(NodeCreate(type=NodeType.FILE.value, name="memory/2026-04-06.md"))
entry = await mgr.add_memory_entry(MemoryEntryCreate(...))
await mgr.create_edge(EdgeCreate(source_id=file_node.id, target_id=entry.id, type=EdgeType.CONTAINS.value))
await session.commit()
```

See `examples/` for mission tracking, snapshots, safeguards, and audit logging.

---

## Alembic Migrations

Migrations in `alembic/versions/`. Initial revision creates all 12 tables.

```bash
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

Always test migrations on a copy of the dev DB.

---

## Querying

Graph queries let you trace the full agent universe:

```python
# Active missions for Birka instance 'birka-1'
result = await session.execute(select(Mission).where(Mission.node_id == 'birka-1', Mission.status == MissionStatus.IN_PROGRESS))

# Spawn tree depth for a Birka
depth = await session.execute(select(func.max(SpawnTree.depth)).where(SpawnTree.parent_instance_id == 'birka-1'))

# All memory references to file 'foo.md'
refs = await session.execute(select(Edge).where(Edge.type == EdgeType.REFERENCES, Edge.target_id == ...))
```

---

## Event Flow

1. Agent writes `memory/YYYY-MM-DD.md` and/or updates `MEMORY.md`
2. Agent also calls `MemoryEventManager` to insert rows into `memory_entry` and create `Node`/`Edge` entries
3. On compaction (daily), `compaction_index` links curated entry to raw entries it merged
4. Snapshots (`snapshot_index`) capture global state at milestones
5. Orchestrator events (spawns, commands, safeguards) written to dedicated tables

---

## File Structure

```
birka-memory-vault/
├── alembic/versions/        # migrations
├── birka_memory_vault/      # package (models, schemas, events, database)
├── docs/                    # architecture details
├── examples/                # integration patterns
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Production Notes

- Use PostgreSQL (`postgresql+asyncpg://`)
- Partition `events` table by month for high volume
- Enable connection pooling
- Nightly backups (pg_dump)
- Monitor safeguard event rate

---

**Maintainer:** Simonas, SV Projects