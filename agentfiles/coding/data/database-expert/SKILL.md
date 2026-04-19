---
name: database-expert
description: >
  Use for schema design, migrations, query optimization, indexing, and
  ORM work (SQLAlchemy, Prisma, Diesel). Trigger phrases: "design the
  schema for X", "write a migration for this change", "this query is
  slow", "add an index for this lookup", "SQL or NoSQL for this feature",
  "I'm seeing N+1 queries", "is this migration safe for production",
  "what isolation level do I need", "should this be a foreign key or
  denormalized", "reviewing these SQLAlchemy/Prisma models". Covers
  relational and document databases, reversible/online migration
  patterns, and transaction safety. Do NOT use for general CPU/memory
  profiling (use performance-profiling), database server install /
  replication (use infrastructure-expert), API endpoint shape (use
  api-architect), or SQL injection review (use security-review).
---

# Database Expert

Deep database knowledge — schema design, query optimization, migration safety,
and ORM best practices across SQLAlchemy, Prisma, and Diesel.

**Core principle:** The database outlives every application that talks to it.
Schema decisions are the hardest to reverse — get them right first.

## When to Use

- Designing new tables, collections, or schema changes
- Writing or reviewing database migrations
- Investigating slow queries or high database load
- Choosing between SQL and NoSQL for a new feature
- Working with ORMs — SQLAlchemy, Prisma, Diesel, or raw SQL
- Reviewing transaction boundaries and isolation levels
- Adding indexes or optimizing existing ones

## When NOT to Use

- **General performance profiling** (CPU, memory) — use `performance-profiling`
- **Infrastructure setup** (database server config, replication) — use `infrastructure-expert`
- **API endpoint design** that happens to touch a database — use `api-architect`
- **Security review** of SQL injection — use `security-review`

## The Iron Law

```
EVERY MIGRATION MUST BE REVERSIBLE AND SAFE TO RUN ON A LIVE DATABASE
```

No migration should lock a table for more than a few seconds on production data.

## Schema Design Process

### Phase 1: Data Modeling

1. **Identify entities and relationships** — draw them out before writing DDL
2. **Normalize to 3NF first** — then denormalize only with measured justification
3. **Choose primary keys carefully** — UUIDs for distributed systems, auto-increment for simplicity
4. **Add timestamps** — `created_at` and `updated_at` on every table, always
5. **Plan for soft deletes** if business logic requires audit trails

### Phase 2: Index Strategy

| Query Pattern | Index Type |
|---------------|-----------|
| Exact match (`WHERE email = ?`) | B-tree (default) |
| Range queries (`WHERE created_at > ?`) | B-tree |
| Full-text search | GIN / full-text index |
| JSON field queries | GIN (Postgres) |
| Geospatial queries | GiST / spatial index |
| Composite lookups (`WHERE a = ? AND b = ?`) | Composite index (leftmost prefix rule) |

**Index rules of thumb:**
- Index every foreign key column
- Index columns used in WHERE, JOIN, ORDER BY
- Composite indexes: put high-cardinality columns first
- Don't over-index — each index slows writes

### Phase 3: Query Optimization

1. **Run EXPLAIN ANALYZE** before and after changes — never optimize blind
2. **Detect N+1 queries** — the most common ORM performance killer:
   ```python
   # BAD: N+1 — one query per post's comments
   posts = session.query(Post).all()
   for post in posts:
       print(post.comments)  # lazy load fires N queries

   # GOOD: eager load
   posts = session.query(Post).options(joinedload(Post.comments)).all()
   ```
3. **Watch for sequential scans** on large tables — usually means missing index
4. **Paginate everything** — never `SELECT *` without LIMIT
5. **Use CTEs for readability** but benchmark — some databases don't optimize them well

## Safe Migration Patterns

| Operation | Unsafe | Safe |
|-----------|--------|------|
| Add column | `NOT NULL` without default | Add with default, or nullable first |
| Remove column | Drop directly | Stop reading → deploy → drop column |
| Rename column | Rename directly | Add new → backfill → migrate reads → drop old |
| Add index | `CREATE INDEX` (locks table) | `CREATE INDEX CONCURRENTLY` (Postgres) |
| Change column type | `ALTER COLUMN TYPE` | Add new column → backfill → swap |
| Add foreign key | `ADD CONSTRAINT` (full scan) | Add as `NOT VALID` → `VALIDATE` separately |

**Migration checklist:**
1. Can this migration run while the previous app version is still serving traffic?
2. Can this migration be rolled back without data loss?
3. How long will it take on production data volume?
4. Does it acquire locks that block reads or writes?

## ORM-Specific Guidance

### SQLAlchemy (Python)

```python
# Always use explicit session management
with Session(engine) as session:
    result = session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

# Use Alembic for migrations
# alembic revision --autogenerate -m "add users table"
# alembic upgrade head
```

### Prisma (TypeScript)

```typescript
// Use transactions for multi-step operations
await prisma.$transaction([
  prisma.account.update({ where: { id: 1 }, data: { balance: { decrement: 100 } } }),
  prisma.account.update({ where: { id: 2 }, data: { balance: { increment: 100 } } }),
]);

// Use include/select to avoid over-fetching
const user = await prisma.user.findUnique({
  where: { id },
  select: { name: true, email: true },
});
```

### Diesel (Rust)

```rust
// Use connection pooling (r2d2 or deadpool)
// Run migrations with diesel_migrations::embed_migrations!
// Always use .get_result() for INSERT/UPDATE to verify
let new_user = diesel::insert_into(users)
    .values(&new_user_form)
    .get_result::<User>(&mut conn)?;
```

## Transaction Safety

- **Default to READ COMMITTED** — sufficient for most operations
- **Use SERIALIZABLE** only when business logic requires it (inventory, transfers)
- **Keep transactions short** — no HTTP calls, no user input inside transactions
- **Handle deadlocks** — retry with exponential backoff
- **Use advisory locks** for operations that need coordination without row locking

## Anti-patterns

| Anti-pattern | Why It's Bad | Instead |
|-------------|-------------|---------|
| `SELECT *` in application code | Fetches unused columns, breaks on schema changes | Explicit column lists |
| N+1 queries | O(N) database roundtrips | Eager loading or batch queries |
| Business logic in triggers | Invisible side effects, untestable | Application-layer logic |
| No indexes on foreign keys | Slow JOINs and cascading deletes | Index every FK |
| String concatenation in queries | SQL injection | Parameterized queries always |
| Unbounded queries | OOM on large tables | Always paginate with LIMIT/OFFSET or cursors |
| Migrations that can't roll back | Stuck deployments | Write up and down migrations |
| UUIDs as clustered primary keys | Random inserts fragment B-tree | UUID v7 (time-ordered) or auto-increment |

## Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `EXPLAIN ANALYZE` | Query plan analysis | Run in database client |
| `pgcli` / `mycli` | Interactive SQL with autocomplete | `pgcli postgres://...` |
| `Alembic` | Python/SQLAlchemy migrations | `alembic upgrade head` |
| `prisma migrate` | Prisma schema migrations | `npx prisma migrate dev` |
| `diesel migration` | Rust/Diesel migrations | `diesel migration run` |
| `pg_stat_statements` | Query performance stats (Postgres) | Enable extension, query view |

## Outputs

- Schema design with entity relationships documented
- Migration files that are reversible and production-safe
- Query optimization report with EXPLAIN ANALYZE before/after
- Index recommendations based on query patterns
- Chain into `tdd` for data-layer tests, `verification-before-completion` to confirm
