# Birka Memory Vault

Built March 2026 as a structured memory layer for autonomous agents. Designed to solve the stateless session problem — agents that forget everything between runs.

---

## The Problem

Agents run, produce output, exit. Their memory vanishes. Rebuilding context from raw files is slow, error-prone, and impossible to query.

---

## Core Idea

Keep raw Markdown as the source of truth. Add a **parallel structured index** that remembers relationships, tags, lineages, and audit trails. The Vault doesn't store content — it stores *structure* about the content. Dual-write, never replace.

---

## Why This Exists

- Queryable memory: find all decisions about a project in the last week
- Relationships: see which agent produced which artifact, which mission spawned which memory
- Compaction trace: track how daily logs were merged into curated summaries
- Capability orchestration: know which agent can do what
- Works across restarts, deployments, and multiple concurrent instances

---

## Schema (at a glance)

Three foundation tables + nine orchestrator tables:

- **memory_entry** — indexed memories with tags and source file
- **compaction_index** — lineage of merged memories
- **snapshot_index** — periodic state checkpoints

- **nodes** — universal typed entities (agent, mission, artifact, memory, file, user, context)
- **edges** — typed relations (SPAWNED_BY, PRODUCES, REFERENCES, CONTAINS, DERIVED_FROM, BLOCKS, DEPENDS_ON)
- **missions** — dispatched work units with lifecycle tracking
- **birka_fleet** — all running agent instances with capabilities and heartbeats
- **spawn_tree** — full delegation tree with depth tracking
- **resource_manifest** — declared capabilities parsed from TOOLS.md/SOUL.md
- **control_commands** — signed commands (PAUSE, KILL, OVERRIDE_MODEL, DRAIN, SYNC)
- **safeguard_events** — circuit breaker events (loops, cost ceiling, timeout)
- **events** — append-only audit log (spawn, dispatch, command, safeguard, state_change, error, metric)

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

Default database is SQLite (`sqlite+aiosqlite:///./birka_memory.db`). For production, set `DATABASE_URL` to PostgreSQL.

---

## Integration

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from birka_memory_vault.database import AsyncSessionLocal, init_db
from birka_memory_vault.events import MemoryEventManager

await init_db()

# Index a memory entry
from birka_memory_vault.schemas import MemoryEntryCreate
async with AsyncSessionLocal() as session:
    mgr = MemoryEventManager(session)
    await mgr.add_memory_entry(MemoryEntryCreate(
        type="decision",
        title="Pivot to self-improving loop",
        content="We will capture manual edits to drafts and learn automatically.",
        tags=["architecture", "learning"],
        source_file="memory/2026-04-06.md"
    ))

# Create nodes and edges
from birka_memory_vault.schemas import NodeCreate, EdgeCreate
from birka_memory_vault.models import NodeType, EdgeType

async with AsyncSessionLocal() as session:
    mgr = MemoryEventManager(session)
    file_node = await mgr.create_node(NodeCreate(type=NodeType.FILE.value, name="memory/2026-04-06.md"))
    entry = await mgr.add_memory_entry(MemoryEntryCreate(type="decision", title="...", content="...", tags=["..."], source_file="memory/2026-04-06.md"))
    await mgr.create_edge(EdgeCreate(source_id=file_node.id, target_id=entry.id, type=EdgeType.CONTAINS.value))
    await session.commit()
```

See `examples/` for mission tracking, snapshots, safeguards, and audit logging.

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
- Partition `events` by month for high volume
- Enable connection pooling
- Nightly backups
- Monitor safeguard event rate

---

**Maintainer:** Simonas, SV Projects