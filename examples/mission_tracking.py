"""
Example: Recording a mission dispatched to Birka and its completion.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from birka_memory_vault.database import AsyncSessionLocal, init_db
from birka_memory_vault.events import MemoryEventManager
from birka_memory_vault.schemas import MissionCreate, NodeCreate
from birka_memory_vault.models import NodeType, MissionStatus, EdgeType

async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        mgr = MemoryEventManager(session)

        # Create Birka node (the agent that will receive the mission)
        birka_node = await mgr.create_node(NodeCreate(
            type=NodeType.AGENT.value,
            name="Birka-Main",
            properties={"model": "openrouter/free", "workspace": "/home/.../workspace"}
        ))

        # OpenClaw dispatches a mission
        mission = await mgr.create_mission(MissionCreate(
            node_id=birka_node.id,
            openclaw_id="oc-mission-123",
            birka_instance_id="birka-main-001",
            title="Draft Lithuanian blog post",
            description="Write a 500-word blog about AI in marketing",
            task_payload={"topic": "AI marketing", "word_count": 500, "language": "lt"},
            priority=10,
            dispatched_at=datetime.utcnow()
        ))

        # Link mission to Birka
        await mgr.create_edge(EdgeCreate(
            source_id=birka_node.id,
            target_id=mission.node_id,
            type=EdgeType.DISPATCHED.value
        ))

        print(f"Mission {mission.id} dispatched to {birka_node.name}")

        # ... later, mission completes
        mission.status = MissionStatus.COMPLETED.value
        mission.completed_at = datetime.utcnow()
        mission.result = {"word_count": 512, "tone": "casual", "language": "lt"}
        await session.commit()

        # Optionally create a MemoryEntry for the output
        output_entry = await mgr.add_memory_entry(MemoryEntryCreate(
            type="artifact",
            title="Lithuanian AI marketing draft",
            content="[full content would be here]",
            tags=["blog", "lt", "ai-marketing"],
            source_file="drafts/2026-04-06-lt-ai-marketing.md"
        ))

        # Link mission -> output memory
        await mgr.create_edge(EdgeCreate(
            source_id=mission.node_id,
            target_id=output_entry.id,
            type=EdgeType.PRODUCES.value
        ))

        await session.commit()
        print(f"Mission {mission.id} completed; output indexed as memory {output_entry.id}")

if __name__ == "__main__":
    asyncio.run(main())