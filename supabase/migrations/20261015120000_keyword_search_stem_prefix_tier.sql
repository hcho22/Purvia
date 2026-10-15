-- ADR-0014: add a stem-tolerant PREFIX tier to keyword_search so a question word
-- and a chunk word that share a root but not a Snowball stem still match
-- ("respond" vs "response").
--
-- WHY: the english dictionary stems `respond` -> `respond` but `response` ->
-- `respons`, so neither the AND query nor the exact-lexeme OR fallback (ADR-0009)
-- can connect "How quickly do you respond to my messages?" to the chunk that
-- literally says "First response within 60 seconds". The vector leg misses it too
-- (cosine 0.2265 < the 0.3 floor), so a viewer whose visible set holds only that
-- chunk retrieved ZERO rows and the weekly RAGAS run could not score the row
-- (issue #172, q40 x partial_access).
--
-- WHAT: a third match tier. For every normalized query lexeme of 6+ letters, drop
-- its last character and prefix-match (`respon:*`) against the chunk's lexemes.
-- Tier 1 (AND) and tier 2 (exact-lexeme OR) are byte-for-byte unchanged and always
-- rank above tier 3; tier 3 only fills slots the first two tiers left empty, so a
-- query that already filled `match_count` returns identical rows, similarities and
-- order. Short lexemes (< 6 letters), digits and identifiers (`err-4102`) are never
-- widened, so exact-token lookups stay exact.
--
-- The prefix tsquery uses the `simple` config so the truncated stem is compared to
-- the chunk's already-stemmed lexemes as-is (it is not re-stemmed), and it is
-- served by the existing content_tsv GIN index.
--
-- SECURITY: a recall change, not a visibility change. The whole visibility block
-- (owner-OR-ACL, workspace-membership EXISTS, deleted_at, filter_workspace_id,
-- metadata filters) and the granting-principal projection are copied verbatim from
-- 20260710120000_keyword_search_or_fallback.sql; the extra tier only widens which
-- chunks are CONSIDERED. No `role` / `is_bot` appears (core invariant 1).
--
-- Byte-identical 7-parameter signature, return table, `security invoker`, and
-- GRANT: the backend caller needs no change. Reversible: see
-- supabase/rollbacks/20261015120000_keyword_search_stem_prefix_tier.down.sql.

drop function if exists public.keyword_search(
  text, int, text[], text, date, date, uuid
);

create function public.keyword_search(
  query text,
  match_count int default 5,
  filter_topics text[] default null,
  filter_document_type text default null,
  filter_date_from date default null,
  filter_date_to date default null,
  filter_workspace_id uuid default null
)
returns table (
  id uuid,
  document_id uuid,
  chunk_index int,
  content text,
  similarity float,
  filename text,
  granting_principal_id uuid,
  granting_principal_display text
)
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  -- tsq_and: the current AND matcher (unchanged). tsq_or: the same query rebuilt
  -- as an OR over its normalized lexemes. Building tsq_or from
  -- tsvector_to_array(to_tsvector(...)) guarantees each element is an already-
  -- normalized lexeme (no tsquery operators to parse), and the numnode guard maps
  -- a stopword-only / empty query to null so it matches nothing rather than erroring.
  with raw as (
    select
      websearch_to_tsquery('english'::regconfig, coalesce(query, '')) as tsq_and,
      to_tsquery(
        'english'::regconfig,
        array_to_string(
          tsvector_to_array(to_tsvector('english'::regconfig, coalesce(query, ''))),
          ' | '
        )
      ) as tsq_or_raw,
      -- tier 3: drop the last character of each 6+ letter lexeme and prefix-match.
      -- Letters only (`^[a-z]{6,}$`): identifiers and numbers are never widened.
      to_tsquery(
        'simple'::regconfig,
        array_to_string(
          array(
            select left(l, length(l) - 1) || ':*'
            from unnest(tsvector_to_array(to_tsvector('english'::regconfig, coalesce(query, '')))) as l
            where l ~ '^[a-z]{6,}$'
          ),
          ' | '
        )
      ) as tsq_pre_raw
  ),
  q as (
    select
      tsq_and,
      case when numnode(tsq_or_raw) > 0 then tsq_or_raw else null::tsquery end as tsq_or,
      case when numnode(tsq_pre_raw) > 0 then tsq_pre_raw else null::tsquery end as tsq_pre
    from raw
  )
  select
    sub.id,
    sub.document_id,
    sub.chunk_index,
    sub.content,
    sub.similarity,
    sub.filename,
    sub.granting_principal_id,
    sub.granting_principal_display
  from (
    select distinct on (c.id)
      c.id,
      c.document_id,
      c.chunk_index,
      c.content,
      -- match tier: 1 = matched the AND query, 2 = exact-lexeme OR fallback,
      -- 3 = stem-prefix fallback only. Deterministic per chunk (function of
      -- c.content_tsv and the fixed queries), so it is identical across a chunk's
      -- ACL rows and never disturbs the distinct-on pick.
      case
        when c.content_tsv @@ q.tsq_and then 1
        when c.content_tsv @@ q.tsq_or then 2
        else 3
      end as match_tier,
      -- rank against whichever query the row matched, AND preferred. Tier 1 and 2
      -- rows keep exactly today's ts_rank_cd values.
      case
        when c.content_tsv @@ q.tsq_and
          then ts_rank_cd(c.content_tsv, q.tsq_and)
        when c.content_tsv @@ q.tsq_or
          then ts_rank_cd(c.content_tsv, q.tsq_or)
        else ts_rank_cd(c.content_tsv, q.tsq_pre)
      end::float as similarity,
      d.filename,
      case
        when c.user_id = auth.uid() then null::uuid
        else ca.principal_id
      end as granting_principal_id,
      case
        when c.user_id = auth.uid() then 'owner'::text
        when ca.principal_type = 'user' then (
          select p.email from public.profiles p where p.id = auth.uid()
        )
        when ca.principal_type = 'group' then (
          select pr.name from public.principals pr where pr.id = ca.principal_id
        )
      end as granting_principal_display
    from public.chunks c
    join public.documents d on d.id = c.document_id
    left join public.chunk_acl ca on ca.chunk_id = c.id
      and (
        (ca.principal_type = 'user' and ca.principal_id = auth.uid())
        or (
          ca.principal_type = 'group'
          and ca.principal_id in (
            select pm.principal_id
            from public.principal_membership pm
            where pm.member_user_id = auth.uid()
          )
        )
      )
    cross join q
    where (
        c.content_tsv @@ q.tsq_and
        or (q.tsq_or is not null and c.content_tsv @@ q.tsq_or)
        or (q.tsq_pre is not null and c.content_tsv @@ q.tsq_pre)
      )
      and d.deleted_at is null
      and (c.user_id = auth.uid() or ca.chunk_id is not null)
      and exists (
        select 1
        from public.workspace_membership wm
        where wm.workspace_id = d.workspace_id
          and wm.user_id = auth.uid()
      )
      -- US-070 non-security narrowing filter (mirror of match_chunks): when set,
      -- restrict to one workspace's documents. AND-ed, so subtractive only.
      and (filter_workspace_id is null or d.workspace_id = filter_workspace_id)
      and (
        filter_topics is null
        or (d.metadata ? 'topics' and d.metadata->'topics' ?| filter_topics)
      )
      and (
        filter_document_type is null
        or d.metadata->>'document_type' = filter_document_type
      )
      and (
        filter_date_from is null
        or (d.metadata->>'published_date')::date >= filter_date_from
      )
      and (
        filter_date_to is null
        or (d.metadata->>'published_date')::date <= filter_date_to
      )
    order by
      c.id,
      case
        when c.user_id = auth.uid() then 1
        when ca.principal_type = 'user' then 2
        when ca.principal_type = 'group' then 3
      end asc,
      ca.created_at asc nulls first,
      ca.principal_id asc nulls first
  ) sub
  -- Tier 1 (AND) ranks above tier 2 (exact OR) above tier 3 (stem prefix); within
  -- each block the ordering stays similarity desc, id asc. With the limit, lower
  -- tiers only surface into slots the higher tiers left empty.
  order by sub.match_tier asc, sub.similarity desc, sub.id asc
  limit greatest(match_count, 0);
$$;

grant execute on function public.keyword_search(
  text, int, text[], text, date, date, uuid
) to authenticated;
