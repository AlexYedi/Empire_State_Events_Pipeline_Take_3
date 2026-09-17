<!-- Public-safe copy (repo is PUBLIC): 'In Alex's stack' live-DB notes stripped. Canonical private version: Notion + claude.ai artifact. Linear YED-167. -->
# Postgres for the Agentic Era — A Working Glossary

*Built from Ryan Booz's talk "Postgres Tuning in the Age of AI: Context Is Everything" (pganalyze; an every-other-month NYC Postgres meetup hosted by Mila Zhou at AWS, 2026-09-16), the pre-event research brief, the published posts and carousels, (Live-database notes are omitted from this public repo copy; they live in the private Notion/web versions.) Every version number and date below was checked against postgresql.org release notes or the vendor's own docs; anything that could not be checked is marked "(unverified)" or omitted.*

## How to use this

Read "The 60-second mental model" first; it strings the core terms into one story so the individual entries have somewhere to sit. Then use the Core section as a reference: each entry stands alone, ends with where Ryan Booz used the term in the room (timestamp = start of the transcript paragraph, since the ElevenLabs transcript groups long stretches of speech into single paragraphs),  The long tail, tools list and corrections are for lookup, not reading.

## Table of contents

1. [The 60-second mental model](#the-60-second-mental-model)
2. [Core terms](#core-terms) (26, alphabetical)
   auto_explain · Buffers and pages · Connection pooling · Correlated subquery · CREATE INDEX CONCURRENTLY · CTE and MATERIALIZED · Cumulative statistics system · Database branching and thin clones · EXPLAIN / EXPLAIN ANALYZE / BUFFERS · Extensions · GUC (configuration) · Index and index types · Join algorithms · log_min_duration_statement · MCP for databases · Parameter-sensitive plans · pg_stat_statements · pgvector · Planner cost · Query planner · Row-Level Security · Sequential scan vs index scan · Statistics and ANALYZE · track_io_timing · VACUUM, autovacuum, MVCC · work_mem and disk spill
3. [Long tail](#long-tail) — SQL and query shapes · Settings and logging · Diagnosis and tuning method · Agent access, safety and test data · Security · Community
4. [Tools and companies](#tools-and-companies)
5. [Corrections and unresolved](#corrections-and-unresolved)
6. [Sources](#sources)

---

## The 60-second mental model

You write SQL, which is **declarative**: you say what rows you want, not how to get them. The **query planner** works out the how. It is a GPS: it considers possible routes (a **sequential scan** of the whole table, an **index scan**, one of three **join algorithms**) and picks the one with the lowest estimated **cost**. Its map is the **statistics** that **ANALYZE** collects about each table: how many rows, which values are common, how values spread. Stale or thin statistics mean a confident wrong route, exactly like a GPS with an old map.

The chosen route is the **plan**. **EXPLAIN** prints the intended route; **EXPLAIN ANALYZE** drives it and reports what actually happened: real row counts, real times, and (**BUFFERS**) how many 8 kB **pages** had to be touched to answer the query. Pages are the honest unit of work. A query that reads 193 million pages is doing 193 million pages of work no matter what the clock says.

Some plan shapes are traps: a **correlated subquery** that re-runs for every outer row, a **nested loop** chosen because the statistics said "only a few rows", a sort that exceeds **work_mem** and **spills to disk**. Some fixes are traps too: a **CREATE INDEX** without **CONCURRENTLY** locks a production table; a **CTE** without **MATERIALIZED** may be inlined and recomputed. Meanwhile **VACUUM** cleans up the dead row versions that Postgres's **MVCC** design leaves behind, and refreshes the map.

None of this is visible unless you turn the lights on. **pg_stat_statements** keeps a running ledger of every query shape (part of the **cumulative statistics system**); **auto_explain** captures the plan of any slow query at the moment it ran; **log_min_duration_statement** logs the text; **track_io_timing** separates disk wait from CPU. These are **GUCs**, settings, and most are off by default on most providers.

That telemetry is the context an **AI agent** needs. Given raw SQL alone, a model guesses ("add an index"). Given the plan, the statistics, the schema and the history, the models Ryan Booz tested found the real problem ten times out of ten. **MCP** is the plug that hands an agent that context, and the safety questions are about what the plug exposes (read-only? which project? raw parameters?) and where the agent tests its ideas (a **branch** or **thin clone**, never production). **Row-Level Security**, **connection pooling** and **extensions** such as **pgvector** are the parts of Postgres that shape what an agent-facing database on Supabase actually looks like.

---

## Core terms

### auto_explain

**What it is.** A built-in Postgres module that automatically writes the execution plan of any query slower than a threshold into the server log. The pre-event post framed it as a dashcam that switches itself on: you do not have to be watching when the slow query happens; the recording is waiting for you afterwards.

**How it works.** The module is loaded through `shared_preload_libraries` (server-wide), `session_preload_libraries`, or `LOAD 'auto_explain'` for one session. Its main knob is `auto_explain.log_min_duration` in milliseconds (default `-1`, off; `0` logs everything). Companion settings decide how rich the captured plan is: `log_analyze` (actual rows and times, not just estimates), `log_buffers`, `log_format` (`text`, `json`, `xml`, `yaml`), `log_nested_statements` (statements inside functions), `log_timing`, `log_verbose`, and `sample_rate` (fraction of statements to explain). The docs warn that `log_analyze` turns on per-node timing for every statement regardless of threshold, so disable `log_timing` if the overhead worries you.

**History.** Added as a contrib module in PostgreSQL 8.4 (July 1, 2009), alongside pg_stat_statements, by Itagaki Takahiro and Tom Lane.

**Value and use cases.** It answers "what did the plan look like last night when it blew up?" Re-running the query in the morning often shows a different, fast plan; without the captured plan you cannot see that the plan flipped. Ryan Booz described exactly that customer call, at the airport, the morning of the talk.

**Limitations and gotchas.** It writes to the log, so you need something that reads the log (pganalyze, pgWatch, your own parser). JSON is easier to parse but more verbose. A threshold of 0 or 50 ms buries the signal; Ryan Booz's starting point is about one second. It captures plans only for statements that cross the threshold, so you do not get a plan for the query that is fast individually but called 12,000 times.

**Agentic-era relevance.** An agent asked "why was this slow?" needs the plan from the moment it was slow. auto_explain is the cheapest way to make that history exist. Ryan Booz's rule of thumb: in years of customers, the overhead has never been the actual problem; withholding the information has.

**In the room.** 12:08 (introduced as the first "turn this on" item; explained), 15:43 (`auto_explain.log_min_duration` versus `log_min_duration_statement`: one logs plans, the other logs text; explained), 18:03 (sampled ledger versus captured instances; explained), 21:43 (JSON recommended). Ryan Booz explained it fully.

**Learn more.** https://www.postgresql.org/docs/current/auto-explain.html

---

### Buffers and pages (shared hit / read / written)

**What it is.** Postgres stores every table and index as a sequence of fixed 8 kB blocks called pages. A buffer is a page held in memory. `EXPLAIN (BUFFERS)` counts how many pages a query touched. Ryan Booz's analogy: if the data were a printed book, buffers are the pages you had to open to answer the question, whether they were already on your desk (memory) or had to be fetched from the shelf (disk).

**How it works.** The buffer line under each plan node reports `shared hit` (page was already in Postgres's shared buffer cache), `shared read` (page had to be read from the operating system or disk), `shared dirtied` (page modified in memory) and `shared written` (page written out), plus `temp read/written` for work files created by sorts and hashes that overflow memory. Counts are cumulative up the plan tree: a parent node's buffers include its children's. In text output the number is per-loop; multiply by `loops` to get the total.

**History.** The `BUFFERS` option arrived in PostgreSQL 9.0 (September 20, 2010, Itagaki Takahiro), alongside JSON/XML/YAML output. It became automatic with `EXPLAIN ANALYZE` in PostgreSQL 18 (September 25, 2025; Guillaume Lelarge, David Rowley). Ryan Booz said "as of Postgres fifteen"; the release notes say 18.

**Value and use cases.** Buffers are the honest measure of work. Time varies with cache state, machine load and what else is running; page counts do not. A query touching 193 million pages (roughly 1.5 TB at 8 kB) on a database that does not hold that much data is a shape problem you can spot in seconds: something is looping. Ryan Booz's first move on any plan is to find where the buffers are, because that is where the work is.

**Limitations and gotchas.** A high `shared hit` count is still work: memory reads are cheap per page, not free. `written` under a read-only query usually means a sort or hash spilled. Buffer counts need `EXPLAIN ANALYZE` (real execution) to be meaningful; plain `EXPLAIN` estimates cost, not pages.

**Agentic-era relevance.** Page counts are exactly what an agent can reason about without knowing your hardware. "This node reads 1,000× more pages than the table contains" is a machine-checkable claim; "this feels slow" is not.

**In the room.** 25:22 block ("we always run this with explain, analyze, and buffers"; the printed-pages analogy; 193 million pages for one query; explained), 40:03 block (shared hit / read / written defined live; "if you have stuff being written to disk, that's particularly bad"; explained). Fully explained.

**Learn more.** https://www.postgresql.org/docs/current/using-explain.html

---

### Connection pooling (PgBouncer, Supavisor)

**What it is.** A pooler sits between clients and Postgres, keeping a small number of real database connections open and lending them out to many short-lived clients. Think of a coat check: hundreds of guests, a few dozen hooks, nobody keeps a hook all night.

**How it works.** Each Postgres connection is an operating-system process with its own memory, so connections are expensive and `max_connections` is finite. PgBouncer's `pool_mode` decides when a server connection is returned: `session` (when the client disconnects; the default), `transaction` (after each transaction), or `statement` (after each query). Transaction mode gives the highest reuse but breaks anything that assumes session state persists between transactions: prepared statements, cursors, advisory locks, `SET` commands.

**History.** PgBouncer was written by Marko Kreen at Skype and announced on the PostgreSQL mailing lists on March 13, 2007. Supabase built Supavisor, an Elixir pooler designed for cloud scale, and announced Supavisor 1.0 on December 13, 2023, migrating all projects from PgBouncer connection strings by January 15, 2024.

**Value and use cases.** Serverless and edge functions open many short connections; a pooler in transaction mode keeps them from exhausting the database. Supabase exposes Supavisor in session mode (port 5432) and transaction mode (port 6543); paid plans also get a dedicated pooler, which runs on the database machine and uses PgBouncer for routing.

**Limitations and gotchas.** Transaction mode does not support prepared statements; disable them in the client library or use session mode. A pooler hides the real connection count from you, so per-role usage in pg_stat_statements can look odd (the `pgbouncer` role shows up as its own user).

**Agentic-era relevance.** Agents are exactly the kind of client that opens many short connections in bursts. The pre-event brief flagged "connection exhaustion under agent concurrency" as a hypothesised failure; the pooler is the standard defence. It is also the place to set per-client limits, which matters when an unsupervised agent loop is "relentless".

**In the room.** Not discussed. Comes from the pre-event research (Xata's pooler that "scales to zero") and Alex's stack.

**Learn more.** https://supabase.com/docs/guides/database/connecting-to-postgres · https://www.pgbouncer.org/config.html

---

### Correlated subquery (and subplan)

**What it is.** A subquery that refers to a column of the outer query, so it must be re-evaluated for every outer row. In the plan it shows up as a **SubPlan** node with a large `loops` count. Ryan Booz's slow demo query had one, and it was 98% of the runtime.

**How it works.** Postgres can often rewrite an uncorrelated subquery into a join or a one-time InitPlan. A correlated one, `WHERE c.customer_id = outer.customer_id`, depends on the current outer row, so the executor runs it once per row. If the outer query returns 200 rows and the subquery takes 0.7 s, you have spent 140 s in that one node. The `actual time` shown is per loop; the total is time × loops.

**History.** Correlated subqueries are standard SQL and have been in Postgres since its SQL support in Postgres95 (1995). The planner's ability to flatten some subqueries into joins has improved over releases; the version-by-version detail is not needed here.

**Value and use cases.** The shape itself is legitimate ("for each customer, compare their spend to everyone who rented similar films"). The problem is when the inner query does heavy work that could be done once. The fix is usually to pull the subquery out, compute its result set once (a CTE with `MATERIALIZED`, a temp table, or a join on an aggregated derived table), then join to it.

**Limitations and gotchas.** ORMs generate this shape without telling you. The plan is the only reliable way to see it; the SQL text alone hides it, which is why Ryan Booz's audience-guess exercise at 02:35 produced four or five wrong candidates.

**Agentic-era relevance.** With only the query text, models suggested indexes 7 times out of 10. With the EXPLAIN plan, every model tested (Sonnet, Opus, ChatGPT) found the correlated subquery 10 out of 10 times. This is the talk's central evidence that context, not model choice, decides the outcome.

**In the room.** 25:20–25:22 (audience supplied the word "subquery"; Ryan Booz named it "the correlated subquery"), 25:22 block (SubPlan carries 193 million of the buffers; "ninety-eight percent of the time the work is done right there"), 40:03 block ("the correlation means that this C value is referring to the outer customer"; the MATERIALIZED CTE rewrite), 47:49 block (found 10/10 with a plan). Explained thoroughly.

**Learn more.** https://www.postgresql.org/docs/current/using-explain.html · https://www.postgresql.org/docs/current/queries-with.html

---

### CREATE INDEX CONCURRENTLY (and locking)

**What it is.** The option that builds an index without blocking writes to the table. Ryan Booz's point at 08:28: an AI's very first recommendation ("add an index") is dangerous not because it is wrong but because it omits this word.

**How it works.** A normal `CREATE INDEX` takes a lock that blocks `INSERT`, `UPDATE` and `DELETE` for the whole build (reads continue). On a huge table that is an outage. `CONCURRENTLY` instead does two table scans in two transactions, waits for in-flight transactions to finish before and after, and never blocks writes. It takes longer and cannot run inside a transaction block. If it fails (deadlock, uniqueness violation) it leaves behind an `INVALID` index that costs write overhead but is never used for queries; drop it or `REINDEX INDEX CONCURRENTLY`.

**History.** Added in PostgreSQL 8.2 (December 5, 2006, Greg Stark and Tom Lane). Azure's autonomous tuning, notably, emits every recommendation as `CREATE INDEX CONCURRENTLY …`.

**Value and use cases.** Any index on a table that is taking writes in production. It is the difference between "we added an index at 2 pm" and "the app was down at 2 pm."

**Limitations and gotchas.** Only one concurrent build per table at a time. Migration tools that wrap DDL in a transaction will reject it. It still consumes I/O and CPU while it runs, so it is not free on a stressed primary, just non-blocking.

**Agentic-era relevance.** This is the canonical example of a plausible fix that a model produces without knowing it is on a live system. Every vendor in the pre-event research gates DDL: Supabase's advisors emit findings, not DDL; Xata gates writes behind explicit flags; pganalyze's MCP server does not execute DDL at all. "No vendor lets an AI apply DDL to prod unattended" was the pre-event brief's summary.

**In the room.** 08:28 ("no query concurrently in any of this, right? … I go to do that, I lock my database … could cause mayhem in a production environment"). Explained.

**Learn more.** https://www.postgresql.org/docs/current/sql-createindex.html

---

### CTE (WITH clause) and MATERIALIZED

**What it is.** A Common Table Expression names a subquery at the top of a statement (`WITH matched AS (…) SELECT … FROM matched`). It exists only for that statement. It makes SQL readable, and, with `MATERIALIZED`, it forces Postgres to compute the named result once and reuse it.

**How it works.** By default, a non-recursive, side-effect-free CTE that is referenced exactly once is inlined (folded) into the parent query, as if you had written a subquery, so the planner can push filters into it and use indexes. A CTE referenced more than once, or a recursive or data-modifying one, is materialized: computed once into a temporary result set. `AS MATERIALIZED` forces the fence; `AS NOT MATERIALIZED` forces inlining even when referenced twice.

**History.** CTEs and `WITH RECURSIVE` arrived in PostgreSQL 8.4 (July 1, 2009). Until PostgreSQL 12 (October 3, 2019) every CTE was an optimization fence, always materialized. PG 12 made inlining the default for single-reference CTEs and added the `MATERIALIZED` / `NOT MATERIALIZED` keywords. Ryan Booz called 12 "this apocalypse" because plans that had silently relied on the fence changed overnight.

**Value and use cases.** Ryan Booz's fix for the correlated subquery: compute "customers who rented a film whose overview contains 'love' in the last 18 months" once as a materialized CTE, then join to it. Buffers fell from 193 million to about one million, and runtime from up to 173 s to well under a second, consistently across search terms.

**Limitations and gotchas.** A materialized CTE can become a very large in-memory set; if it exceeds `work_mem` it spills. Ryan Booz called forcing it "a hack … a very reputable and good hack, if you know what you're doing." Since PG 12, an old query that assumed the fence may need `MATERIALIZED` added back.

**Agentic-era relevance.** Every model Ryan Booz tested found the correlated subquery once it saw the plan, and in the MCP run the agent reached the same rewrite. Ryan Booz attributes models' Postgres fluency to the open-source code and comments they have read (a stated belief, unsourced). The gotcha for agents is version awareness: the same `WITH` behaves differently before and after PG 12.

**In the room.** 40:03 ("CTE stands for common table expression … Postgres didn't do that until version twelve … you can force a materialized view. This is a hack"). Explained, including the history.

**Learn more.** https://www.postgresql.org/docs/current/queries-with.html · https://www.postgresql.org/docs/release/12.0/

---

### Cumulative statistics system (pg_stat_* views)

**What it is.** Postgres's built-in activity counters: the `pg_stat_*` views that accumulate table scans, rows fetched, I/O, vacuum activity and more since the last reset. Ryan Booz's phrase: "pg_stat something, pg_stat_statements, pg_stat_tables, pg_stat over and over." It is an odometer, not a speedometer.

**How it works.** Each backend process counts locally and flushes to shared memory at least every second. Views such as `pg_stat_user_tables` (seq_scan, idx_scan, n_dead_tup, last_autoanalyze), `pg_stat_database`, `pg_stat_io` (reads, writes, hits, evictions by backend type) and `pg_stat_activity` (live sessions; dynamic, not cumulative) read those counters. Counters persist across clean shutdowns and reset on a crash or `pg_stat_reset()`. Because they are cumulative, a big number tells you nothing about *when* the work happened; you must sample and difference over time, which is what monitoring tools do.

**History.** The stats collector existed as a separate process that received UDP packets for most of Postgres's history. PostgreSQL 15 (October 13, 2022) moved the system into shared memory and removed the collector process (Kyotaro Horiguchi, Andres Freund, Melanie Plageman). `pg_stat_io` arrived in PostgreSQL 16 (September 14, 2023); PG 18 added byte counts and WAL rows to it.

**Value and use cases.** Table-level questions: is this table sequentially scanned a thousand times a day? Are dead tuples piling up? When was it last analyzed? It is also how autovacuum decides what to do (`track_counts` is on by default "because the autovacuum daemon needs the collected information").

**Limitations and gotchas.** Cumulative since reset, so `seq_scan = 1231` could be one bad day or six quiet weeks. Reading requires either a sampling tool or your own snapshot-and-diff. Ryan Booz: "You need to use a tool because otherwise you're gonna have to build a sampler, and no one wants to do that."

**Agentic-era relevance.** This is what "telemetry as agent-readable context" is made of. Ryan Booz's agent noticed "something messed up with vacuum" on the demo database purely from these stats, something the speaker did not know. The pganalyze MCP server exposes sampled versions of these views instead of a live connection.

**In the room.** 18:03 ("this is part of the cumulative statistics system in Postgres … you have no idea when you query it right now, is all that work now or did it happen eight days ago"). Explained.

**Learn more.** https://www.postgresql.org/docs/current/monitoring-stats.html

---

### Database branching and thin clones

**What it is.** A way to get an isolated, writable copy of a production database in seconds without copying the data. Git branching for data: the branch shares storage with its parent until something changes, and only the changes are stored (copy-on-write).

**How it works.** Neon branches point at already-stored pages; writes are saved as deltas; a branch of a terabyte takes about a second and costs nothing until written. Postgres.ai's Database Lab Engine (DBLab) does the same on your own infrastructure using ZFS or LVM snapshots; a 10 TiB clone in under 2 seconds. Amazon Aurora "fast clone" uses a copy-on-write protocol at the storage layer and stays inside your VPC. Xata's branches are the unit its MCP server scopes an agent to: create a branch for one agent run, delete it on the way out.

**History.** Aurora cloning, Neon branching (public launch December 2022) and DBLab (Apache-2.0, PostgresAI) all predate the agent wave; the pre-event brief's "five generations" places branch-scoped agent access in the fifth. Ryan Booz said pganalyze is working on letting its MCP server spin up a clone of a customer's database to test rewrites off-prod.

**Value and use cases.** Testing a rewrite, an index, or a migration against real data distribution, at real size, without touching production. The audience question at 61:58 ("I can't run the query against prod 'cause prod's already stressed") is the universal version of the problem.

**Limitations and gotchas.** A clone is a snapshot; production keeps moving. A clone carries production PII, so pair it with anonymization (Dalibo's PostgreSQL Anonymizer, Tonic) or subsetting. On managed platforms, cloning the compute is still a cost. Ryan Booz's warning: an agent that tested on a dev database "wasn't anything like prod, and it would have never given you that recommendation if it had known that."

**Agentic-era relevance.** The bounded environment is the precondition for letting an agent iterate at all. Read-only access lets it look; a branch lets it try. This is the design Xata converged on after archiving its stand-alone agent.

**In the room.** 63:58–64:04 (Aurora clone: "it will do the snapshot, restore the clone … still in your VPC"; "Neon, Databricks, Postgres AI … branching at a moment in time"). Partly explained.

**Learn more.** https://neon.com/docs/introduction/branching · https://postgres.ai/docs/database-lab · https://xata.io/blog/introducing-the-xata-mcp-server

---

### EXPLAIN / EXPLAIN ANALYZE / BUFFERS

**What it is.** `EXPLAIN` prints the plan the planner intends to use for a statement, with estimated costs and row counts. `EXPLAIN ANALYZE` executes the statement and adds what actually happened. The pre-event post's version: EXPLAIN is the planned route, EXPLAIN ANALYZE is the dashcam of the drive.

**How it works.** The output is a tree of nodes (Seq Scan, Index Scan, Hash Join, Sort, SubPlan…). Each node carries `cost=startup..total rows=N width=W`. With `ANALYZE` each node also gets `actual time=first..last rows=N loops=L`; the time and rows are per loop, so multiply by `loops` to get totals. `BUFFERS` adds page counts per node. `FORMAT JSON` produces machine-readable output. Because `ANALYZE` really runs the statement, wrap data-modifying statements in `BEGIN; … ROLLBACK;`.

**History.** `EXPLAIN ANALYZE` arrived in PostgreSQL 7.2 (February 4, 2002, Martijn van Oosterhout). JSON/XML/YAML formats and the `BUFFERS` option came in 9.0 (September 20, 2010). PG 17 (September 26, 2024) added `SERIALIZE` and `MEMORY`. PG 18 (September 25, 2025) made `BUFFERS` automatic with `ANALYZE`, reported per-index lookup counts, and started printing fractional row counts. Ryan Booz said 15 for the buffers default; it is 18.

**Value and use cases.** Without the plan you are guessing. Ryan Booz asked the room what was slow in the demo query; the SQL suggested four or five candidates; the plan pointed at one node with 98% of the time. The plan also shows whether the planner's estimate matched reality (estimated 200 rows, actual 2.5 million is a statistics problem, not a query problem).

**Limitations and gotchas.** `EXPLAIN ANALYZE` on a 150-second query takes 150 seconds; Ryan Booz declined to run it live. Timing overhead is real on systems with slow clocks. `LIMIT` stops execution early, so actual rows can be far below estimates without anything being wrong. Cost units are not milliseconds.

**Agentic-era relevance.** The plan is the single piece of context that changed model behaviour most in Ryan Booz's scripted trials: with it, the correlated subquery was found 10/10 times. Retained plans (auto_explain, pganalyze's 7-day plan history) let an agent compare the worst and best plans for one query ID and reason about why they differ.

**In the room.** 22:54 (audience: "So what is a plan?"), 22:56 (answer deferred, then delivered), 25:22 block ("This tells you exactly what the query the engine did … SQL is a declarative language"; the always-ANALYZE-and-BUFFERS habit; per-loop time). Fully explained.

**Learn more.** https://www.postgresql.org/docs/current/sql-explain.html · https://www.postgresql.org/docs/current/using-explain.html

---

### Extensions

**What it is.** Packaged add-ons that install into a database with `CREATE EXTENSION name`, bundling functions, types, operators and index methods as one manageable unit. Postgres's plug-in system: pgvector, pg_trgm, pg_stat_statements, PostGIS and pgaudit are all extensions.

**How it works.** An extension ships a control file and versioned SQL scripts; `CREATE EXTENSION` runs the script and records the objects as belonging to the extension, so `pg_dump` emits one line instead of hundreds of objects and `ALTER EXTENSION … UPDATE` upgrades in place. Some extensions also need a shared library preloaded at server start via `shared_preload_libraries` (pg_stat_statements, auto_explain, pgaudit), which requires a restart; others (pgvector, pg_trgm) load on demand.

**History.** The extension mechanism (`CREATE/ALTER/DROP EXTENSION`) arrived in PostgreSQL 9.1 (September 12, 2011, Dimitri Fontaine and Tom Lane); all contrib modules moved to it at the same time.

**Value and use cases.** Extensions are why Postgres can be a vector store, a time-series database (TimescaleDB), a queue (pgmq) or a cron scheduler (pg_cron) without forking the core. Managed providers curate an allow-list; Supabase lists what is available and lets you enable it from the dashboard.

**Limitations and gotchas.** Installing into the `public` schema exposes an extension's functions through APIs that expose `public` (Supabase flags this as `extension_in_public`). Preloaded extensions consume shared memory whether or not you use them. Version pinning is the provider's, not yours: you get the version the platform build ships.

**Agentic-era relevance.** The agent-relevant capabilities (pgvector, pg_trgm for fuzzy match, pg_stat_statements for telemetry, hypopg for hypothetical indexes) are all extensions, and an agent needs to know which are installed before it recommends them. Ryan Booz's early LLM run suggested a trigram index without knowing whether pg_trgm existed.

**In the room.** Not defined as a concept, but the talk's instrumentation list (pg_stat_statements, auto_explain, pgaudit at 14:47) is an extensions list, and the trigram suggestion at 02:35 implies pg_trgm.

**Learn more.** https://www.postgresql.org/docs/current/extend-extensions.html

---

### GUC (Grand Unified Configuration)

**What it is.** The name Postgres gives its server settings: every parameter you can set in `postgresql.conf`, with `ALTER SYSTEM`, per role or database, or per session with `SET`. Ryan Booz counted roughly 400 on a default PostgreSQL 18 Docker image. GUC stands for Grand Unified Configuration (the acronym is expanded in the Postgres source's `utils/misc/README`); Ryan Booz said "Global".

**How it works.** Each GUC has a type (boolean, enum, integer, real, string), a default, and a context that decides who can change it and when: some need a restart (`shared_buffers`, `shared_preload_libraries`), some a reload (`log_min_duration_statement` can be changed by a superuser without restart), some are per-session. `SHOW name` and the `pg_settings` view expose current values and their source. Settings layer: session overrides role overrides database overrides `postgresql.conf` overrides the compiled default.

**History.** The GUC subsystem has existed since the 7.x series (exact introduction unverified here); the name has stuck in community usage. "GUC" is the word you will hear in every Postgres talk and mailing-list thread.

**Value and use cases.** The instrumentation Ryan Booz asked the room to turn on (auto_explain, pg_stat_statements, track_io_timing, log_min_duration_statement) is all GUCs. So is the planner's cost model (`random_page_cost`, `effective_cache_size`), memory (`work_mem`), and every autovacuum threshold.

**Limitations and gotchas.** Nearly everything is off or conservative by default, on every provider. "Thirty years of work, and everyone has an opinion," so the defaults are the least-objectionable, not the best. Managed platforms restrict which GUCs you can change; Supabase exposes many only through `ALTER ROLE/DATABASE … SET` or its CLI, and some not at all on lower tiers.

**Agentic-era relevance.** Two-sided. The instrumentation GUCs are what give an agent context. And "configuration autotune" (OtterTune, DBtune) is a whole category of AI product that does nothing but tune GUCs against your workload, which Ryan Booz explicitly scoped out of the talk.

**In the room.** 12:08 ("round about four hundred settings … GUCs is the Global Unified Configuration, so G-U-C … It's all the settings that Postgres you can change"). Explained, with the acronym expansion misstated.

**Learn more.** https://github.com/postgres/postgres/blob/master/src/backend/utils/misc/README · https://www.postgresql.org/docs/current/runtime-config-query.html

---

### Index (B-tree) and index types (GIN, BRIN, trigram, HNSW / IVFFlat)

**What it is.** A separate data structure that lets Postgres find matching rows without reading the whole table. The pre-event post's analogy: a book's index gets you to the page fast, but every time you add a page the index must be updated too. That write cost is why "add an index" is not free.

**How it works.** `CREATE INDEX` defaults to **B-tree**, a balanced tree that supports equality and range lookups (`=`, `<`, `BETWEEN`, prefix `LIKE 'abc%'`) and sorted output. **GIN** (Generalized Inverted Index) maps each element (a word, a trigram, an array item, a JSON key) to the rows containing it; with the pg_trgm extension a GIN trigram index makes `ILIKE '%love%'` and regex searches indexable. **BRIN** (Block Range Index) stores only min/max summaries per range of pages; it is tiny and works only when values correlate with physical order (timestamps in an append-only table). Expression indexes (`ON (lower(title))`) and partial indexes (`WHERE status = 'unbilled'`) narrow what is indexed. **HNSW** and **IVFFlat** are pgvector's approximate-nearest-neighbour indexes for embeddings (see pgvector).

**History.** GIN: PostgreSQL 8.2 (December 5, 2006). BRIN: PostgreSQL 9.5 (January 7, 2016, Álvaro Herrera). B-tree deduplication of repeated keys: PG 13 (September 24, 2020). HNSW in pgvector 0.5.0 (August 28, 2023). The HNSW algorithm itself is from Malkov and Yashunin's 2016 paper (arXiv:1603.09320).

**Value and use cases.** The right index turns a full-table read into a handful of page fetches. The wrong index is pure write overhead: the pre-event carousel's `WHERE status = 'shipped'` (95% of rows match) is a case where a sequential scan beats any index.

**Limitations and gotchas.** A leading wildcard (`'%love%'`) defeats a B-tree; that is the trigram case. An index the planner never uses still costs every write (Supabase's `unused_index` advisor). Statistics decide whether an index is used at all. Building one without `CONCURRENTLY` locks writes.

**Agentic-era relevance.** Index recommendation is the oldest form of AI-ish database tuning (the "first generation": hypothetical-index advisors such as HypoPG). It is also the most common thing a model suggests without context. With schema and existing-index context, Ryan Booz's model stopped recommending a trigram index it could see already existed, and noticed a BRIN on the `overview` column that limited its options.

**In the room.** 02:35 ("let's create eighteen hundred indexes … let's try a trigram"; explained as the reflexive first guess), 08:28 (locking), 25:22 block ("index is fast, but that's not gonna help anybody" when looped 2.5 million times), 47:49 block (BRIN found on the column; B-tree suggested instead). Partly explained per type.

**Learn more.** https://www.postgresql.org/docs/current/sql-createindex.html · https://www.postgresql.org/docs/current/pgtrgm.html · https://www.postgresql.org/docs/current/brin.html

---

### Join algorithms (nested loop, hash join, merge join)

**What it is.** The three ways Postgres combines rows from two inputs. The planner picks one per join based on estimated row counts, available indexes and memory. Picking wrong is one of the most common ways a query goes from one second to an hour.

**How it works.** **Nested loop**: for each row of the outer input, scan the inner input for matches; cheap when the outer side is small and the inner side has an index, catastrophic when the outer side turns out to have a million rows. **Hash join**: load the smaller input into an in-memory hash table keyed on the join column, then stream the larger input through it; good for large, unsorted inputs, memory-bound (`work_mem × hash_mem_multiplier`). **Merge join**: sort both inputs on the join key and walk them together; each side read once; good when inputs are already sorted (index order). The planner considers all three for every join and, past `geqo_threshold` (default 12 tables), switches to a genetic search rather than exhaustive enumeration.

**History.** All three strategies have been in the planner since early PostgreSQL releases (exact versions not needed here). PG 13 let hash aggregation spill to disk rather than be avoided; PG 9.6 (September 29, 2016) introduced parallel hash joins and nested loops.

**Value and use cases.** Reading the join choice in a plan tells you what the planner believed. Ryan Booz's example: a nested loop chosen because statistics said "a couple hundred rows", then a data load last night made it a million, "and the query ends up taking an hour."

**Limitations and gotchas.** The join choice is downstream of statistics; a bad estimate produces a bad join. `enable_nestloop = off` cannot fully suppress nested loops (some joins have no alternative). A hash join whose table exceeds memory spills to temp files and shows up as `written`/`temp` buffers.

**Agentic-era relevance.** "I see a nested loop. By doing this change, I expect that to turn into a hash join. Does that happen?" is Ryan Booz's template for a testable hypothesis, and it is exactly the kind of prediction an agent should be made to state before it is allowed to change anything.

**In the room.** 40:04 block (nested loop from a bad statistic; the expected flip to a hash join; "specific formulas for, like, hey, when it's a hash join, it's gonna add this much work"). Partly explained: nested loop and hash join were named and motivated; merge join was not mentioned.

**Learn more.** https://www.postgresql.org/docs/current/planner-optimizer.html

---

### log_min_duration_statement (and statement logging)

**What it is.** The setting that logs the text and duration of any statement that runs at least N milliseconds. Its sibling `auto_explain.log_min_duration` logs the plan; this one logs the query. Ryan Booz's rule: start at about one second.

**How it works.** Default `-1` (off). `0` logs every statement's duration. A value like `250ms` logs only statements at or over that. Changeable by a superuser without a restart. Related: `log_duration` (log every statement's duration, no threshold: noisy), `log_statement` (`none`/`ddl`/`mod`/`all`: which statement classes to log regardless of duration), `log_min_error_statement` (log the statement that caused an error at or above a severity), `log_min_duration_sample` + `log_statement_sample_rate` (log a random fraction of slow statements when traffic is too high to log all), and `log_destination = jsonlog` for structured logs.

**History.** Present through the 8.x series and earlier (exact introduction unverified here). The sampling variants are more recent additions. PG 15 added `jsonlog`.

**Value and use cases.** Finding queries that are slow but do not show up in pg_stat_statements as top offenders by total time, and correlating a slow statement with its plan in the same log window. Ryan Booz uses pg_stat_statements to choose the threshold: "almost eight and a half million queries execute fifty milliseconds or slower … maybe I want my auto_explain to be like three seconds."

**Limitations and gotchas.** Over-instrumentation is the classic mistake: "I'm gonna set log_min_duration_statement to, like, zero … it's too much noise, and you can't find the stuff that really you need to." Logs are also where query parameters leak, which is the "parameter paradox" from the pre-event brief: you need the values to reproduce the plan, and you must not ship them to an agent.

**Agentic-era relevance.** Log lines are one of the three context sources (with stats and plans). pganalyze's MCP server exposes individual log lines only if PII filtering is configured, which is how a vendor resolves the paradox.

**In the room.** 14:47 (the zero-threshold anti-pattern; explained), 15:43 ("Both of them are the threshold … This will log the query text to the log. Over here, log_min_duration, the setting, will log the EXPLAIN plans"; explained), 18:03–21:43 (choosing a value from pg_stat_statements). Fully explained.

**Learn more.** https://www.postgresql.org/docs/current/runtime-config-logging.html

---

### MCP for databases (and read-only agent access)

**What it is.** The Model Context Protocol is an open standard, announced by Anthropic on November 25, 2024, for connecting AI assistants to tools and data through a single protocol instead of one custom integration per source. A "database MCP server" is a program that exposes database tools (run a query, get stats, list tables) to an agent. The whole safety conversation is about which tools, against which database, with which permissions.

**How it works.** The agent calls named tools; the server executes them and returns results. Designs differ on what sits behind the tools. Anthropic's original reference Postgres server ran SQL against a live connection inside a read-only transaction; Datadog Security Labs later showed that read-only wrapper could be broken out of with a `COMMIT; …` injection, and the server now lives in the archived repo with "no security guarantees." Supabase's MCP server offers `read_only=true` (queries run as a read-only Postgres user) and `project_ref=` scoping. Xata's server never gives the agent a credential, is read-only by default, requires `write=true` and `confirm=true` for writes, and scopes every call to a branch. pganalyze's server has no database connection at all: it reads pganalyze's collected stats, plans and logs, withholds raw query parameters under basic access, and is rate-limited to 100 requests per billable server per hour in preview.

**History.** MCP: November 2024. Reference Postgres server: archived (the SQL injection write-up appeared in August 2025). Xata MCP server: May 2025, then 2.0. pganalyze MCP server: public preview April 30, 2026, after nearly 100 early-access companies. The MCP roadmap of August 22, 2026 put identity and security among its five priorities (see the Security long tail).

**Value and use cases.** Ryan Booz's live demo: "Here's the query ID. Go find the worst and the best EXPLAIN plans. See if they're similar. Look at the total runtime over the last twenty-four hours. Find if it's a time-based issue." The agent found the correlated subquery, a vacuum problem and a missing index on `overview`.

**Limitations and gotchas.** Prompt injection: instructions embedded in data the agent reads can steer it into running queries. Ryan Booz's one hard "don't": "the only tool I wouldn't tell you to use is Anthropic's Postgres MCP tool against your prod. Because it will be relentless." A live connection also means the agent's exploratory queries add load to the server it is trying to fix.

**Agentic-era relevance.** This is the term. The pre-event brief's "five generations" ends with "context servers": feed curated telemetry to the general-purpose agent you already use, instead of building a stand-alone AI DBA (Xata archived its Agent on June 15, 2026 and shipped branch-scoped MCP instead).

**In the room.** 09:43 ("It's not gonna be about MCP security. I'm gonna show you an MCP server"), 47:49 block (the demo, the "relentless" warning, six unsupervised rewrite iterations). Partly explained: the demo was shown; the protocol was not.

**Learn more.** https://www.anthropic.com/news/model-context-protocol · https://pganalyze.com/docs/mcp · https://supabase.com/docs/guides/getting-started/mcp · https://securitylabs.datadoghq.com/articles/mcp-vulnerability-case-study-SQL-injection-in-the-postgresql-mcp-server/

---

### Parameter-sensitive plans (generic vs custom plans, prepared statements)

**What it is.** The same query can deserve different plans for different parameter values. `WHERE tenant_id = $1` wants an index scan for a small tenant and a sequential scan for the tenant that owns 40% of the rows. A plan that is right for one value and wrong for another is parameter-sensitive, and it is the reason "this query is sometimes slow" is so hard to diagnose.

**How it works.** A prepared statement is parsed and planned once and re-executed with different values. Postgres plans the first five executions with **custom plans** (tailored to the actual values), computes the average estimated cost, then builds a **generic plan** (value-agnostic) and switches to it if its cost is not much higher. `plan_cache_mode` (`auto`, `force_custom_plan`, `force_generic_plan`) overrides the heuristic. Even without prepared statements, a plan flip happens whenever the statistics say "this value is rare" and it is not: Ryan Booz's demo query had four different plan shapes in 24 hours, with costs of 10 million and 22 million where the *more* expensive estimate ran *faster*.

**History.** Custom plans for prepared statements: PostgreSQL 9.2 (September 10, 2012, Tom Lane). `plan_cache_mode`: PostgreSQL 12 (October 3, 2019, Pavel Stehule).

**Value and use cases.** Explains bimodal latency. Fixing it is usually a statistics fix (higher `statistics_target` on the skewed column, extended statistics) or a query-shape fix, not an index.

**Limitations and gotchas.** Connection poolers in transaction mode do not support prepared statements at all. Generic plans cannot see the value, so on a skewed column they are a coin flip. The "parameter paradox": to reproduce the bad plan you need the specific value, which is often the thing you must not log or hand to an agent.

**Agentic-era relevance.** Alex's prepared question for the talk: without raw parameters, how does an agent reason about a plan that flips on one skewed value? Azure's autonomous tuning answers by capturing one sample value per query (`capture_first_sample`). pganalyze answers by retaining plan history per query ID and letting Workbooks test named parameter sets against baseline and variants.

**In the room.** 12:08 block, near the end ("Maybe some parameters create plan A and some parameters create plan B, and plan B is really slow"), 25:22 block ("four different explained plans over that time … a lot of that's because of the words that are being searched for"). Described, not explained in generic/custom terms.

**Learn more.** https://www.postgresql.org/docs/current/sql-prepare.html · https://learn.microsoft.com/en-us/azure/postgresql/monitor/concepts-autonomous-tuning

---

### pg_stat_statements

**What it is.** The extension that keeps a running ledger of every distinct query shape the server has executed: how many times, total and mean time, rows, buffers, WAL, and more. The pre-event brief's phrase: "a running ledger of every distinct query shape's execution counts and timing." Ryan Booz's: "my weird passion of Postgres … love it and hate it."

**How it works.** It must be in `shared_preload_libraries` (restart required). Each statement is normalized (constants replaced by `$1`, `$2`) and hashed into a 64-bit `queryid` computed from the parsed tree, so `WHERE a IN (1,2,3)` and `WHERE a IN (4,5)` share one row. `pg_stat_statements.max` (default 5000) caps the number of tracked shapes; least-executed rows are evicted. `track = top` (default) counts only top-level statements; `all` includes statements inside functions. Counters are cumulative until `pg_stat_statements_reset()`. Non-superusers see statistics but not other users' query text unless granted `pg_read_all_stats`.

**History.** Added as a contrib module in PostgreSQL 8.4 (July 1, 2009, Itagaki Takahiro). PG 17 (September 26, 2024) renamed the I/O timing columns (`shared_blk_read_time`) and added `stats_since`; PG 18 added parallel-worker columns.

**Value and use cases.** Triage. "Does this query actually matter?" Ryan Booz's slow query was called 256 times in 24 hours and was already 22% of total runtime; another was called 12,000 times and did almost no work. Ranking by total time, not by call count or by single-run duration, is the discipline. It is also how you pick a sane `log_min_duration` threshold.

**Limitations and gotchas.** Not installed by default on most providers; Ryan Booz believes AWS RDS is the only major one that enables it automatically (Azure and GCP require enabling; stated as belief, not verified here). It is cumulative, so you cannot tell *when* the work happened without sampling. `queryid` is not stable across major versions. Filling it with thousands of one-off query texts (`pg_audit`, `log_duration` habits, unparameterized SQL) makes it slow to query and lock-heavy.

**Agentic-era relevance.** The query ID is the handle you give an agent: "here's the query ID, go find the worst and best plans." pganalyze's "context server" is largely sampled pg_stat_statements plus retained plans. Without it, an agent has no way to know whether the query it is tuning is worth tuning.

**In the room.** 14:47 ("not installed in most environments"; explained), 18:03 (cumulative, needs sampling; explained), 21:43 (choosing thresholds from it), 25:22 block (256 calls, 22% of runtime; "is this actually doing something"). Fully explained; Ryan Booz also announced a seven-part pganalyze series on it.

**Learn more.** https://www.postgresql.org/docs/current/pgstatstatements.html · https://pganalyze.com/blog

---

### pgvector

**What it is.** The extension that adds a `vector` column type and similarity search to Postgres, so embeddings can live next to the rows they describe, with the same transactions, backups and access control. It is why "Postgres as the agent data layer" is a sentence people say.

**How it works.** `CREATE EXTENSION vector` adds types (`vector` single-precision, `halfvec` half-precision, `sparsevec`, and `bit` for binary vectors), distance operators (`<->` L2, `<=>` cosine, `<#>` inner product, `<+>` L1, Hamming and Jaccard for binary) and two approximate index types. **HNSW** builds a multi-layer proximity graph: best query speed and recall, slower build, more memory. **IVFFlat** clusters vectors into lists and searches the nearest lists: faster build, less memory, lower recall, and it needs data present before building. Without an index, search is exact and sequential. From 0.8.0, iterative index scans keep scanning until a filtered query has enough results, fixing the "fewer rows than requested" problem with `WHERE` clauses.

**History.** First release 0.1.0 on April 20, 2021 (Andrew Kane). HNSW in 0.5.0 (August 28, 2023). `halfvec`/`sparsevec` in 0.7.0 (April 29, 2024). Iterative scans and better cost estimation in 0.8.0 (October 30, 2024). CVE-2026-3172 (buffer overflow in parallel HNSW build; CVSS 8.1; published February 25, 2026) affects 0.6.0–0.8.1 and is fixed in 0.8.2. Latest release 0.8.6.

**Value and use cases.** Semantic search over documents, deduplication of near-identical records, retrieval for RAG. The pre-event prior-context pack put the practical ceiling around 10 million vectors before dedicated vector databases start to win at 50 million and up (a prior-brief figure, not re-verified here).

**Limitations and gotchas.** Approximate indexes trade recall for speed; tune `ef_search` (HNSW) or `probes` (IVFFlat). Vector limits: 2,000 dimensions for indexed `vector`, 16,000 unindexed. Filtering plus an approximate index can under-return; use iterative scans. Index builds are memory- and time-hungry on large tables.

**Agentic-era relevance.** Embeddings are how an agent's notion of "similar" gets stored. Keeping them in the same Postgres as the entity graph means one system of record, one RLS model, one backup, and one set of pg_stat_statements rows to watch.

**In the room.** Not mentioned. Comes from the pre-event research (Postgres as the agent data layer; AlloyDB's ScaNN as the Google alternative) and Alex's stack.

**Learn more.** https://github.com/pgvector/pgvector · https://supabase.com/docs/guides/database/extensions/pgvector

---

### Planner cost

**What it is.** The planner's estimate of how much work a plan will take, in arbitrary units, used only to compare candidate plans against each other. Not a time, not a page count. Ryan Booz at 47:45–47:49: "an artificial unit … a relative value of work."

**How it works.** Every node gets `startup cost` (before the first row can be returned; a sort's cost is almost all startup) and `total cost`. The anchor is `seq_page_cost = 1.0`: one sequential page read. `random_page_cost` (default 4.0) prices a random page fetch; on SSDs or fully cached data it is commonly lowered toward 1.1. `cpu_tuple_cost`, `cpu_operator_cost` price per-row work. A sequential scan of a 345-page, 10,000-row table costs 345 × 1.0 + 10,000 × 0.01 = 445. Join costs use per-algorithm formulas fed by estimated row counts, which come from statistics. `effective_cache_size` (default 4 GB) tells the planner how much of the data it may assume is cached, which tilts it toward index scans.

**History.** Cost-based planning is how Postgres has always chosen plans; the tunable cost constants have been GUCs for the whole modern era. PG 18 began printing fractional row estimates in `EXPLAIN`.

**Value and use cases.** Comparing plans for the *same* query: if a rewrite drops estimated cost from 22 million to 10 thousand, the planner believes it is doing far less work. Comparing across different queries is meaningless: "it's not like a thousand costs versus ten million costs for a different query means that it's gonna be a thousand times slower."

**Limitations and gotchas.** Cost is only as good as the statistics under it. Ryan Booz's two plans: cost 22 million ran faster than cost 10 million. When cost and runtime disagree, the map is wrong, not the GPS. Cost also ignores network transfer and result serialization unless `SERIALIZE` is requested.

**Agentic-era relevance.** Azure's tuner measures improvement and regression thresholds in plan cost, not duration, and the docs say so explicitly. An agent that reports "cost dropped 90%" has made a claim about the planner's belief, not about your latency; the bounded loop must re-check with `EXPLAIN ANALYZE` and buffers.

**In the room.** 25:22 block (cost estimates of 10 million and 22 million; the more expensive one ran faster), 47:45–47:49 (audience: "Just a number?"; Ryan Booz: "artificial unit … based on statistics"; "cost-based planners"). Explained.

**Learn more.** https://www.postgresql.org/docs/current/using-explain.html · https://www.postgresql.org/docs/current/runtime-config-query.html

---

### Query planner (optimizer)

**What it is.** The part of Postgres that turns a declarative SQL statement into an execution plan. The glossary's own words: "the part of PostgreSQL that is devoted to determining (planning) the most efficient way to execute queries. Also known as query optimizer, optimizer, or simply planner." The GPS: it knows every road (scan and join method), consults its map (statistics), and picks the lowest-cost route.

**How it works.** For each table it generates a sequential-scan path and, where an index matches a `WHERE` or `ORDER BY`, index paths (including bitmap scans). For each join it considers nested loop, merge and hash, and different join orders. Each candidate gets a cost; the cheapest wins; the winner becomes the plan tree the executor runs. Below `geqo_threshold` (12 FROM items) the search is near-exhaustive; above it a genetic algorithm approximates. The `enable_*` GUCs can discourage a strategy for diagnosis. Extensions such as pg_hint_plan can force choices.

**History.** Cost-based planning has been Postgres's approach since the Berkeley project (1986–1994) and Postgres95 (1995). Parallel query: PG 9.6 (September 29, 2016). Extended statistics for the planner: PG 10 (October 5, 2017). JIT compilation of expressions: PG 11, on by default.

**Value and use cases.** Understanding that SQL says *what* and the planner decides *how* is the foundation of every tuning conversation. Ryan Booz: "SQL is a declarative language. I want this. I don't tell Postgres how to get it." The planner source is famously well-commented ("like a book at the beginning of the planner"), Ryan Booz's own explanation for why LLMs do well at Postgres was that the models have read that open source (a belief offered in the room without a source: "I can't point to a source").

**Limitations and gotchas.** The planner cannot see the future or your data; it sees statistics. It assumes column independence unless you create extended statistics. It cannot know an index would help unless the index (or a hypothetical one via HypoPG) exists. A good plan for one parameter value may be wrong for another.

**Agentic-era relevance.** Ryan Booz's "Query, data, stats, or config?" triage is a question about which of the planner's inputs is wrong. An agent that reads the plan is reading the planner's reasoning; an agent with only the SQL is guessing at what the planner might do.

**In the room.** 25:22 block ("It determines, okay, you want data from here … it says, 'Well, I think the best way to go about it is first to grab this data and then iterate over the data over here'"; the source-code-as-book aside), 40:04 block ("PostgreSQL, SQL Server, others are cost-based planners"). Explained.

**Learn more.** https://www.postgresql.org/docs/current/planner-optimizer.html · https://www.postgresql.org/docs/current/glossary.html

---

### Row-Level Security (RLS)

**What it is.** A Postgres feature that filters which rows a role may see or change, per table, using policies you write as SQL expressions. On Supabase it is the mechanism that makes it safe to expose a database through a public API: the `anon` and `authenticated` roles hit PostgREST, and RLS decides what rows come back.

**How it works.** `ALTER TABLE t ENABLE ROW LEVEL SECURITY` turns it on; with no policies, the default is deny-all. `CREATE POLICY … USING (expr) WITH CHECK (expr)` grants visibility (`USING`) and modifiability (`WITH CHECK`) where the expression is true; multiple policies combine with OR (permissive) or AND (restrictive). Superusers, roles with `BYPASSRLS`, and table owners bypass it (owners can opt in with `FORCE ROW LEVEL SECURITY`). Policy expressions are appended to the query's `WHERE`, so they are evaluated per row; Supabase's guidance is to wrap `auth.uid()` in `(select auth.uid())` so the planner evaluates it once as an InitPlan instead of once per row (their advisor `auth_rls_initplan` flags the slow form). Two things RLS does not govern: `TRUNCATE` and `REFERENCES` privileges; and grants still decide whether a role can touch the table at all (grants first, then policies).

**History.** PostgreSQL 9.5 (January 7, 2016; Craig Ringer, KaiGai Kohei, Adam Brightwell, Dean Rasheed, Stephen Frost).

**Value and use cases.** Multi-tenant isolation in one table. Public-facing APIs. Giving an agent a role that can only see the rows it should.

**Limitations and gotchas.** RLS is a filter, not a wall: a role with full grants and RLS-enabled-no-policy can still `TRUNCATE`. `service_role` bypasses RLS entirely and must stay server-side. Policies with subqueries or function calls cost per row on big tables.

**Agentic-era relevance.** The cleanest way to give an agent "read-only, these rows only" access is a dedicated role with `SELECT` grants and RLS policies, rather than trusting the MCP server's read-only flag alone. Datadog's injection finding against the reference Postgres server is the argument: enforce in the database, not in the wrapper.

**In the room.** Not discussed. Comes from the pre-event research (Supabase's `RLS initplan` advisor) and Alex's stack.

**Learn more.** https://www.postgresql.org/docs/current/ddl-rowsecurity.html · https://supabase.com/docs/guides/database/postgres/row-level-security

---

### Sequential scan vs index scan

**What it is.** The two basic ways to read a table. A sequential scan reads every page in order, like reading a book cover to cover. An index scan looks up matching entries in an index and fetches just those rows, like using the book's index. Neither is always better; the planner chooses by cost.

**How it works.** Sequential scan cost is roughly pages × `seq_page_cost` plus rows × `cpu_tuple_cost`, and it benefits from the operating system's read-ahead. An index scan pays per random page fetch (`random_page_cost`, default 4.0) and per index entry, so it wins only when the query selects a small fraction of rows. In between sits the **bitmap index scan**, which collects matching page locations from one or more indexes, sorts them, and reads the heap in page order. **Index-only scans** (PG 9.2, 2012) skip the table entirely when the index holds every needed column and the visibility map says the page is all-visible, which is one more reason VACUUM matters.

**History.** Sequential and index scans are as old as the planner. Bitmap scans arrived in the 8.1 era (unverified here); index-only scans in PostgreSQL 9.2 (September 10, 2012). Parallel sequential scans in 9.6 (September 29, 2016). PG 18's asynchronous I/O subsystem (`io_method`) speeds sequential and bitmap heap scans.

**Value and use cases.** The pre-event carousel's example: `WHERE status = 'shipped'` where 95% of rows match; the full scan is cheaper, and on an insert-heavy table the index would be pure write cost. `WHERE tenant_id = $1` wants an index scan for a small tenant and a sequential scan for the largest.

**Limitations and gotchas.** A sequential scan on a small table is correct, not a problem; Supabase's "unused index" findings on a 17 MB database are expected for this reason. An index scan inside a nested loop that runs 2.5 million times is technically "using the index" and is still a disaster. `enable_seqscan = off` is a diagnostic tool, never a production setting.

**Agentic-era relevance.** "Add an index on the column in your WHERE clause" is the first thing every model says with no context, and it is wrong whenever selectivity is poor, the write load is high, or the table is small. Data distribution decides, and distribution lives in the statistics, which the model cannot see unless you hand them over.

**In the room.** 02:35 (the reflexive index suggestion), 25:22 block ("it ended up looping over this table to index two point five million times. Like, index is fast, but that's not gonna help anybody"). Partly explained; the scan types were not named as such.

**Learn more.** https://www.postgresql.org/docs/current/planner-optimizer.html · https://www.postgresql.org/docs/current/using-explain.html

---

### Statistics and ANALYZE (extended statistics, statistics targets)

**What it is.** The planner's map. `ANALYZE` samples each table and records, per column, the estimated row count, most common values and their frequencies, a histogram of value ranges, the number of distinct values, and the correlation between value order and physical order. The planner reads these to estimate how many rows each step will return, which decides scans, joins and everything else.

**How it works.** `ANALYZE` (manual, or autovacuum's auto-analyze when about 10% of a table has changed) samples rows and writes to `pg_statistic`, readable through `pg_stats`. `default_statistics_target` (default 100) sets how many most-common values and histogram buckets are kept; `ALTER TABLE … ALTER COLUMN … SET STATISTICS n` raises it per column for skewed data (up to 10,000). Table-level `reltuples`/`relpages` live in `pg_class`. Because the planner assumes columns are independent, `CREATE STATISTICS` builds **extended statistics** across columns: functional dependencies (ZIP determines city), n-distinct for multi-column `GROUP BY`, and multi-column most-common-value lists.

**History.** `default_statistics_target` rose from 10 to 100 in PostgreSQL 8.4 (July 1, 2009). Extended statistics (`CREATE STATISTICS`) arrived in PostgreSQL 10 (October 5, 2017; Tomas Vondra, David Rowley, Álvaro Herrera); MCV lists for extended statistics followed in PG 12.

**Value and use cases.** Ryan Booz's customer story: a query that "absolutely had a problem last night" ran in 50 ms at 9 am after `ANALYZE`. Stale statistics after a data load are the textbook cause of "a nested loop because there's a bad statistic … suddenly there's a million of those." Azure's tuner refuses to recommend indexes for tables with no statistics; it recommends `ANALYZE` first.

**Limitations and gotchas.** Statistics are a sample; on highly skewed columns the default target under-represents the tail. Autovacuum's analyze threshold is proportional, so small, slowly changing tables can go months without a refresh. Extended statistics only help the column combinations you declare.

**Agentic-era relevance.** Statistics are what the planner "believes" and therefore what an agent must see to explain a plan. They are also, per the audience discussion at 62:45–63:50, the shortcut to a realistic test environment: hand the statistics to a model and it can generate a smaller dataset with a similar distribution.

**In the room.** 25:22 block ("when we ran analyze at that moment at nine AM Eastern, it ran in, like, fifty milliseconds"; "something about the stats seemed to be off"), 40:04 block ("a nested loop join because there's a bad statistic"), 47:49 ("it's based on statistics. So hey, the column has this much distribution of a specific value"), 62:45 ("Distribution's the bigger one"). Partly explained: the role of statistics was clear; `ANALYZE` itself and targets were not walked through.

**Learn more.** https://www.postgresql.org/docs/current/planner-stats.html · https://www.postgresql.org/docs/release/10.0/

---

### track_io_timing

**What it is.** The setting that makes Postgres record how long it waits on disk reads and writes, separately from CPU work. Off by default. Ryan Booz's slide put it among the four things to turn on, with an overhead of roughly 1–5% (Ryan Booz's figure).

**How it works.** When on, Postgres asks the operating system for the time before and after each I/O and accumulates the difference. The timings surface in `pg_stat_database` (`blk_read_time`, `blk_write_time`), `pg_stat_io` (`read_time`, `write_time`, `fsync_time`), `EXPLAIN (BUFFERS)` output (`I/O Timings: read=… write=…`), `VACUUM (VERBOSE)`, autovacuum logs, and pg_stat_statements (`shared_blk_read_time` since PG 17). The docs' caveat is that repeatedly querying the clock "may cause significant overhead on some platforms"; `pg_test_timing` measures your platform's cost. Modern Linux on virtualized cloud hardware is usually cheap.

**History.** Added in PostgreSQL 9.2 (September 10, 2012; Ants Aasma, Robert Haas). PG 16 added `pg_stat_io`; PG 17 split the pg_stat_statements columns into shared/local; `track_wal_io_timing` covers WAL separately.

**Value and use cases.** Answers "is this query slow because it is waiting on disk or because it is burning CPU?", the I/O-bound versus CPU-bound split Ryan Booz raised at 14:47. Without it, a query that reads 10,000 `shared read` buffers looks identical whether those reads took 2 ms or 2 s.

**Limitations and gotchas.** Only measures I/O Postgres issues; a page served from the OS page cache still counts as a "read" (fast) versus a true disk read (slow), and the timing is how you tell them apart. Needs `BUFFERS` in `EXPLAIN` to show. On a database that is 99.99% cache hits it will report almost nothing.

**Agentic-era relevance.** It turns a buffer count into a cost the agent can attribute: "the time is in I/O on this node" versus "the time is CPU in the sort." Ryan Booz's four-tools slide treats it as baseline context.

**In the room.** 15:43 ("track_ever_timing, consider it" — the ASR heard "ever"; the slide reads `track_io_timing`). Named as a recommendation, not explained.

**Learn more.** https://www.postgresql.org/docs/current/runtime-config-statistics.html

---

### VACUUM, autovacuum, MVCC and dead tuples

**What it is.** Postgres never overwrites a row in place. An `UPDATE` writes a new version and leaves the old one for transactions that might still need it; a `DELETE` marks the old one. The design is **MVCC** (multiversion concurrency control): readers do not block writers and writers do not block readers, because everyone sees a snapshot. The price is **dead tuples**: old versions nobody can see anymore. **VACUUM** reclaims them; **autovacuum** runs it for you.

**How it works.** Plain `VACUUM` marks dead space reusable, updates the visibility map (which index-only scans depend on), and freezes old transaction IDs to prevent wraparound; it does not block reads or writes. `VACUUM FULL` rewrites the table under an `ACCESS EXCLUSIVE` lock and should be rare. Autovacuum's launcher starts workers (default 3, checking every 60 s); a table is vacuumed when dead tuples exceed `autovacuum_vacuum_threshold` (50) + `autovacuum_vacuum_scale_factor` (0.2) × rows, and analyzed at threshold 50 + 0.1 × rows. Both can be tuned per table with storage parameters. Bloat is the accumulated dead space when vacuum cannot keep up.

**History.** MVCC replaced table-level locking in PostgreSQL 6.5 (June 9, 1999). Non-blocking "lazy" `VACUUM` with `VACUUM FULL` as the old behaviour: PostgreSQL 7.2 (February 4, 2002). Autovacuum moved from contrib into the server in 8.1 (November 8, 2005, Álvaro Herrera). PG 17 (September 26, 2024) rewrote vacuum's memory management (the TID store), removing the old 1 GB ceiling.

**Value and use cases.** Keeps tables from growing without bound, keeps the visibility map accurate, and refreshes statistics as a side effect (auto-analyze). Supabase's advisors flag disabled autovacuum and bloated tables; Azure's tuner recommends `VACUUM` on bloated tables.

**Limitations and gotchas.** Default thresholds are proportional, so a huge table with 19% dead rows is "fine" by the rule and terrible in practice; lower the scale factor for hot tables. Long-running transactions (or `idle in transaction` sessions) pin old snapshots and stop vacuum from cleaning anything. Autovacuum that is starved of workers or I/O silently falls behind; Ryan Booz's agent found "something messed up with vacuum" on the demo database from stats alone.

**Agentic-era relevance.** Vacuum health is table-level telemetry an agent can read (`n_dead_tup`, `last_autovacuum`) and act on with low risk (`ANALYZE` and `VACUUM` are safe to recommend). pganalyze ships a VACUUM Advisor for exactly this.

**In the room.** 47:49 block ("Inventory, it turns out I did not know this on this database … I apparently have something messed up with vacuum, so that was interesting … it could see that through the stats"). Named, not explained.

**Learn more.** https://www.postgresql.org/docs/current/routine-vacuuming.html · https://www.postgresql.org/docs/current/mvcc-intro.html

---

### work_mem and disk spill

**What it is.** `work_mem` is the memory budget each sort or hash operation may use before it writes temporary files to disk. Spilling is what happens when it runs out: the operation continues, correctly, but at disk speed, and the plan shows it (`Sort Method: external merge Disk: 1024kB`, or `temp read/written` buffers).

**How it works.** Default 4 MB. It is per operation, not per query and not per connection: a query with three sorts and a hash join can use four times `work_mem`, and 50 concurrent connections multiply again, which is why the default is conservative. Hash-based operations (hash joins, hash aggregates, memoize, `IN` subqueries) get `work_mem × hash_mem_multiplier` (default 2.0). Sorts serve `ORDER BY`, `DISTINCT` and merge joins. It can be set per session (`SET work_mem = '64MB'`) for a known heavy query, per role, or globally. `maintenance_work_mem` (64 MB default) is the separate budget for `VACUUM`, `CREATE INDEX` and foreign-key builds.

**History.** `work_mem` replaced the older `sort_mem` name in the 8.0 era (unverified here). PG 13 (September 24, 2020) let hash aggregation spill to disk instead of being avoided and introduced `hash_mem_multiplier`. PG 18 added memory and disk usage details to Material, Window Aggregate and CTE nodes in `EXPLAIN`.

**Value and use cases.** Ryan Booz's rewritten query was hundreds of times faster and still spilled: "it actually still had to spin out to disk because there wasn't enough memory in the process to do the sorting." That is the next optimization after the shape fix, and it is a one-line setting. pganalyze's Query Advisor includes a `work_mem` sizing check.

**Limitations and gotchas.** Raising it globally is the classic way to run a server out of memory under concurrency. Raise it per role or per statement first. A spill shows as `written` buffers even on a read-only query, which confuses people reading their first plan.

**Agentic-era relevance.** "Server tuning" was one of the two things Ryan Booz's models kept alternating between after they found the subquery; `work_mem` is usually what they mean. It is a safe, reversible, session-scoped change, which makes it a good candidate for an agent to propose and a human to approve.

**In the room.** 40:03 block (disk usage in the rewritten plan; "there wasn't enough memory in the process to do the sorting … that's another potential optimization"). Partly explained; the GUC name was not stated on the transcript (it appears on the slide and in the pre-event material).

**Learn more.** https://www.postgresql.org/docs/current/runtime-config-resource.html · https://www.postgresql.org/docs/release/13.0/

---

## Long tail

Format: term — what it is; why it matters (where it came up: mm:ss for the talk, or "brief" / "post" / "carousel" for the pre- and post-event material).

### SQL and query shapes

- **Bitmap index scan / bitmap heap scan** — the planner's middle path between index and sequential scan: collect matching page locations from an index (or several), then read the heap in page order. Shows up on medium-selectivity predicates. (docs)
- **Cartesian product** — a join with no matching condition that pairs every row with every row; the hidden cost Ryan Booz suspected among the demo query's many joins before seeing the plan. (23:52)
- **DDL** — schema-changing statements (`CREATE INDEX`, `ALTER TABLE`). The line every vendor draws: agents may propose DDL, not apply it to prod. (brief)
- **DROP INDEX / REINDEX** — remove an index, or rebuild one (needed after a failed `CONCURRENTLY` build or on upgrade to use PG 13 deduplication). Azure's tuner emits both as recommendations. (brief)
- **Expression index** — an index on a computed value such as `lower(title)`, so `WHERE lower(title) = …` can use it. Ryan Booz's LLM suggested one on `lower()` before knowing an index already existed. (02:35; post)
- **ILIKE** — case-insensitive `LIKE`. With wildcards on both sides it cannot use a B-tree; needs a trigram GIN index. "The ILIKE is probably not the most efficient way." (23:52)
- **Index-only scan** — answer a query from the index alone, skipping the table, when the visibility map says the pages are all-visible; one reason vacuum matters for reads. PG 9.2 (2012). (docs)
- **Inner join** — returns only rows that match on both sides. All the demo query's joins were inner joins, so a Cartesian blow-up was less likely but not impossible. (23:52)
- **Loops (EXPLAIN metric)** — how many times a node executed; times and rows in the plan are per loop. "That's per loop … for each row, it took almost a second. There's two hundred, almost two hundred seconds." (25:22 block)
- **OR-to-UNION rewrite** — split `WHERE a = x OR b = y` into two `UNION`ed queries so each half can use its own index; a pganalyze Query Advisor rule. (brief)
- **ORDER BY / sort** — sorting is a plan node with startup cost and memory needs; extra `ORDER BY`s on large intermediate results are a spill risk. (23:52)
- **ORM** — object-relational mapper that generates SQL for you; a frequent source of accidental correlated subqueries and duplicated work. "Heaven forbid, I went down the ORM." (25:22 block)
- **Parallel query** — splitting a scan, join or aggregate across worker processes; PG 9.6 (2016), off by default until later releases. One of the alternating suggestions Ryan Booz's models offered after the subquery fix ("it looks like it's going parallel. It looks like it's not going parallel"). (47:49 block)
- **Partial index** — an index restricted by a `WHERE` clause (`WHERE status = 'unbilled'`); small and fast when queries always filter the same way. (docs)
- **Query ID (queryid)** — pg_stat_statements' 64-bit hash of a normalized query; the handle Ryan Booz gave the agent over MCP. Not stable across major versions. (47:49 block)
- **Range types (tstzrange)** — Postgres types for intervals; the demo schema's `rental_period`, queried with `lower()`/`upper()`. An index on `lower(rental_period)` already existed. (23:52; brief)
- **Subquery** — a query nested in another; the audience supplied the word when Ryan Booz blanked. Correlated is the dangerous kind. (25:20)
- **WHERE clause / leading wildcard** — the first thing an LLM blames ("wild cards on both sides"); right instinct, wrong priority without the plan. (02:35)

### Settings and logging

- **auto_explain.log_format** — `text` or `json` (also xml/yaml). Ryan Booz: JSON, because tools parse it; logs get bigger. (21:43)
- **auto_explain.log_nested_statements / log_verbose / sample_rate** — capture statements inside functions; print verbose plans; explain only a fraction of statements. All on Ryan Booz's baseline slide except sample_rate. (brief)
- **compute_query_id** — `auto` by default; lets pg_stat_statements turn query-ID computation on. (docs)
- **effective_cache_size** — planner's assumption about OS + Postgres cache available (default 4 GB); higher favours index scans. Alex's DB: ~384 MB. (db)
- **hash_mem_multiplier** — multiplies `work_mem` for hash operations (default 2.0). PG 13. (docs)
- **idle_in_transaction_session_timeout** — kills sessions that sit inside an open transaction, which otherwise block vacuum. Alex's DB: 0 (disabled). (db)
- **jit** — just-in-time compilation of expressions; on by default upstream, off on Alex's Supabase tier. (db)
- **log_duration** — logs every statement's duration with no threshold; a log-bloat source when combined carelessly. (14:47)
- **log_min_error_statement** — logs the statement behind any error at or above a severity (default `error`). Alex's DB: `error`. (brief; db)
- **log_statement** — which classes to log regardless of duration: `none`, `ddl`, `mod`, `all`. Alex's DB: `ddl`. (brief; db)
- **log_min_duration_sample / log_statement_sample_rate** — log a random fraction of slow statements when full logging is too much traffic. (docs)
- **maintenance_work_mem** — memory for `VACUUM`, `CREATE INDEX` and FK builds (default 64 MB). (docs)
- **max_connections** — hard cap on backend processes; the reason poolers exist. Alex's DB: 60. (db)
- **pgaudit** — extension for detailed session/object audit logging; heavy if left wide open. "log_duration, pg_audit … logs get really big." (14:47) Preloaded but not created on Alex's DB. (db)
- **random_page_cost** — planner's price for a random page fetch (default 4.0); lower on SSD/cached data. Alex's DB: 1.1. (db)
- **shared_buffers** — Postgres's own page cache (default 128 MB; guidance 25% of RAM on a dedicated server). Alex's DB: ~224 MB. (brief; db)
- **shared_preload_libraries** — extensions loaded at startup; restart to change. Alex's DB preloads pg_stat_statements, pgaudit, auto_explain, pg_cron, pg_net, pgsodium, pg_tle, plan_filter, supabase_vault, plpgsql, plpgsql_check. (db)
- **statement_timeout** — cancels statements longer than N; Alex's DB: 120 s. (db)
- **statistics target** — per-column detail level for `ANALYZE`; raise on skewed columns. See Statistics. (brief)

### Diagnosis and tuning method

- **Baseline** — the "before" plan and runtime captured with the same parameters and environment, so the "after" can be compared apples to apples. pganalyze Workbooks is built around it. (47:49 block; brief)
- **Bounded tuning loop** — evidence → hypothesis → test → compare → stop. The post-event carousel's distillation of Ryan Booz's method. (carousel)
- **Churn / iterative AI-assisted tuning** — an agent iterating without a stop condition; "we churn way too much … let's churn for an hour." The talk's core risk. (02:35; 47:49 block)
- **Configuration autotune** — automatically tuning GUCs against a workload (OtterTune, DBtune); explicitly not this talk. (08:53)
- **Context (as agent input)** — the plan, stats, schema, config and history a human expert would use; the thing that turned 7/10 index guesses into 10/10 correct diagnoses. (throughout; brief)
- **Context engineering / context servers** — designing what an agent is given; the "fifth generation" of tuning tools that serve curated telemetry over MCP to a general-purpose agent. (brief)
- **CPU bound vs I/O bound** — is the query slow because the disk is busy or because the processor is? `track_io_timing` is how you tell. (14:47)
- **Data distribution / data skew** — how values spread across a column; decides whether an index helps and whether a plan flips on one lopsided value. "Distribution's the bigger one." (62:57; brief)
- **Definition of done** — the stopping rule an agent lacks unless you state it; "tune this. Everything's slow right now. Fix it. Well, I'll just keep going." (47:49 block; post)
- **Five generations of AI DB tuning** — hypothetical-index advisors → managed-cloud recommenders → fixed-logic advisors (pganalyze Query Advisor) → stand-alone AI DBA agents (Xata Agent, archived) → context servers. Pre-event framing. (brief; carousel)
- **"A finding is not a fix"** — the pre-event brief's summary of Supabase's advisor guidance (paraphrase; not verified as a verbatim Supabase quote): a flag still needs a human to weigh it against the schema and access model. (brief)
- **High-cardinality workloads** — many distinct query shapes or values; a pg_stat_statements series topic; fills the `max` slots fast. (brief)
- **Hypothetical index** — an index the planner costs "as if" it existed without building it (HypoPG); the first generation of index advice; still how Azure's tuner works. (brief; carousel)
- **Over-instrumentation / under-instrumentation** — log everything and drown, or log nothing and fly blind; Ryan Booz's longer talk is about the middle. (12:08; 14:47)
- **Planner source-code comments** — the planner's source explains why it prefers one join over another; "like a book"; Ryan Booz's (unsourced) explanation for why LLMs handle Postgres well. (25:22 block; 61:00)
- **Production environment risk** — applying a first-guess fix (non-concurrent index) to prod "could cause mayhem." (08:28)
- **Query / data / stats / config triage** — Ryan Booz's four-way question for any slow query: is it the SQL, the data volume, stale statistics, or a setting? (43:45 slide)
- **Sampling (of cumulative stats)** — reading counters at intervals and differencing, to know when work happened; what monitoring tools do for you. (18:03)
- **Workload** — the read/write mix hitting a table; decides whether an index's write cost is worth it. (brief)

### Agent access, safety and test data

- **AI DBA agent** — a stand-alone LLM agent with direct database access (Xata Agent); the generation that was archived in favour of governed MCP access. (brief)
- **Autonomous tuning (Azure)** — Azure Database for PostgreSQL's recommender; modes `OFF`/`REPORT` only, never applies changes; B-tree only; needs `capture_first_sample` for parameterized queries; uses hypopg. (brief; carousel)
- **capture_first_sample** — Azure query-store setting that keeps one sample parameter value so the tuner can analyze parameterized queries. (brief)
- **Clone / snapshot (Aurora)** — snapshot then restore into an isolated copy in your VPC; "fairly fast." (63:58–64:04)
- **Connection exhaustion** — hypothesised failure where concurrent agents use up the pool; flagged unsourced in the brief, plausible in principle. (brief)
- **Copy-on-write** — share storage until something changes; the mechanism under Neon, Aurora clones, DBLab and Xata branches. (brief)
- **Credential (agent never receives one)** — Xata's principle: the agent names a branch; the server holds the secret. (brief)
- **De-identified / anonymized data** — production data with identities removed so prod-like queries can be tested safely; Tonic, Dalibo's Anonymizer. (65:04; brief)
- **Pseudonymization** — replace values with consistent stand-ins so joins and distributions survive; PostgreSQL Anonymizer 3.2 (September 9, 2026) made it ~40× faster. (brief)
- **Parameter paradox** — you need the raw parameter to reproduce a plan flip and you must not hand it to an agent. (brief)
- **Raw query parameters** — the actual bound values; withheld by pganalyze's MCP server under basic access. (brief)
- **Read-only by default** — the agent can look; writing needs an explicit extra step (Xata's `write=true` + `confirm=true`; Supabase's `read_only=true`). (brief; post)
- **Scales to zero** — a pooler or branch that uses nothing when idle; Xata's pitch. (brief)
- **Subsetting** — a smaller slice of production with the same distribution (Tonic Condenser, RepliByte). (brief)
- **Synthetic data** — generated rows that mimic real distributions without real identities; the audience's ask at 62:23. (65:04)
- **Text-to-SQL** — translating natural-language questions into SQL; accuracy is the question the brief raised about Google's tooling. (brief)
- **VPC** — the private network an Aurora clone stays inside, so the test is isolated but realistic. (63:58)

### Security

- **Apache-2.0** — the license the Xata Agent, DBLab and much Postgres tooling ship under. (brief)
- **CVE-2026-3172** — pgvector buffer overflow in parallel HNSW builds; 0.6.0–0.8.1 affected, fixed in 0.8.2; CVSS 8.1. (brief)
- **DPoP** — token binding so a stolen MCP token cannot be replayed elsewhere; on the MCP roadmap (August 22, 2026). (brief)
- **Enterprise-Managed Authorization** — stable MCP extension for enterprise authorization; same roadmap. (brief)
- **IAM / OAuth** — identity and authorization layers proposed for managed MCP servers after the STDIO RCE disclosure; Supabase's MCP uses OAuth or a personal access token. (brief)
- **Prompt injection** — instructions hidden in data the agent reads (a row, a log line) that steer it into unintended queries; Supabase's stated primary MCP risk. (docs)
- **RCE (STDIO)** — remote-code-execution class vulnerability disclosed by OX Security in an MCP STDIO transport; the trigger for "the database layer absorbs the MCP security surface." (brief)
- **RLS initplan (auth_rls_initplan)** — Supabase advisor flag for policies that call `auth.uid()` per row instead of once; wrap in `(select …)`. (brief)
- **SOC 2 Type 2** — the audit certification enterprise buyers ask for; pganalyze and DBtune hold it. (brief)
- **SQL injection (reference Postgres MCP)** — the archived Anthropic server passed SQL straight through; `COMMIT; DROP SCHEMA …` escaped its read-only transaction; forks inherited it. (brief; Datadog Security Labs)
- **SSRF** — tricking a server into fetching internal addresses; a class the MCP Toolbox hardened against. (brief)
- **Workload Identity Federation** — software proves identity via its runtime platform instead of a stored secret; MCP roadmap item. (brief)

### Community

- **PGSQL Phriday** — monthly rotating-topic Postgres community blogging event founded by Ryan Booz; the meetup series borrows the name. (00:00; brief)
- **PostgreSQL Summit US / PgUS** — the Lower Manhattan conference two weeks after the talk; Ryan Booz spoke and ran a beginner workshop. (00:11; 66:14)

---

## Tools and companies

Format: what it is · relevance · free vs paid · in the room?

- **Anthropic reference Postgres MCP server** — the original read-only Postgres MCP example, now in `modelcontextprotocol/servers-archived` with "no security guarantees" after the SQL-injection read-only bypass · the cautionary tale for live-connection agent access · free (archived) · yes: "the only tool I wouldn't tell you to use … against your prod" (47:49 block).
- **AWS RDS / Aurora** — Amazon's managed Postgres; Aurora adds storage-level fast cloning; RDS hosts Ryan Booz's demo · per Ryan Booz the one major provider enabling pg_stat_statements by default (stated, not verified) · paid · yes (14:47, 21:43, 63:58).
- **Azure Database for PostgreSQL** — Microsoft's managed Postgres with "autonomous tuning" (report-only recommender built on query store and hypopg) · the managed-cloud-recommender generation · paid · yes, as a provider requiring manual enablement (12:08); tuner from the brief.
- **Blue Box** — Ryan Booz's open-source demo database and data generator (a DVD-rental schema that keeps inserting rentals), hosted on RDS for the talk · every example in the talk · free · yes (21:43).
- **Claude / Sonnet / Opus, ChatGPT, Gemini (models)** — the assistants Ryan Booz tested; Sonnet did most of the 60 iterations; Opus and ChatGPT also found the subquery with a plan; Gemini not tried · "the model doesn't matter that much" once context is present · paid APIs · yes (47:49, 60:47–61:18).
- **Crunchy Data / EDB (EnterpriseDB)** — Postgres vendors whose bundled monitoring the brief named as "good enough" alternatives to pganalyze · paid · no.
- **Dalibo** — French Postgres consultancy (since 2005) behind PostgreSQL Anonymizer, the extension for masking and pseudonymizing data in place · the anonymized-clone path · open source · likely yes: the ASR heard "Delevo out of Spain" (62:57); Dalibo is French, so "likely Dalibo" and the country was misremembered.
- **Databricks** — named among platforms with point-in-time branching · no detail given · paid · yes (63:58).
- **Datadog (Database Monitoring)** — bundled observability competitor; an audience member flagged a Datadog talk on prod-like test data at the upcoming conference · paid · yes (47:49 block, 64:55).
- **DBtune** — SaaS that tunes Postgres configuration automatically with machine learning (the brief attributed Bayesian optimization; the vendor site says "agentic AI"); SOC 2 Type II · the live configuration-autotune vendor · paid · yes (09:43).
- **Docker** — how Ryan Booz stood up a default PG 18 to count ~400 GUCs · free · yes (12:08).
- **Google AlloyDB / MCP Toolbox for Databases** — Google's Postgres-compatible managed DB (ScaNN vector index, `ai.*` functions) and its open-source `genai-toolbox` giving agents structured DB access (Database Insights, Advanced Query Insights, Secure Parameters) · the May 27 prior event's subject · AlloyDB paid, Toolbox free · GCP mentioned as needing manual enablement (14:47); Toolbox from the brief.
- **HypoPG** — extension for hypothetical indexes the planner costs without building · first-generation index advice; Azure's tuner and Supabase's index_advisor depend on it · free; available but not installed on Alex's DB · no.
- **libpg_query** — pganalyze's open-source packaging of Postgres's own SQL parser for other software · why pganalyze can normalize and analyze query text off-server · free · no.
- **Neon** — serverless Postgres with instant copy-on-write branching (public December 2022) · "I love what some of those folks are doing" · free tier + paid · yes (63:58).
- **OtterTune** — the ML configuration-tuning company out of Carnegie Mellon (launched 2020, $12M Series A 2022); shut down June 2024 after an acquisition fell through · origin of the "autotune" category · defunct · yes: "No longer exists" (08:53).
- **pg_hint_plan** — NTT OSS Center extension for forcing scan and join choices with SQL-comment hints · used inside pganalyze Workbooks to test plan variants · free · no (brief).
- **pg_stat_monitor** — Percona's alternative to pg_stat_statements with time-bucketed stats · available, not installed on Alex's DB · free · no.
- **pg_trgm** — trigram extension enabling GIN/GiST indexes for `ILIKE '%x%'` and regex · the index the LLM suggested at 02:35; available, not installed on Alex's DB · free · alluded to, not named.
- **pganalyze** — independent, bootstrapped (2012, Lukas Fittl) Postgres monitoring and optimization vendor; Query Advisor, Index Advisor, VACUUM Advisor, Workbooks, Server Groups; SOC 2 Type 2; Ryan Booz is a Solutions Engineer there · the talk's context server · paid · yes (02:35 onward).
- **pganalyze MCP Server** — ~30 tools over pganalyze's collected data; no database connection; basic access withholds parameters and unfiltered plans; 100 requests per billable server per hour in preview; public preview April 30, 2026 · the live demo · included in current plans · yes (09:43, 47:49 block).
- **pganalyze Workbooks** — baseline-vs-variants query comparison with parameter sets and side-by-side plans; collector runs the EXPLAINs · the "definition of done" tooling · paid · yes (47:49 block).
- **pgEdge** — distributed-Postgres vendor; hosted the May 27 NYC Postgres meetup · no.
- **pgNow (Redgate)** — free point-in-time desktop diagnostic (pg_stat_activity, pg_stat_statements time-slicing, index usage, config checks; no history) · from Ryan Booz's Redgate years · free · yes (02:35).
- **pgvector** — see Core. Free · no.
- **pgWatch** — Cybertec's open-source Postgres monitoring with Grafana dashboards (v5, BSD-3) · Ryan Booz's named free alternative to pganalyze for sampling stats · free · yes (18:03).
- **Postgres.ai (Database Lab Engine)** — thin clones in seconds on ZFS/LVM, Apache-2.0, plus commercial editions · the self-hosted branching path · free core · yes, as "Postgres AI" (63:58).
- **PostgreSQL Anonymizer** — see Dalibo.
- **Redgate / Redgate Monitor** — database-tooling company (SQL Server heritage) where Ryan Booz was PostgreSQL Advocate; Redgate Monitor is its monitoring product (ASR: "Radio Monitor") · paid · yes (02:35, 47:49 block).
- **RepliByte** — tool for seeding databases with anonymized, subsetted production-like data · free · no (brief).
- **Supabase** — managed Postgres platform: Supavisor pooler, 30 security/performance advisors ("a finding is not a fix"), an official MCP server with `read_only` and `project_ref` flags, branching (experimental), and an `index_advisor` extension built on hypopg · Alex's system of record · free tier + paid · no (brief; db).
- **Timescale / Tiger Data** — time-series Postgres (TimescaleDB extension); company renamed Tiger Data on June 17, 2025; Ryan Booz's former employer · yes (02:35).
- **Tonic.ai** — synthetic and de-identified test data (Condenser subsetting); founded 2018 by former Palantir engineers (Ian Coe, Karl Hanson, Andrew Colombi) and Adam Kamor; the audience's "spin-off from Palantir" is loosely right (founders, not a corporate spin-off) · paid · yes (65:04–65:39).
- **Xata** — Postgres platform that archived its open-source AI DBA "Xata Agent" (Apache-2.0) on June 15, 2026 and shipped a branch-scoped MCP server (read-only default, gated writes, no credential to the agent) plus "xata scratch" disposable databases · the clearest generation-4-to-5 story · free tier + paid · no (brief; carousel).
- **MySQL / Oracle / SQL Server** — the other major relational databases; named in the CTE-inlining history (they inline; Postgres did not until 12) · yes (40:03).

---

## Corrections and unresolved

Speaker or transcription errors, checked against primary sources.

- **BUFFERS default is PostgreSQL 18, not 15.** Ryan Booz said "as of Postgres fifteen, if you say explain analyze, you get buffers by default." The PG 18 release notes (September 25, 2025) list "Automatically include BUFFERS output in EXPLAIN ANALYZE." Alex's DB is PG 17.6, so `BUFFERS` must still be requested explicitly there.
- **GUC = Grand Unified Configuration, not "Global."** The Postgres source (`src/backend/utils/misc/README`) expands it as Grand Unified Configuration.
- **CTE inlining arrived in PG 12.** Ryan Booz had this right (October 3, 2019); recorded here because it is load-bearing.
- **OtterTune "no longer exists."** Confirmed: Andy Pavlo announced the shutdown in June 2024.
- **"Delevo out of Spain" → likely Dalibo, which is French.** Dalibo (Paris) publishes PostgreSQL Anonymizer, which matches the "anonymize a copy of prod on a schedule" description. Treated as "likely," and the country as misremembered.
- **"Rigby has a product"** — unresolved company name; excluded from the glossary.
- **"Sable" / "Table"** (60:47, 61:18) — a model name Ryan Booz chose not to use; unresolvable from the audio; excluded.
- **"Radio Monitor"** → Redgate Monitor. **"track_ever_timing"** → `track_io_timing`. **"D-stone"** (14:47) → discarded as noise. **"against your product"** (47:49 block) → "against your prod."
- **"Bruce Law, Jim"** (47:49) — the planner-talk speakers Ryan Booz cited; the names did not transcribe cleanly and were not resolved.
- **"AWS is the only provider that automatically enables pg_stat_statements"** — Ryan Booz's stated belief ("as far as I know"); not verified here.
- **"Round about four hundred settings"** on a default PG 18 Docker image — Ryan Booz's own count with possible extension GUCs included; not independently counted.
- **"Fifteen years"** of pganalyze — the company dates from 2012, so about fourteen at the time of the talk; immaterial.
- **Two titles.** The invite and the pre-event material used "Postgres Tuning in the Age of AI: Context Is Everything"; the slide read "Query Tuning in the Age of AI: Who Wins?"
- **Tonic "spin-off from Palantir"** (audience, 65:12) — the founders came from Palantir; the company was not a corporate spin-off.
- **pgvector ceiling "~10M vectors"** — from the pre-event prior-context pack; not re-verified.
- **Exact introduction versions** for `work_mem` (renamed from `sort_mem`), bitmap scans, `log_min_duration_statement` and the GUC subsystem itself are left unstated rather than guessed.

---

## Sources

Primary sources fetched for this glossary (PostgreSQL docs and release notes unless noted):

- PostgreSQL 18.0 release notes — https://www.postgresql.org/docs/release/18.0/
- PostgreSQL 17.0 — https://www.postgresql.org/docs/release/17.0/
- PostgreSQL 16.0 — https://www.postgresql.org/docs/release/16.0/
- PostgreSQL 15.0 — https://www.postgresql.org/docs/release/15.0/
- PostgreSQL 13.0 — https://www.postgresql.org/docs/release/13.0/
- PostgreSQL 12.0 — https://www.postgresql.org/docs/release/12.0/
- PostgreSQL 10.0 — https://www.postgresql.org/docs/release/10.0/
- PostgreSQL 9.6 — https://www.postgresql.org/docs/release/9.6/
- PostgreSQL 9.5 — https://www.postgresql.org/docs/release/9.5/
- PostgreSQL 9.2 — https://www.postgresql.org/docs/release/9.2/
- PostgreSQL 9.1 — https://www.postgresql.org/docs/release/9.1/
- PostgreSQL 9.0 — https://www.postgresql.org/docs/release/9.0/
- PostgreSQL 8.4 — https://www.postgresql.org/docs/release/8.4/
- PostgreSQL 8.2 — https://www.postgresql.org/docs/release/8.2/
- PostgreSQL 8.1 — https://www.postgresql.org/docs/release/8.1/
- PostgreSQL 7.2 — https://www.postgresql.org/docs/release/7.2/
- PostgreSQL 6.5 — https://www.postgresql.org/docs/release/6.5.0/
- PostgreSQL 18.6 / 19 beta 3 announcement — https://www.postgresql.org/about/news/postgresql-186-1711-1615-1519-1424-and-19-beta-3-released-3365/
- Glossary — https://www.postgresql.org/docs/current/glossary.html
- A Brief History of PostgreSQL — https://www.postgresql.org/docs/current/history.html
- auto_explain — https://www.postgresql.org/docs/current/auto-explain.html
- pg_stat_statements — https://www.postgresql.org/docs/current/pgstatstatements.html
- Run-time statistics (track_io_timing) — https://www.postgresql.org/docs/current/runtime-config-statistics.html
- Logging (log_min_duration_statement etc.) — https://www.postgresql.org/docs/current/runtime-config-logging.html
- Resource consumption (work_mem, shared_buffers) — https://www.postgresql.org/docs/current/runtime-config-resource.html
- Query planning (cost constants, geqo, plan_cache_mode) — https://www.postgresql.org/docs/current/runtime-config-query.html
- EXPLAIN — https://www.postgresql.org/docs/current/sql-explain.html
- Using EXPLAIN — https://www.postgresql.org/docs/current/using-explain.html
- Planner/Optimizer — https://www.postgresql.org/docs/current/planner-optimizer.html
- Statistics used by the planner — https://www.postgresql.org/docs/current/planner-stats.html
- WITH queries (CTEs) — https://www.postgresql.org/docs/current/queries-with.html
- PREPARE (generic vs custom plans) — https://www.postgresql.org/docs/current/sql-prepare.html
- CREATE INDEX — https://www.postgresql.org/docs/current/sql-createindex.html
- pg_trgm — https://www.postgresql.org/docs/current/pgtrgm.html
- BRIN — https://www.postgresql.org/docs/current/brin.html
- Cumulative statistics system — https://www.postgresql.org/docs/current/monitoring-stats.html
- Routine vacuuming — https://www.postgresql.org/docs/current/routine-vacuuming.html
- MVCC introduction — https://www.postgresql.org/docs/current/mvcc-intro.html
- Row security policies — https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Packaging related objects into an extension — https://www.postgresql.org/docs/current/extend-extensions.html
- GUC README (Grand Unified Configuration) — https://github.com/postgres/postgres/blob/master/src/backend/utils/misc/README
- PostgreSQL Anonymizer 3.2 — https://www.postgresql.org/about/news/postgresql-anonymizer-32-faster-pseudonymization-3373/
- pgvector README and CHANGELOG — https://github.com/pgvector/pgvector · https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md
- HNSW paper (Malkov & Yashunin, 2016) — https://arxiv.org/abs/1603.09320
- pgvector 0.8.2 / CVE-2026-3172 — https://www.postgresql.org/about/news/pgvector-082-released-3245 · https://github.com/pgvector/pgvector/issues/959
- Supabase: connecting to Postgres (Supavisor) — https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase: Supavisor 1.0 — https://supabase.com/blog/supavisor-postgres-connection-pooler
- Supabase: database advisors — https://supabase.com/docs/guides/database/database-advisors
- Supabase: MCP server — https://supabase.com/docs/guides/getting-started/mcp
- Supabase: Row Level Security — https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase: pgvector — https://supabase.com/docs/guides/database/extensions/pgvector
- Supabase index_advisor — https://github.com/supabase/index_advisor
- PgBouncer configuration — https://www.pgbouncer.org/config.html
- PgBouncer 1.0 announcement (Skype, March 13, 2007) — https://www.postgresql.org/message-id/54333.194.126.108.9.1173801248.squirrel%40mail.skype.net
- Anthropic: Introducing the Model Context Protocol — https://www.anthropic.com/news/model-context-protocol
- MCP archived servers — https://github.com/modelcontextprotocol/servers-archived
- Datadog Security Labs: SQL injection in the Postgres MCP server — https://securitylabs.datadoghq.com/articles/mcp-vulnerability-case-study-SQL-injection-in-the-postgresql-mcp-server/
- MCP specification update (July 28, 2026) and roadmap (August 22, 2026) — https://blog.modelcontextprotocol.io/posts/2026-07-28/ · https://blog.modelcontextprotocol.io/posts/mcp-roadmap/
- pganalyze: MCP server docs — https://pganalyze.com/docs/mcp
- pganalyze: MCP server public preview — https://pganalyze.com/blog/mcp-server-public-preview
- pganalyze: Workbooks — https://pganalyze.com/docs/workbooks
- pganalyze: About — https://pganalyze.com/about
- pganalyze: Query Advisor insights — https://pganalyze.com/blog/new-query-advisor-insights
- Xata: Introducing the Xata MCP server — https://xata.io/blog/introducing-the-xata-mcp-server
- Xata Agent (archived June 15, 2026) — https://github.com/xataio/agent
- Azure: autonomous tuning — https://learn.microsoft.com/en-us/azure/postgresql/monitor/concepts-autonomous-tuning
- HypoPG — https://github.com/HypoPG/hypopg
- pg_hint_plan — https://github.com/ossc-db/pg_hint_plan
- pgwatch — https://github.com/cybertec-postgresql/pgwatch
- Redgate pgNow — https://documentation.red-gate.com/pgnow · https://www.postgresql.org/about/news/pgnow-v100-released-free-fast-postgresql-monitoring-and-diagnostics-3114
- Neon branching — https://neon.com/docs/introduction/branching
- Postgres.ai Database Lab Engine — https://postgres.ai/docs/database-lab
- Aurora cloning — https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora-Managing-Clone.html
- OtterTune shutdown (Andy Pavlo, June 2024) — https://www.cs.cmu.edu/~pavlo/blog/2025/01/2024-databases-retrospective.html
- Dalibo Labs: PostgreSQL Anonymizer — https://labs.dalibo.com/postgresql_anonymizer
- DBtune — https://www.dbtune.com/
- Tiger Data (Timescale rename, June 17, 2025) — https://www.tigerdata.com/newsroom/timescale-becomes-tiger-data-defining-a-new-standard-as-the-fastest-postgresql-platform-for-modern-applications
- Tonic.ai origin (TechCrunch, December 2020) — https://techcrunch.com/2020/12/14/tonic-synthetic-data/
- Google MCP Toolbox releases — https://github.com/googleapis/genai-toolbox/releases
- Ryan Booz (PostgreSQL Person of the Week) — https://postgresql.life/post/ryan_booz/

Corpus inputs: `harvest_transcript.md`, `harvest_briefs.md`, `02_notion_pre_event_extras.md`, `05_transcript_elevenlabs.md`, `db_inspection.md` (read-only inspection of Supabase project `oicikjyzmxqfomrrqkvf`, 2026-09-17).
