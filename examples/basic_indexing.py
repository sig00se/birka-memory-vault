"""
Example: Indexing a memory entry and linking it to a file node.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from birka_memory_vault.database import AsyncSessionLocal, init_db
from birka_memory_vault.events import MemoryEventManager
from birka_memory_vault.schemas import MemoryEntryCreate, NodeCreate, EdgeCreate
from birka_memory_vault.models import NodeType, EdgeType

async def main():
    # Initialize (ensures tables exist)
    await init_db()

    async with AsyncSessionLocal() as session:
        mgr = MemoryEventManager(session)

        # 1) Create a Node representing the source file
        file_node = await mgr.create_node(NodeCreate(
            type=NodeType.FILE.value,
            name="memory/2026-04-06.md",
            properties={"path": "memory/2026-04-06.md", "size": 2048}
        ))

        # 2) Index the memory content
        entry = await mgr.add_memory_entry(MemoryEntryCreate(
            type="decision",
            title="Pivot to self-improving loop",
            content="We will now capture Simonas's manual edits to social-beast drafts and learn automatically.",
            tags=["architecture", "learning"],
            source_file="memory/2026-04-06.md"
        ))

        # 3) Link the memory to the file node
        await mgr.create_edge(EdgeCreate(
            source_id=file_node.id,
            target_id=entry.id,
            type=EdgeType.CONTAINS.value
        ))

        await session.commit()
        print(f"Indexed memory entry {entry.id} and linked to file {file_node.id}")

if __name__ == "__main__":
    asyncio.run(main())