# Architecture of Birka Memory Vault

## Evolution

The Vault started as a simple "memory index" to make Birka's Markdown memories searchable. It quickly became the backbone of OpenClaw's orchestration layer.

**Stage 1 — Indexer (3 tables)**
- `memory_entry` — raw indexed memories
- `compaction_index` — compaction lineage
- `snapshot_index` — state checkpoints

**Stage 2 — Graph Entities (added nodes/edges)**
- Need to relate memories across files and projects
- Nodes: typed entities (agent, mission, artifact, memory, file, user, context)
- Edges: typed relations (REFERENCES, PRODUCES, CONTAINS, DERIVED_FROM)

**Stage 3 — Mission Tracking**
- OpenClaw dispatches work to Birka via "missions"
- Need to track lifecycle, priority, result, errors, token count
- Table: `missions`

**Stage 4 — Fleet Management**
- Multiple Birka instances can run concurrently
- Track each instance (pid, model, capabilities, status, heartbeat)
- Table: `birka_fleet`

**Stage 5 — Spawn Tree**
- Birka can spawn sub-Birkas (recursive delegation)
- Need full tree with depth tracking to enforce limits and trace costs
- Table: `spawn_tree`

**Stage 6 — Capability Discovery**
- OpenClaw should route missions to the correct Birka based on declared capabilities
- Table: `resource_manifest` (parsed from TOOLS.md/SOUL.md)

**Stage 7 — Control Plane**
- OpenClaw sends signed commands (pause, kill, override model, drain, sync)
- Table: `control_commands`

**Stage 8 — Safeguards**
- Circuit breaker for runaway processes (loops, depth exceeded, cost ceiling, timeout, error rate)
- Table: `safeguard_events`

**Stage 9 — Event Log**
- Append-only log for all significant happenings (category: spawn, dispatch, command, safeguard, state_change, error, metric)
- Table: `events`

---

## Data Model Philosophy

- **Nodes are universal.** Every meaningful thing is a Node with a canonical ID. This eliminates separate tables for agents, missions, files, etc. All inherit from `Node` with a `type` discriminator.
- **Edges are typed.** Relationships have meaning (not just foreign keys). This allows graph traversals like "find all Missions that PRODUCE Memory and were SPAWNED_BY Agent X."
- **Append-only.** No UPDATE/DELETE on core operational tables. Corrections are new events; nothing is ever truly deleted.
- **Properties JSON.** Flexible attributes without schema churn. The properties dictionary can store arbitrary structured data per node type.
- **Audit first.** Every state change is recorded in `events` with source/target and metadata.

---

## Typical Integration Flow

1. **On startup:** Birka creates a Node of type `agent` representing itself.
2. **On spawn:** When Birka spawns a sub-agent, create a new Node (type=agent) and Edge `SPAWNED_BY`.
3. **On mission receive:** Create Node (type=mission), link to Birka via `DISPATCHED` edge, set status lifecycle.
4. **On memory creation:** Insert into `memory_entry`, create Node (type=memory) and Edge `CONTAINS` or `PRODUCES` as appropriate.
5. **On safeguard fire:** Insert row in `safeguard_events`, optionally create Node/Edge to link cause.
6. **On command:** Insert into `control_commands`, update target Birka's status when executed.
7. **On compaction:** Create `compaction_index` entry linking merged IDs to the new curated memory entry ID.
8. **On snapshot:** Insert `snapshot_index` with the current entry ID set and MEMORY.md hash.

---

## Query Patterns

```python
# Find all missions where Birka instance 'b1' exceeded its cost limit
miss = select(Mission).join(SafeguardEvent, Mission.id == SafeguardEvent.mission_id).where(
    SafeguardEvent.instance_id == 'b1',
    SafeguardEvent.safeguard_type == SafeguardType.COST_CEILING
)

# Get the spawn tree depth for a particular Birka
depth = select(func.max(SpawnTree.depth)).where(SpawnTree.parent_instance_id == 'b1')

# List capabilities of all active Birka instances
caps = select(BirkaFleet.id, ResourceManifest.capability_name).join(ResourceManifest).where(BirkaFleet.status == FleetStatus.ACTIVE)

# Find all memories that reference file 'foo.md'
refs = select(MemoryEntry).join(Edge, MemoryEntry.id == Edge.target_id).where(
    Edge.source_id == (select(Node.id).where(Node.type == NodeType.FILE, Node.name == 'foo.md'))
)
```

---

## Performance Considerations

- Index all foreign keys and commonly filtered columns (see `models.py` `__table_args__`)
- Use async sessions to avoid blocking the event loop
- Partition `events` table by month if logging high volume
- Keep long-running transactions short; the Vault is append-heavy
- Connection pool size should match concurrent Birka instances + margin

---

## Future Extensions

- **Timeseries aggregation** for token usage and cost metrics
- **Full-text search** integration (PostgreSQL tsvector) as a faster alternative to Markdown grep
- **Webhooks** on specific events (safeguard fire, mission completed)
- **GraphQL endpoint** for OpenClaw UI to browse the agent universe

---

This architecture diagram is the culmination of 4 months of operation. It is designed to scale to hundreds of concurrent Birka instances while keeping every decision auditable.