# Database Interview Cheat Sheet

Senior-level notes on relational databases, SQL, scaling, Redis, and MongoDB. SQL examples use PostgreSQL syntax unless noted; commands and behavior can differ by database engine.

## Contents

- [Relational vs. non-relational databases](#relational-vs-non-relational-databases)
- [How to design a database](#how-to-design-a-database)
- [ACID and transaction isolation](#acid-and-transaction-isolation)
- [Referential integrity](#referential-integrity)
- [SQL joins](#sql-joins)
- [Aggregate functions](#aggregate-functions)
- [SQL window functions](#sql-window-functions)
- [SQL queries](#sql-queries)
- [Database backups and recovery](#database-backups-and-recovery)
- [Stored procedures, functions, and triggers](#stored-procedures-functions-and-triggers)
- [Locks and concurrency control](#locks-and-concurrency-control)
- [Indexes and commands](#indexes-and-commands)
- [B-tree and B+ tree](#b-tree-and-b-tree)
- [Clustered and non-clustered indexes](#clustered-and-non-clustered-indexes)
- [Scaling: vertical, horizontal, and sharding](#scaling-vertical-horizontal-and-sharding)
- [Database partitioning vs. sharding](#database-partitioning-vs-sharding)
- [Can joins work across shards?](#can-joins-work-across-shards)
- [Does Redis use threads?](#does-redis-use-threads)
- [MongoDB](#mongodb)
- [Drawbacks of non-relational databases](#drawbacks-of-non-relational-databases)
- [Practical SQL scaling and isolation questions](#practical-sql-scaling-and-isolation-questions)
- [References](#references)

## Relational vs. non-relational databases

| | Relational (SQL) | Non-relational (often called NoSQL) |
|---|---|---|
| Data model | Tables, rows, columns, defined relationships | Document, key-value, wide-column, or graph models |
| Schema | Usually explicit and enforced by the database | Often flexible; constraints depend on the product and design |
| Relationships | Foreign keys and joins are central features | Often embedded or resolved by application logic; some systems also support joins |
| Transactions | ACID transactions are a core strength | Varies; many products support transactions, with product-specific scope and cost |
| Typical fit | Related business data, reporting, strong constraints, flexible querying | Data naturally shaped as documents, key-value access, graph traversal, or very large distributed workloads |
| Examples | PostgreSQL, MySQL, SQL Server | MongoDB (document), Redis (key-value), Cassandra (wide-column), Neo4j (graph) |

Choose based on access patterns, consistency requirements, data relationships, operational skills, and scale. “SQL scales vertically” and “NoSQL has no transactions” are both overgeneralizations: relational databases can scale out, and many non-relational databases support transactions.

## How to design a database

Start from the domain and the queries the application must support. A useful sequence is:

1. List entities and their attributes (for example, `Customer`, `Order`, `OrderItem`).
2. Define relationships and cardinality: one-to-one, one-to-many, or many-to-many.
3. Choose primary keys and add foreign keys, `NOT NULL`, `UNIQUE`, and `CHECK` constraints for invariants the database can enforce.
4. Normalize first to reduce duplicated facts and update anomalies; commonly target 3NF for transactional data.
5. Identify high-frequency reads/writes, then add indexes based on actual filters, joins, and ordering.
6. Review query plans and representative data volumes; measure before denormalizing or adding caches.
7. Plan schema evolution through reversible or backward-compatible migrations.

Example many-to-many design:

```sql
CREATE TABLE students (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE courses (
    id BIGINT PRIMARY KEY,
    title TEXT NOT NULL UNIQUE
);

CREATE TABLE enrollments (
    student_id BIGINT NOT NULL REFERENCES students(id),
    course_id BIGINT NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, course_id)
);
```

The junction table represents the many-to-many relationship. Its composite primary key prevents duplicate enrollment pairs; an additional index on `(course_id, student_id)` helps queries that start from a course.

| Term | Plain meaning |
|---|---|
| Normalization | Organize facts to reduce duplication and inconsistent updates |
| Denormalization | Intentionally duplicate or precompute data to make chosen reads cheaper |
| Constraint | Database-enforced rule such as uniqueness or valid references |
| Data model | The shape and relationships chosen to represent application data |

| Normal form | Main goal |
|---|---|
| 1NF | Each field holds one value from its domain; no repeating column groups |
| 2NF | In 1NF, and every non-key field depends on the whole candidate key (relevant for composite keys) |
| 3NF | In 2NF, and non-key fields depend on the key, the whole key, and nothing but the key; avoid transitive dependencies |
| BCNF | Every determinant is a candidate key; stricter than 3NF for certain overlapping candidate-key cases |

Denormalize only for a measured workload, and define how duplicated values stay in sync.

## ACID and transaction isolation

ACID describes transaction guarantees:

| Property | Meaning | Example |
|---|---|---|
| Atomicity | All transaction operations commit, or none do | A transfer debits one account and credits the other together |
| Consistency | A committed transaction preserves defined rules | Balance constraints remain valid |
| Isolation | Concurrent transactions behave according to the isolation level | Two reservations should not both consume the last item |
| Durability | Committed data survives failures covered by the database's durability guarantees | A confirmed payment remains recorded after restart |

```sql
BEGIN;
UPDATE accounts SET balance = balance - 50 WHERE id = 1;
UPDATE accounts SET balance = balance + 50 WHERE id = 2;
COMMIT; -- use ROLLBACK if an operation fails
```

Isolation levels control what concurrent transactions can observe. Common anomalies include dirty reads (reading uncommitted data), non-repeatable reads (same row changes between reads), and phantom reads (new matching rows appear). Exact guarantees vary by engine; PostgreSQL, for example, implements `READ UNCOMMITTED` as `READ COMMITTED`.

| Level | General idea |
|---|---|
| Read uncommitted | Weakest; may expose uncommitted changes in engines that support it |
| Read committed | Each statement sees committed data as of that statement |
| Repeatable read | Re-reading rows is stable within a transaction; phantom handling varies by engine |
| Serializable | Strongest; outcome is equivalent to serial execution, sometimes with transaction retries |

The practical interview answer: choose isolation to protect the business invariant, understand your database's behavior, and retry serialization/deadlock failures safely.

## Referential integrity

Referential integrity means relationships between rows stay valid. A foreign key ensures that a child row points to an existing parent row (or is `NULL` if the column allows it). The database can enforce this rule even when writes come from multiple services or scripts.

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT
);
```

| Foreign-key action | Effect when the parent row is updated/deleted |
|---|---|
| `RESTRICT` / `NO ACTION` | Reject the operation while child rows refer to it (timing differs by engine/constraint) |
| `CASCADE` | Apply the parent delete/update to referencing rows |
| `SET NULL` | Set child key to `NULL`; column must allow nulls |
| `SET DEFAULT` | Set the child key to its default; default must reference a valid parent |

Use cascading actions only when they match the domain. An index on the child foreign-key column often helps joins and parent deletes/updates; many databases do not automatically create that index.

## SQL joins

A join combines rows from tables using a related key. The join condition is normally a primary-key/foreign-key relationship.

```sql
SELECT o.id, c.name, o.total
FROM orders AS o
JOIN customers AS c ON c.id = o.customer_id;
```

| Join | Rows returned |
|---|---|
| `INNER JOIN` | Only rows with a match on both sides |
| `LEFT JOIN` | Every left row plus matching right rows; unmatched right columns are `NULL` |
| `RIGHT JOIN` | Every right row plus matching left rows |
| `FULL OUTER JOIN` | Matched rows and unmatched rows from either side |
| `CROSS JOIN` | Every left/right combination (Cartesian product) |
| Self join | A table joined to itself, for example employee to manager |

Find customers with no orders:

```sql
SELECT c.id, c.name
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id
WHERE o.id IS NULL;
```

For a left join, placing a right-table filter in `WHERE` can remove `NULL` rows and make the result behave like an inner join. Put the condition in `ON` when unmatched left rows must remain.

Compare an inner join and a left join:

```sql
-- Only orders with a matching customer
SELECT c.name, o.id
FROM customers AS c
INNER JOIN orders AS o ON o.customer_id = c.id;

-- Keep every customer, including customers with no orders
SELECT c.name, o.id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id;
```

Other useful forms:

```sql
-- Keep every row from the right side
SELECT c.name, o.id
FROM customers AS c
RIGHT JOIN orders AS o ON o.customer_id = c.id;

-- Keep unmatched rows from both tables (supported by PostgreSQL)
SELECT c.name, o.id
FROM customers AS c
FULL OUTER JOIN orders AS o ON o.customer_id = c.id;

-- Pair every customer with every region; row count is customers * regions
SELECT c.name, r.name
FROM customers AS c CROSS JOIN regions AS r;

-- Self join: employee to manager
SELECT e.name AS employee, m.name AS manager
FROM employees AS e
LEFT JOIN employees AS m ON m.id = e.manager_id;
```

## Aggregate functions

Aggregate functions calculate one result from multiple rows. `GROUP BY` produces one output row per group; `HAVING` filters groups after aggregation, while `WHERE` filters input rows before grouping.

```sql
SELECT customer_id,
       COUNT(*) AS order_count,
       SUM(total) AS revenue,
       AVG(total) AS average_order,
       MIN(created_at) AS first_order,
       MAX(created_at) AS latest_order
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total) >= 1000
ORDER BY revenue DESC;
```

| Function | Purpose | Note |
|---|---|---|
| `COUNT(*)` | Count input rows | Includes rows where columns are `NULL` |
| `COUNT(column)` | Count non-`NULL` values | Excludes `NULL` values |
| `SUM`, `AVG` | Total and mean | Ignore `NULL` inputs in common SQL engines |
| `MIN`, `MAX` | Smallest/largest value | Work with ordered data types |

`GROUP BY` and window functions differ: grouping collapses rows; a window function keeps each row and adds a computed value.

## SQL window functions

A window function calculates something using a set of related rows, then shows that answer beside each original row. Think: **keep every row, add a value calculated across its “window” of related rows.**

For example, show each order and the customer's total spending. The total repeats on each of that customer's order rows:

```sql
SELECT
    customer_id,
    order_id,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id) AS customer_total
FROM orders;
```

Here `PARTITION BY customer_id` means “calculate separately for each customer.” It does **not** group rows into one result row per customer. Compare with `GROUP BY`, which does collapse each customer to one row:

```sql
SELECT customer_id, SUM(amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

`OVER (...)` is what makes an aggregate such as `SUM` act as a window function. Add `ORDER BY` inside `OVER` when the calculation depends on row sequence, such as rank or running total.

```sql
SELECT department_id, employee_id, salary,
       RANK() OVER (
           PARTITION BY department_id
           ORDER BY salary DESC
       ) AS salary_rank
FROM employees;
```

Common functions:

| Function | Use |
|---|---|
| `ROW_NUMBER()` | Unique sequential number per partition |
| `RANK()` | Ranking with gaps after ties (1, 1, 3) |
| `DENSE_RANK()` | Ranking without gaps after ties (1, 1, 2) |
| `LAG()` / `LEAD()` | Read a previous/next row's value |
| `SUM()`, `AVG()`, `COUNT()` with `OVER` | Running or partition-level aggregates |

Running total example:

```sql
SELECT account_id, occurred_at, amount,
       SUM(amount) OVER (
           PARTITION BY account_id
           ORDER BY occurred_at, id
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS running_total
FROM transactions;
```

Use a deterministic tie-breaker in `ORDER BY` when row order matters. Window-frame defaults vary with the function and ordering; specify a frame explicitly for running aggregates.

## SQL queries

### Employees who logged in for three consecutive days

**Question:** given `employee_logins(employee_id, login_date)`, return employees who logged in on at least three consecutive calendar days. A four-day streak also qualifies; weekends count as calendar days.

The [window functions section](#sql-window-functions) provides the foundation. The extra steps are to remove duplicate logins on the same day, order dates separately for each employee, and check that the next two dates are one and two days later.

```sql
-- PostgreSQL; login_date can be a DATE or a timestamp.
WITH daily_logins AS (
    SELECT DISTINCT employee_id, CAST(login_date AS DATE) AS login_day
    FROM employee_logins
    WHERE employee_id IS NOT NULL AND login_date IS NOT NULL
), next_logins AS (
    SELECT employee_id, login_day,
           LEAD(login_day, 1) OVER (
               PARTITION BY employee_id ORDER BY login_day
           ) AS next_day,
           LEAD(login_day, 2) OVER (
               PARTITION BY employee_id ORDER BY login_day
           ) AS day_after_next
    FROM daily_logins
)
SELECT DISTINCT employee_id
FROM next_logins
WHERE next_day = login_day + 1
  AND day_after_next = login_day + 2
ORDER BY employee_id;
```

**How to explain it in an interview:**

1. `daily_logins` keeps one row per employee per calendar day. Multiple logins on one day must not count as multiple days.
2. `PARTITION BY employee_id` prevents dates from different employees being compared.
3. `ORDER BY login_day` puts each employee's dates in sequence; `LEAD` reads the next and second-next dates.
4. In PostgreSQL, adding an integer to a `DATE` adds calendar days. Both comparisons must match; merely having three login rows is insufficient.
5. The final `DISTINCT` returns an employee once even when they have several qualifying streaks. Missing following rows produce `NULL` and do not pass the filter.

Example after removing duplicate days:

| Employee | Login days | Qualifies? |
|---|---|---|
| 101 | Oct 1, Oct 2, Oct 3 | Yes |
| 102 | Oct 1, Oct 2, Oct 4 | No: a day is missing |
| 103 | Oct 1, Oct 2, Oct 3, Oct 4 | Yes: at least three consecutive days |
| 104 | Oct 1 only, with three logins that day | No: only one distinct day |

If timestamps include time zones, define the business time zone before extracting the date. For a PostgreSQL `TIMESTAMPTZ`, for example, use `(login_date AT TIME ZONE 'Asia/Kolkata')::date` for India calendar days. The plain cast uses the session time zone for `TIMESTAMPTZ`.

### Follow-up: return streak dates and lengths (gaps and islands)

For a configurable minimum length, group each uninterrupted run of dates into an “island.” Subtracting the row number from each date gives the same key throughout a consecutive streak:

```sql
WITH daily_logins AS (
    SELECT DISTINCT employee_id, CAST(login_date AS DATE) AS login_day
    FROM employee_logins
    WHERE employee_id IS NOT NULL AND login_date IS NOT NULL
), numbered AS (
    SELECT employee_id, login_day,
           ROW_NUMBER() OVER (
               PARTITION BY employee_id ORDER BY login_day
           ) AS rn
    FROM daily_logins
), grouped AS (
    SELECT employee_id, login_day,
           login_day - CAST(rn AS INTEGER) AS streak_key
    FROM numbered
)
SELECT employee_id,
       MIN(login_day) AS streak_start,
       MAX(login_day) AS streak_end,
       COUNT(*) AS consecutive_days
FROM grouped
GROUP BY employee_id, streak_key
HAVING COUNT(*) >= 3
ORDER BY employee_id, streak_start;
```

For Oct 1, 2, 3 with row numbers 1, 2, 3, all three dates minus their row numbers give Sep 30. A missing day changes that key and starts another group. Replace `>= 3` with `>= N` for at least N days, or `= 3` for maximal streaks of exactly three days. To return only employee IDs, wrap this result in a CTE and select `DISTINCT employee_id`.

**Common traps:** comparing only day-of-month values (fails across month/year boundaries), counting rows without removing duplicate days, or checking only `MAX(date) - MIN(date)` without verifying that every intervening day exists. Date arithmetic syntax differs in MySQL and SQL Server; these examples follow the cheatsheet's PostgreSQL convention.

## Stored procedures, functions, and triggers

A **stored procedure** is a named database program called explicitly, often for multi-step work or administrative operations. A **stored function** returns a value (or table) and can commonly be used inside SQL expressions. A **trigger** runs automatically when a configured table event occurs.

| Object | How it runs | Common use | Watch out for |
|---|---|---|---|
| Procedure | Explicit call (`CALL` in PostgreSQL) | Encapsulate a database operation or batch | Transaction control and syntax differ by database |
| Function | Called in a query or expression | Reusable calculation, transformation, or table result | Hidden work in queries; volatility and side effects affect planning/semantics |
| Trigger | Automatically before/after a table event | Audit rows or maintain tightly coupled derived data | Hidden side effects, recursion, bulk-write overhead, ordering complexity |

PostgreSQL-style examples:

```sql
CREATE FUNCTION add_tax(amount NUMERIC)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
AS $$ SELECT amount * 1.10 $$;

SELECT add_tax(100);
```

```sql
CREATE PROCEDURE close_old_orders(cutoff TIMESTAMP)
LANGUAGE SQL
AS $$
    UPDATE orders SET status = 'closed'
    WHERE status = 'open' AND created_at < cutoff;
$$;

CALL close_old_orders(TIMESTAMP '2025-01-01');
```

Triggers use a trigger function plus a trigger definition in PostgreSQL; other engines have different syntax. Prefer application/service code for business workflows when it keeps behavior visible and testable. Use triggers for narrow invariants/auditing when all writers must obey the rule, and document them clearly.

```sql
-- PostgreSQL: write an audit record when an order's status changes
CREATE FUNCTION audit_order_status() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO order_audit(order_id, old_status, new_status, changed_at)
        VALUES (OLD.id, OLD.status, NEW.status, CURRENT_TIMESTAMP);
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER order_status_audit
AFTER UPDATE OF status ON orders
FOR EACH ROW EXECUTE FUNCTION audit_order_status();
```

## Locks and concurrency control

Concurrency control prevents simultaneous transactions from corrupting data or violating invariants. Databases combine transaction isolation, locks, and often MVCC (multi-version concurrency control), where readers can see a consistent version while writers create newer versions.

| Lock / technique | What it protects | Example use |
|---|---|---|
| Shared (read) lock | Allows compatible readers; conflicts with some writes | Read data while preventing a conflicting update, when supported/needed |
| Exclusive (write) lock | Prevents conflicting access to a row/table | Updating a row |
| Row-level lock | Locks selected rows | Reserve inventory without blocking unrelated rows |
| Table-level lock | Locks a table or broader resource | Schema change or operations needing broad coordination |
| Optimistic concurrency | Detect conflict at write time, often with a version column | Retry if `version` changed since it was read |
| Pessimistic concurrency | Lock before changing data | Serialize sensitive updates such as balance transfers |

```sql
BEGIN;
SELECT available FROM inventory WHERE product_id = 7 FOR UPDATE;
UPDATE inventory SET available = available - 1
WHERE product_id = 7 AND available > 0;
COMMIT;
```

The row lock is held until commit/rollback. Always check whether the conditional update changed a row; if not, inventory was unavailable. Keep transactions short and acquire multiple locks in a consistent order to reduce deadlocks. A deadlock victim or serialization failure should usually retry the whole transaction, with a bounded retry policy.

## Indexes and commands

An index is an auxiliary data structure that helps the database find or order rows without scanning the whole table. The optimizer chooses whether to use it; an index is not a command to force a particular plan.

PostgreSQL examples:

```sql
-- Single-column index for filtering/ordering by email
CREATE INDEX idx_users_email ON users (email);

-- Use this instead of the ordinary index when email must be unique
CREATE UNIQUE INDEX idx_users_email_unique ON users (email);

-- Composite index; leading column order matters for query matching
CREATE INDEX idx_orders_customer_created ON orders (customer_id, created_at DESC);

-- Partial index: only index active rows (PostgreSQL)
CREATE INDEX idx_active_users_email ON users (email) WHERE active = TRUE;

-- Inspect a query plan (ANALYZE executes the query)
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE customer_id = 42 ORDER BY created_at DESC;

DROP INDEX idx_users_email;
```

For a production PostgreSQL table, `CREATE INDEX CONCURRENTLY` can reduce blocking of writes while the index is built, with tradeoffs and restrictions (for example, it cannot run inside a transaction block). Syntax differs across database engines.

| Index concept | Interview point |
|---|---|
| Composite index | Column order matters; `(a, b)` commonly supports filters starting with `a`, not just `b` |
| Covering index | Stores/includes extra columns so a query may be answered from the index; syntax and behavior vary |
| Unique index | Speeds lookup and enforces no duplicate key values |
| Partial/filtered index | Indexes only rows matching a predicate; database-specific |
| Index selectivity | More selective predicates often make an index more useful; not the only planner factor |

Indexes speed some reads but consume disk and memory and add work to inserts, updates, and deletes. Avoid indexing every column. Check real query plans, data distribution, and write cost.

## B-tree and B+ tree

B-trees and B+ trees are balanced search trees designed to keep lookup depth small. Database indexes often use a B-tree-family structure because it supports equality lookups and ordered range scans while limiting disk page reads. Exact implementation details depend on the database.

| | B-tree (general form) | B+ tree |
|---|---|---|
| Where keys/data pointers may appear | Internal and leaf nodes | Internal nodes guide search; record references/entries are stored at leaves |
| Leaf linkage | Not required by the general structure | Leaves are commonly linked in key order |
| Range scans | Traverse tree and ordered nodes | Walk linked leaves efficiently after locating the first key |
| Fan-out | Depends on node layout | Internal nodes can hold many separator keys, keeping the tree shallow |

The practical interview answer is that a B+ tree's high fan-out and linked leaves suit disk/page-oriented storage and range scans. Avoid claiming every database uses exactly the same B+ tree implementation or that lookups are always literally `O(log n)` disk reads; caching and page layout matter.

## Clustered and non-clustered indexes

The names and exact behavior are database-specific, so answer in the context of the engine.

| | Clustered index | Non-clustered / secondary index |
|---|---|---|
| Leaf level | Stores or organizes the table's row data by the index key | Separate structure stores keys and row locators (or primary-key values) |
| Count | Usually at most one per table when the table is organized by one key | Many can exist on a table |
| Strength | Efficient key lookups and range scans on the clustering key | Supports other lookup and sort patterns |
| Cost | Choosing a poor key can cause page splits or expensive row movement | Extra storage and write maintenance; lookup may need another row fetch |

Examples: InnoDB organizes row data by its clustered index, normally the primary key; secondary indexes include the primary-key value. SQL Server exposes clustered and non-clustered indexes explicitly. PostgreSQL's ordinary indexes are separate from the heap; its `CLUSTER` command rewrites a table in index order but does not keep it ordered as rows change.

## Scaling: vertical, horizontal, and sharding

| Approach | What changes | Benefits | Costs / limits |
|---|---|---|---|
| Vertical scaling | Give one database server more CPU, RAM, or storage | Simple application model; can improve many workloads | Hardware ceiling, cost, and potential single-node bottleneck |
| Horizontal scaling | Add servers and distribute work/data | More capacity and resilience potential | Routing, replication consistency, rebalancing, and operations become harder |
| Sharding | Split rows across database nodes by a shard key | Spreads storage and writes across shards | Cross-shard queries/transactions, hot shards, and resharding complexity |
| Read replicas | Copy data to servers serving reads | Adds read capacity | Replication lag; writes still go to primary in common setups |

Sharding is a form of horizontal partitioning across independent database nodes. Pick a shard key that distributes load and keeps common queries local. A bad key can create hot shards or force scatter/gather queries. Plan for rebalancing, shard-key changes, transactions, backups, and failure recovery before sharding; it adds operational complexity.

Do not confuse scaling with partitioning: **horizontal partitioning** splits rows into subsets; **vertical partitioning** splits columns (often separating rarely used or sensitive fields). Vertical scaling means adding resources to one server, while horizontal scaling means adding servers.

## Database partitioning vs. sharding

Partitioning divides one logical table into smaller partitions according to a key or rule. In many databases, partitions live within one database cluster and can be managed or pruned independently. Sharding distributes partitions across separate database nodes and adds routing and distributed-systems concerns.

| | Partitioning | Sharding |
|---|---|---|
| Main purpose | Manage large tables and let queries prune irrelevant data | Distribute data/storage/write load across nodes |
| Placement | Often inside one database instance/cluster | Across multiple database servers/shards |
| Application routing | Usually transparent to the application | Often requires a shard router, middleware, or database layer |
| Cross-partition/shard query | Database can often combine partitions | Can require distributed query or scatter/gather across shards |

Partitioning is not automatically sharding. Some products can distribute partitions across nodes; use that product's terminology and architecture. A partition key should align with query filters and lifecycle operations, such as dropping old time-based partitions.

## Can joins work across shards?

Sometimes, but it depends on the database and sharding strategy. A join is easiest when both rows are on the same shard, often because related tables use a compatible shard key. Otherwise the system may have to query multiple shards and move/merge data, or the application must do the join.

| Case | Typical outcome |
|---|---|
| Both tables colocated by the same shard key | Local join on one shard |
| Query can route to a single shard | Ordinary local join is usually possible |
| Join keys map to different shards | Distributed join, scatter/gather, or application-side join; often more expensive |
| Shards are separate databases with no distributed query layer | Application queries each side and combines results, or data is remodeled/denormalized |

Design shard keys around important query patterns and colocate data that is frequently joined. Do not assume cross-shard joins are impossible or free; verify the product's support and execution plan.

## Does Redis use threads?

**Short answer:** Redis can use threads, but normal command execution is mostly single-threaded per server process. The event loop handles client requests sequentially; this keeps individual Redis commands atomic, but one slow/blocking command can delay other clients. Redis also uses background threads for selected I/O or persistence work, and supported versions can use I/O threads for socket read/write work. That does not mean arbitrary Redis commands execute in parallel.

| Question | Answer |
|---|---|
| Can multiple application threads use Redis? | Yes. Clients can connect concurrently; use the client library's supported connection/pool behavior. |
| Do Redis commands run in parallel on one instance? | Generally, command execution is serialized on the main thread. |
| Does Redis use any threads? | Yes, for selected background and I/O work; details depend on version/configuration. |
| How to scale command throughput? | Keep commands fast, pipeline to reduce network round trips, and use multiple shards/instances when appropriate. |
| Is one command atomic? | A command executes without another command interleaving on that server. A sequence of commands needs a transaction/script/other coordination when it must be indivisible. |

Redis transactions (`MULTI`/`EXEC`) queue and execute commands together without other clients' commands interleaving, but they do not provide SQL-style rollback of earlier commands when a command has a runtime error. `WATCH` enables optimistic check-and-set workflows. Use Lua/functions for server-side atomic logic when appropriate, and avoid long/blocking commands.

## MongoDB

MongoDB is a document database. It stores BSON documents in collections; a document can contain nested objects and arrays. Documents in a collection need not all have identical fields, but applications should still validate and evolve document shape deliberately.

```javascript
// mongosh: insert and query a document
db.orders.insertOne({
  _id: 1001,
  customerId: 42,
  status: "paid",
  items: [{ sku: "A7", quantity: 2, price: 12.50 }],
  createdAt: new Date()
});

db.orders.find({ customerId: 42, status: "paid" });

// Index for a common filter/sort pattern
db.orders.createIndex({ customerId: 1, createdAt: -1 });
```

### MongoDB data modeling

Choose embedding or references based on how data is read, updated, and grows:

| Pattern | Use when | Tradeoff |
|---|---|---|
| Embed related data | Data is read together, bounded in size, and updated together | Duplicated data can become stale; document growth needs limits |
| Reference another document | Data is shared, large, independently updated, or unbounded | Reads may need extra queries or `$lookup` |

MongoDB guarantees atomicity at the single-document level. Multi-document transactions are available, but add coordination cost; model related updates into one document when that fits the domain and access patterns.

### MongoDB aggregation

Aggregation pipelines pass documents through stages to filter, reshape, group, and calculate results.

```javascript
db.orders.aggregate([
  { $match: { status: "paid" } },
  { $unwind: "$items" },
  { $group: {
      _id: "$customerId",
      itemCount: { $sum: 1 },
      revenue: { $sum: { $multiply: ["$items.quantity", "$items.price"] } }
  } },
  { $sort: { revenue: -1 } }
]);
```

### MongoDB replication and sharding

| Feature | Purpose |
|---|---|
| Replica set | Multiple copies of the same data for availability and failover; a primary accepts writes and secondaries replicate |
| Sharding | Partitions data across shards to scale storage and throughput |
| Index | Speeds matching/sorting for selected query patterns; every extra index costs storage and write work |

Replication improves availability/read options; it is not the same as sharding, which distributes different portions of the dataset. Choose a shard key that distributes writes and supports common queries. A poor key can create hot shards or scatter/gather operations.

## Database backups and recovery

A backup is a restorable copy of data. Backup types are often grouped by **what is copied** (logical vs. physical) and **how much changed data is copied** (full, incremental, or differential). A database may use more than one method together.

| Backup type | What it contains | Typical use / tradeoff |
|---|---|---|
| Full | A complete copy at a point in time | Simple restore base; takes more time and storage |
| Incremental | Changes since the previous backup (often any backup type) | Smaller/faster backups; restore needs the full base and every incremental in order |
| Differential | Changes since the last full backup | Restore needs the full backup plus the latest differential; grows until the next full |
| Logical | Export of schema and rows as SQL or a database-native logical format | Move selected databases/tables or migrate versions; can be slower for very large datasets |
| Physical | Database files/pages and related physical state | Faster whole-instance recovery; usually tied to engine/version and requires consistency handling |
| Snapshot | Storage-level point-in-time copy | Fast when coordinated with the database; may need transaction-log/WAL backups for point-in-time recovery |
| Transaction log / WAL archive | Ordered record of changes since a base backup | Replay changes to a target time and reduce data loss between full backups |

Recovery commonly means restoring a valid base backup, applying incremental/differential backups if used, then replaying archived logs to the desired point. In PostgreSQL, point-in-time recovery (PITR) uses a base backup plus archived WAL; `pg_dump` is a logical backup and does not replace that physical/WAL process.

```sh
# Example logical backup and restore with PostgreSQL custom format
pg_dump -Fc -d appdb -f appdb.dump
createdb restored_appdb
pg_restore -d restored_appdb appdb.dump
```

| Recovery term | Meaning |
|---|---|
| RPO (Recovery Point Objective) | How much recent data the business can afford to lose |
| RTO (Recovery Time Objective) | How long the service can be unavailable while restoring |
| PITR (Point-in-Time Recovery) | Restore to a chosen time, such as just before an accidental deletion |
| Failover | Switch service to a standby/replica; helps availability but is not a substitute for backups |

Replication can copy accidental deletes or corruption, so retain independent backups. Test restores regularly, including permissions, encryption keys, and recovery steps; an untested backup is not a proven recovery plan.

## Drawbacks of non-relational databases

These are common tradeoffs, not universal limitations of every NoSQL product:

- Relationships and ad-hoc joins may be less convenient, so data modeling can depend more heavily on known access patterns.
- Flexible schemas can allow inconsistent documents unless the application or database validates them.
- Denormalized copies create update and consistency work.
- Cross-document transactions and constraints may be less natural, more limited, or more expensive than in a relational design, depending on the product.
- Query languages, transaction semantics, operational tooling, and portability differ widely across NoSQL families.
- A distributed architecture can add eventual consistency, routing, rebalancing, and debugging complexity.

Choose the model that makes the required invariants and access patterns easiest to implement and operate. NoSQL is not automatically faster or more scalable for every workload.

## Practical SQL scaling and isolation questions

### Coverage of the requested interview topics

| Topic | Existing foundation | Practical material to study |
|---|---|---|
| Indexing | Index commands, tree structures, clustered/non-clustered | Query-to-index workflow below; [Django indexing](Django_Flask.md#django-indexing-practical-interview-questions) |
| Transactions | ACID and transfer example | Inventory race, external side effects, retry boundaries below |
| Isolation | Four levels summarized | PostgreSQL-specific guarantees and write skew below |
| Replication | Previously brief scaling/MongoDB notes | Dedicated replication section below |
| Read replicas | Previously a brief scaling comparison | Freshness, routing, failover, Django usage below |
| Partitioning | Concept and comparison | Range partition SQL and decision criteria below |
| Sharding | Benefits, routing, joins | Shard-key choices, hot tenants, migration costs below |
| NoSQL | SQL comparison, MongoDB, Redis | Workload-based selection and deep follow-ups below |

### 1. How would you choose an index for a slow endpoint?

**Scenario:** show a tenant's latest paid orders. Start with the actual SQL, frequency, data volume/distribution, requested columns, and latency. Remove N+1 queries/unnecessary rows before assuming an index is the only issue.

```sql
SELECT id, created_at, total
FROM orders
WHERE tenant_id = 42 AND status = 'paid'
ORDER BY created_at DESC, id DESC
LIMIT 50;

-- Candidate for this workload; measure against existing indexes.
CREATE INDEX CONCURRENTLY idx_orders_tenant_status_recent
ON orders (tenant_id, status, created_at DESC, id DESC)
INCLUDE (total);

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, created_at, total
FROM orders
WHERE tenant_id = 42 AND status = 'paid'
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Equality filters lead this candidate; the trailing keys support the requested order. `INCLUDE` carries payload rather than additional search keys. An index-only scan also depends on visibility information, not merely covering columns. Concurrent creation is PostgreSQL-specific and must run outside a transaction block.

Compare before/after plans, actual vs. estimated row counts, buffers, sort work, and latency on representative data. A sequential scan can be correct for a small table or a query returning much of it. Check statistics and write overhead rather than forcing index scans. See [examining index usage](https://www.postgresql.org/docs/current/indexes-examine.html).

| Candidate | Useful when | Cost / trap |
|---|---|---|
| Single-column B-tree | Frequent selective equality/range filter | May still need extra sorting/filtering |
| Composite B-tree | Combined filter/order matches common access | Column order matters; extra size/write work |
| Partial index | Small, frequently queried subset | Query predicate must imply its condition |
| Expression index | Query filters an expression, e.g. `lower(email)` | Query expression must match planner requirements |
| GIN | Supported JSONB/array/full-text operators | Write/storage overhead; not a general sort index |
| BRIN | Very large physically correlated data, e.g. append-time | Lossy ranges with rechecks; weak for random distributions |

**Dig deeper:** why might `LIKE '%term%'` not use a normal B-tree? Why can an index on a boolean help for a rare subset but not the majority? Can one composite index replace two others for every query? How much does the index increase write latency and storage?

### 2. Why doesn't putting read-then-write code inside a transaction prevent overselling?

Two transactions can both read stock 1 before either writes. Atomicity alone does not enforce the business rule across concurrent transactions.

```sql
BEGIN;
UPDATE inventory
SET available = available - 1
WHERE product_id = 7 AND available > 0
RETURNING product_id;
-- If no row returned, abort the reservation path.
-- Insert the matching reservation only after successful decrement.
COMMIT;
```

For a more complex decision, lock the relevant rows with `SELECT ... FOR UPDATE`, validate, update, then commit promptly. A conditional update is simpler when the invariant fits one statement. Acquire multiple locks consistently. Retry an entire deadlocked/serialization-failed transaction with bounded attempts and fresh reads.

**Dig deeper:** transaction rollback cannot undo an email or external payment. Use stable idempotency keys, after-commit scheduling when loss is acceptable, or an outbox when delivery must survive crashes. A network failure during commit can leave the client uncertain whether it committed; resolve by operation identity instead of blindly repeating business effects.

### 3. What isolation level would you choose in PostgreSQL?

| PostgreSQL level | Read snapshot | Practical remaining issue |
|---|---|---|
| Read uncommitted | Behaves as read committed | No extra dirty-read behavior in PostgreSQL |
| Read committed | New snapshot per statement | Two reads may differ; multi-statement decisions can race |
| Repeatable read | Stable transaction snapshot | Prevents phantoms in PostgreSQL, but write skew remains possible |
| Serializable | Committed results equivalent to some serial execution | Applications must handle serialization failures |

```sql
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- Read invariant-related data and perform its updates here.
COMMIT; -- serialization failure can occur; retry the whole transaction
```

**Write-skew scenario:** two doctors each see two on-call doctors, then update different rows to go off call. Snapshot isolation can allow both changes. Protect the shared invariant through appropriate common locks/modeling or serializable isolation with retries. Do not generalize these exact guarantees to every engine. See [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html).

**Dig deeper:** row locks protect selected rows, not every future row matching an arbitrary predicate. How would you reproduce the anomaly with two sessions? Why must retry encompass the decision reads rather than only the failed update?

### 4. What is replication, and how is it different from sharding or backup?

Replication maintains copies of data; sharding distributes different subsets. A backup provides a recoverable historical copy—replicas can replay accidental deletes too.

| Replication choice | Advantage | Tradeoff |
|---|---|---|
| Asynchronous | Lower commit-path latency | Lag; failover can lose recently acknowledged writes |
| Synchronous | Required standby acknowledgements strengthen durability | Commit latency and availability depend on configured standbys |
| Physical | Replays low-level changes to maintain a standby | Closely tied to engine/version and whole-instance layout |
| Logical | Selected tables/change streams and integration flexibility | Schema/DDL and conflict handling require planning |

Synchronous acknowledgement is not automatically proof that a standby query can already see the row; acknowledgement/replay settings matter. Availability needs health detection, promotion, routing, and fencing of an old primary. Monitor lag and retained logs; a stalled replication slot can exhaust disk. See [PostgreSQL standby operation](https://www.postgresql.org/docs/current/warm-standby.html).

**Dig deeper:** define RPO (tolerable data loss) and RTO (time to restore service). How do you prevent split brain? How do applications reconnect after promotion? Replication and tested backups address different failures.

### 5. When should you add read replicas? What breaks after a write?

**Scenario:** order creation commits on the primary, but the next GET uses a lagging replica and returns 404. This is a read-after-write consistency problem, not proof that the write failed.

| Read | Suggested route | Reason |
|---|---|---|
| Public catalog / lag-tolerant reports | Replica | Freshness tolerance allows read offload |
| Immediate read after checkout | Primary, or verified replay-aware routing | Must observe committed result |
| Inventory allocation / authorization-critical current state | Authoritative primary transaction | Staleness can break correctness |
| Heavy analytics | Dedicated replica/warehouse as appropriate | Protect OLTP; measure impact and lag |

Primary stickiness for a fixed time reduces failures but does not guarantee freshness under arbitrary lag. Replay-position-aware routing can wait for the relevant log position, with a deadline/fallback. Read replicas generally do not increase the primary's write capacity.

Django routing example, assuming `default` is the primary and `replica` is configured:

```python
order = Order.objects.using("default").create(customer_id=42)
fresh = Order.objects.using("default").get(pk=order.pk)
report = Order.objects.using("replica").filter(status="paid")[:100]
```

Routers can centralize policy, but Django does not automatically solve replication lag or cross-database transactions/relations. See [Django multiple databases](https://docs.djangoproject.com/en/5.2/topics/db/multi-db/).

**Dig deeper:** what happens when a replica is promoted? How do you remove an unhealthy replica from routing? Could long reports delay replay or be cancelled on a standby?

### 6. When should you choose indexing, partitioning, replicas, or sharding?

| Observed problem | First candidate | Why / limitation |
|---|---|---|
| Selective query scans/sorts too much | Query/schema/index tuning | Avoid distributing an inefficient query |
| One large time-series table; retention deletes costly | Time-based partitioning | Lifecycle management and pruning; not independent node capacity |
| Reads saturate primary; staleness acceptable | Read replicas, possibly caching | Adds read capacity; leaves write bottleneck |
| Temporary resource shortage within one-node headroom | Vertical scaling plus tuning | Simpler; hardware/cost ceiling remains |
| Sustained writes/storage exceed one node after tuning | Sharding/distributed SQL evaluation | Distributes capacity; operational and consistency costs |
| One hot account or tenant dominates | Isolate/split that workload deliberately | More random shards may leave the same hot key bottleneck |

There is no universal row-count threshold. Base the choice on measured CPU/I/O/storage, growth, maintenance time, freshness, and operational constraints.

### 7. Show partitioning syntax and explain when it helps

```sql
CREATE TABLE events (
    tenant_id BIGINT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    event_id BIGINT NOT NULL,
    payload JSONB,
    PRIMARY KEY (occurred_at, event_id)
) PARTITION BY RANGE (occurred_at);

CREATE TABLE events_2026_10 PARTITION OF events
FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');

CREATE INDEX idx_events_tenant_time ON events (tenant_id, occurred_at);

EXPLAIN SELECT event_id FROM events
WHERE occurred_at >= TIMESTAMPTZ '2026-10-01 00:00:00+00'
  AND occurred_at <  TIMESTAMPTZ '2026-11-01 00:00:00+00';
```

Time-filtered queries can prune irrelevant partitions; retention can remove old partitions without deleting each row. Automate future partition creation and decide what happens to out-of-range inserts. Excess partition counts increase planning/maintenance overhead. In PostgreSQL, partitioned-table unique/primary constraints must include the partition key; this example does not enforce global uniqueness of `event_id` alone. See [table partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html).

**Dig deeper:** no time predicate means little/no time pruning. Indexes still matter inside partitions. A date partition within one instance still shares that instance's CPU/I/O ceiling. A shard can itself contain time partitions.

### 8. What is the advantage of sharding, and what makes it hard?

**Interview answer:** sharding spreads different rows across independently provisioned nodes, increasing aggregate storage and write throughput when work routes well. It can isolate tenant workloads and failure impact. It costs routing, rebalancing, cross-shard query/transaction complexity, and coordinated operations. More shards do not automatically give redundancy; each shard needs its own durability/availability plan.

| Shard-key approach | Advantage | Risk |
|---|---|---|
| Tenant ID | Tenant-local queries/joins and isolation | Huge tenants cause imbalance; need split/dedicated-shard plan |
| Hash of a high-cardinality key | More even distribution | Range scans and unrelated lookups can fan out |
| Time/range | Efficient range routing | Monotonic writes can overload the newest shard |
| Directory-based tenant placement | Move/select placements explicitly | Routing metadata must be reliable and versioned |

```python
# Interview illustration only: fixed-modulo routing is hard to resize safely.
shard_id = stable_hash(tenant_id) % shard_count
# All tenant-related tables must follow a compatible placement policy.
```

Do not use Python's process-randomized `hash(str_key)` as a cross-process stable routing hash. Production systems need persistent placement metadata or a deliberate hash/range scheme. Changing `shard_count` in this illustration remaps many keys.

**Dig deeper:** a query lacking the shard key may hit every shard. Global pagination/top-K needs merge logic; uniqueness and foreign keys may be only shard-local. Resharding needs snapshot/backfill, change capture, consistency verification, controlled cutover, and recovery from partial migration. Cross-shard workflows need product-supported distributed transactions or explicit compensating/idempotent workflows.

### 9. When would you choose NoSQL for this workload?

| Workload | Candidate | What to defend |
|---|---|---|
| Payments/orders with relationships and constraints | Relational DB | Transaction boundaries, indexes, growth strategy |
| Bounded aggregate documents read together | Document DB | Embedding limits, indexes, duplication/update policy |
| Cache, rate limit counters, ephemeral lookups | Redis | Persistence policy, expiry, memory, failure fallback |
| High-volume key/range access across nodes | Wide-column DB | Partition-key design, query restrictions, consistency settings |
| Rich multi-hop relationship traversal | Graph DB | Traversal patterns and operational/query cost |

NoSQL is not “no schema,” “no indexing,” or “no transactions.” Decide from the product's actual guarantees. SQL can store JSON; document databases still require schema evolution and query/index design. Flexible storage does not fix an unknown access pattern.

**Dig deeper:** distinguish replication lag from transaction isolation. CAP concerns the consistency/availability choice during a network partition; it does not mean casually choosing any two of three properties for every request. If introducing a second database, who owns synchronization, reconciliation, backups, and observability?

### 10. How should I answer “Have you worked with indexing?”

**First audit your experience:** did you add `db_index`, `Meta.indexes`, a unique constraint, a manual SQL index, inspect a plan, or diagnose a query using an existing index? Django-created indexes are real database indexes, but using an automatically indexed primary key is different from personally designing and validating an index.

Use the version that matches your work:

- **Designed and measured one:** “I optimized [real endpoint/query]. It filtered by [columns] and ordered by [columns]. I added [actual index] through [migration/SQL], compared [actual plan/latency], and checked [write/storage/deployment cost].” Use only measured numbers you actually have.
- **Used Django indexes, limited tuning:** “I have defined/used database indexes through Django's models and migrations. My experience with production execution-plan tuning is limited. I can explain the query pattern and why that index was chosen.” Adjust “defined” if you only used them.
- **No direct experience yet:** “I haven't owned production index tuning yet. I understand how Django declares indexes and how to validate them, and I've practiced it locally.” Say the practice part only after doing it.

**Practice exercise:** seed representative local data, capture the ORM SQL/plan, introduce a composite index for a real filter/order, compare with the same data and query, then measure insert/update overhead. A tiny empty table is not meaningful performance evidence.

Prepare for: Why those columns? Why that order? Why not every column? How did you know it was used? Did it slow writes? How did you deploy it without unacceptable blocking? Could it replace an existing index?

## References

- [PostgreSQL window functions](https://www.postgresql.org/docs/current/tutorial-window.html)
- [PostgreSQL indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL `CREATE INDEX`](https://www.postgresql.org/docs/current/sql-createindex.html)
- [PostgreSQL `EXPLAIN`](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL constraints and foreign keys](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [PostgreSQL aggregate functions](https://www.postgresql.org/docs/current/functions-aggregate.html)
- [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- [PostgreSQL MVCC](https://www.postgresql.org/docs/current/mvcc.html)
- [PostgreSQL user-defined functions](https://www.postgresql.org/docs/current/xfunc.html)
- [PostgreSQL `CREATE PROCEDURE`](https://www.postgresql.org/docs/current/sql-createprocedure.html)
- [PostgreSQL triggers](https://www.postgresql.org/docs/current/triggers.html)
- [PostgreSQL index types](https://www.postgresql.org/docs/current/indexes-types.html)
- [PostgreSQL table partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [PostgreSQL backup and restore](https://www.postgresql.org/docs/current/backup.html)
- [PostgreSQL continuous archiving and point-in-time recovery](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [PostgreSQL `CLUSTER`](https://www.postgresql.org/docs/current/sql-cluster.html)
- [MySQL InnoDB clustered and secondary indexes](https://dev.mysql.com/doc/refman/9.7/en/innodb-index-types.html)
- [SQL Server clustered and nonclustered indexes](https://learn.microsoft.com/en-us/sql/relational-databases/indexes/clustered-and-nonclustered-indexes-described)
- [MongoDB data modeling](https://www.mongodb.com/docs/manual/data-modeling/)
- [MongoDB indexes](https://www.mongodb.com/docs/manual/indexes/)
- [MongoDB aggregation](https://www.mongodb.com/docs/manual/aggregation/)
- [MongoDB transactions](https://www.mongodb.com/docs/manual/core/transactions/)
- [MongoDB sharding](https://www.mongodb.com/docs/manual/sharding/)
- [Redis latency and threading model](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/)
- [Redis transactions](https://redis.io/docs/latest/develop/using-commands/transactions/)
- [Redis pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/)

- [PostgreSQL standby replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [PostgreSQL examining index usage](https://www.postgresql.org/docs/current/indexes-examine.html)
- [Django model indexes](https://docs.djangoproject.com/en/5.2/ref/models/indexes/)
- [Django multiple databases](https://docs.djangoproject.com/en/5.2/topics/db/multi-db/)
