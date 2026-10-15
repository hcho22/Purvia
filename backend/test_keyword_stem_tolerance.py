"""ADR-0014 keyword stem-prefix tier, LIVE against Postgres.

Pins three claims about `public.keyword_search` after
20261015120000_keyword_search_stem_prefix_tier.sql:

  1. THE REPORTED MISS IS CLOSED (issue #172). The golden-set question q40 ("How
     quickly do you respond to my messages?") through a viewer whose visible set
     holds only the gold chunk (`customer-service-sop:0`, which says "First
     response within 60 seconds") returns ZERO rows on the pre-migration
     (ADR-0009) function and returns the gold chunk after. "respond" and
     "response" stem differently, so neither the AND query nor the exact-lexeme OR
     fallback connected them.

  2. THE CHANGE IS STRICTLY ADDITIVE. For every golden-set question, at several
     `match_count`s, the rows the old function returned are an exact prefix of the
     new function's rows (same chunk, same similarity, same order). The new tier
     can only fill slots the old tiers left empty.

  3. IT IS A RECALL CHANGE, NEVER A VISIBILITY CHANGE. A same-workspace member
     with no grant, a non-member, and a soft-deleted document all still return zero
     rows for q40 under the new function.

Everything runs inside ONE transaction that is rolled back, including the
`create or replace` swaps between the rollback script and the forward migration,
so the shared local database is left exactly as found and both directions of the
migration are exercised from the files on disk.

Run:
    python -m backend.test_keyword_stem_tolerance

Needs a local Postgres with the Supabase schema (DATABASE_URL, e.g.
postgresql://postgres:postgres@127.0.0.1:54322/postgres). Skips cleanly when
DATABASE_URL is unset or unreachable. Needs no OpenAI and no PostgREST.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import asyncpg
import yaml

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "supabase" / "migrations" / "20261015120000_keyword_search_stem_prefix_tier.sql"
DOWN = ROOT / "supabase" / "rollbacks" / "20261015120000_keyword_search_stem_prefix_tier.down.sql"
CORPUS = ROOT / "db_seed" / "corpus"
GOLD = ROOT / "evals" / "retrieval" / "retrieval_gold.yaml"

INSTANCE = "00000000-0000-0000-0000-000000000000"
EMBEDDING = "[" + ",".join(["1"] + ["0"] * 1535) + "]"
Q40 = "How quickly do you respond to my messages?"
# The shipped corpus is chunked at ~2k chars; chunk 0 of the SOP is the one that
# carries the response-time targets. The whole-file text up to this length holds
# the same sentence, which is all the lexical leg sees.
CHUNK_CHARS = 2300


def _uid(user_id: str) -> str:
    return json.dumps({"sub": user_id, "role": "authenticated"})


async def _as_user(conn: asyncpg.Connection, user_id: str) -> None:
    await conn.execute("set local role authenticated")
    await conn.execute("select set_config('request.jwt.claims', $1, true)", _uid(user_id))


async def _as_admin(conn: asyncpg.Connection) -> None:
    await conn.execute("reset role")


async def _search(
    conn: asyncpg.Connection, user_id: str, query: str, match_count: int
) -> list[tuple[str, float]]:
    await _as_user(conn, user_id)
    try:
        rows = await conn.fetch(
            "select id::text, similarity from public.keyword_search($1, $2)",
            query,
            match_count,
        )
    finally:
        await _as_admin(conn)
    return [(r["id"], float(r["similarity"])) for r in rows]


async def _mk_user(conn: asyncpg.Connection, tag: str) -> str:
    uid = str(uuid.uuid4())
    await conn.execute(
        """
        insert into auth.users
          (id, instance_id, email, encrypted_password, aud, role,
           raw_app_meta_data, raw_user_meta_data, created_at, updated_at, email_confirmed_at)
        values ($1, $2, $3, '', 'authenticated', 'authenticated',
                '{}'::jsonb, '{}'::jsonb, now(), now(), now())
        """,
        uid, INSTANCE, f"{tag}-{uid[:8]}@test.local",
    )
    return uid


async def _mk_doc(
    conn: asyncpg.Connection, owner: str, ws: str, filename: str, content: str
) -> tuple[str, str]:
    doc_id, chunk_id = str(uuid.uuid4()), str(uuid.uuid4())
    await conn.execute(
        """
        insert into public.documents
          (id, user_id, filename, storage_path, byte_size, status, chunks_count,
           uploaded_at, workspace_id)
        values ($1, $2, $3, 'seed/path', 1, 'ready', 1, now(), $4)
        """,
        doc_id, owner, filename, ws,
    )
    # content_tsv is GENERATED from content; never insert it.
    await conn.execute(
        """
        insert into public.chunks (id, document_id, user_id, chunk_index, content, embedding)
        values ($1, $2, $3, 0, $4, $5::vector)
        """,
        chunk_id, doc_id, owner, content, EMBEDDING,
    )
    return doc_id, chunk_id


async def _run() -> None:
    db_url = os.environ.get("KEYWORD_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("SKIP: KEYWORD_TEST_DATABASE_URL/DATABASE_URL unset")
        return
    try:
        conn = await asyncpg.connect(db_url)
    except (OSError, asyncpg.PostgresError) as exc:
        print(f"SKIP: cannot connect to the database ({exc})")
        return

    checks = 0
    tx = conn.transaction()
    await tx.start()
    try:
        if not await conn.fetchval("select to_regclass('public.chunk_acl') is not null"):
            print("SKIP: Supabase schema (chunk_acl) absent")
            return

        up_sql = UP.read_text(encoding="utf-8")
        down_sql = DOWN.read_text(encoding="utf-8")

        ws = str(uuid.uuid4())
        await conn.execute("insert into public.workspaces (id, name) values ($1, 'KW-STEM')", ws)
        owner = await _mk_user(conn, "owner")
        partial = await _mk_user(conn, "partial")       # sees ONLY the gold chunk via ACL
        ungranted = await _mk_user(conn, "ungranted")   # member, no grant
        outsider = await _mk_user(conn, "outsider")     # not a member of ws
        for u in (owner, partial, ungranted):
            await conn.execute(
                "insert into public.workspace_membership (workspace_id, user_id, role) "
                "values ($1, $2, 'member')",
                ws, u,
            )

        # The shipped corpus, one chunk per file, all owned by `owner`.
        chunk_ids: dict[str, str] = {}
        doc_ids: dict[str, str] = {}
        for path in sorted(CORPUS.glob("*.md")):
            doc_ids[path.stem], chunk_ids[path.stem] = await _mk_doc(
                conn, owner, ws, path.name, path.read_text(encoding="utf-8")[:CHUNK_CHARS]
            )
        sop = chunk_ids["customer-service-sop"]
        await conn.execute(
            "insert into public.chunk_acl (chunk_id, principal_type, principal_id, granted_by) "
            "values ($1, 'user', $2, $3)",
            sop, partial, owner,
        )

        # ---- Claim 1: q40 x partial viewer, old function vs new ----
        await conn.execute(down_sql)
        old_partial = await _search(conn, partial, Q40, 10)
        assert old_partial == [], (
            f"precondition: the pre-migration function must return ZERO rows for q40 "
            f"through the partial viewer (that is the reported miss), got {old_partial}"
        )
        old_owner_cache = {}
        ident_queries = ("ZZQXW-4102", "WEBHOOK_RETRY_MAX", "ERR-4102")
        old_ident = {q: await _search(conn, owner, q, 5) for q in ident_queries}
        questions = yaml.safe_load(GOLD.read_text(encoding="utf-8"))["questions"]
        for q in questions:
            for k in (3, 5, 10):
                old_owner_cache[(q["id"], k)] = await _search(conn, owner, q["question"], k)
        checks += 1
        print("  main (ADR-0009 function): q40 x partial viewer -> 0 rows (the miss reproduced)")

        await conn.execute(up_sql)
        new_partial = await _search(conn, partial, Q40, 10)
        assert [cid for cid, _ in new_partial] == [sop], (
            f"after the migration q40 must return exactly the gold chunk, got {new_partial}"
        )
        checks += 1
        print("  migrated: q40 x partial viewer -> exactly customer-service-sop (gold)")

        # ---- Claim 2: strictly additive across the whole golden set ----
        widened = 0
        for q in questions:
            for k in (3, 5, 10):
                old = old_owner_cache[(q["id"], k)]
                new = await _search(conn, owner, q["question"], k)
                assert new[: len(old)] == old, (
                    f"{q['id']} @ k={k}: the old rows are not an exact prefix of the new "
                    f"rows (the tier must only fill empty slots)\n old={old}\n new={new}"
                )
                if len(new) > len(old):
                    widened += 1
        checks += 1
        print(
            f"  additive: {len(questions)} golden questions x 3 match_counts - old rows are "
            f"an exact prefix of new rows ({widened} cells gained rows, 0 changed)"
        )

        # ---- Claim 3: visibility unchanged ----
        assert await _search(conn, ungranted, Q40, 10) == [], (
            "LEAK: a member with no grant retrieved a chunk"
        )
        assert await _search(conn, outsider, Q40, 10) == [], (
            "LEAK: a non-member retrieved a chunk"
        )
        await conn.execute(
            "update public.documents set deleted_at = now() where id = $1", doc_ids["customer-service-sop"]
        )
        assert await _search(conn, partial, Q40, 10) == [], (
            "LEAK: a soft-deleted document was retrieved through the prefix tier"
        )
        await conn.execute(
            "update public.documents set deleted_at = null where id = $1", doc_ids["customer-service-sop"]
        )
        checks += 1
        print("  isolation: ungranted member, non-member, soft-deleted doc -> 0 rows")

        # ---- Exact tokens stay exact: digits/identifiers are never prefix-widened ----
        for q in ident_queries:
            assert await _search(conn, owner, q, 5) == old_ident[q], (
                f"identifier query {q!r} changed; digits/identifiers must not be widened"
            )
        checks += 1
        print("  identifiers: exact-token queries return exactly the pre-migration rows")

        # ---- Rollback path is the exact previous definition ----
        await conn.execute(down_sql)
        assert await _search(conn, partial, Q40, 10) == []
        checks += 1
        print("  rollback script restores the ADR-0009 behaviour (q40 -> 0 rows again)")
    finally:
        await tx.rollback()
        await conn.close()

    print(f"\nPASS: {checks} keyword stem-prefix tier checks (transaction rolled back)")


if __name__ == "__main__":
    asyncio.run(_run())
