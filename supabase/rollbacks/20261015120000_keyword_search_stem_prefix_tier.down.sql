-- ROLLBACK for 20261015120000_keyword_search_stem_prefix_tier.sql (ADR-0014).
-- NOT in supabase/migrations/ on purpose: the CLI would apply it as a forward
-- migration. Run it by hand (psql -f) to restore the ADR-0009 definition, i.e.
-- keyword_search with the AND -> exact-OR fallback and no stem-prefix tier. It is
-- the 20260710120000 function body verbatim, so rolling back changes recall only;
-- the visibility predicate is identical in both directions.
--
-- backend/test_keyword_stem_tolerance.py applies this file and the forward
-- migration inside one rolled-back transaction to prove both directions.

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
      ) as tsq_or_raw
  ),
  q as (
    select
      tsq_and,
      case when numnode(tsq_or_raw) > 0 then tsq_or_raw else null::tsquery end as tsq_or
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
      -- match tier: 1 = matched the AND query, 2 = OR-fallback only. Deterministic
      -- per chunk (function of c.content_tsv and the fixed queries), so it is
      -- identical across a chunk's ACL rows and never disturbs the distinct-on pick.
      case when c.content_tsv @@ q.tsq_and then 1 else 2 end as match_tier,
      -- rank against whichever query the row matched, AND preferred. AND rows keep
      -- exactly today's ts_rank_cd(content_tsv, tsq_and) value.
      case
        when c.content_tsv @@ q.tsq_and
          then ts_rank_cd(c.content_tsv, q.tsq_and)
        else ts_rank_cd(c.content_tsv, q.tsq_or)
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
  -- AND rows (match_tier 1) always rank above OR-fallback rows (match_tier 2);
  -- within each block the ordering stays similarity desc, id asc. With the limit,
  -- OR rows only surface into slots AND left empty.
  order by sub.match_tier asc, sub.similarity desc, sub.id asc
  limit greatest(match_count, 0);
$$;

grant execute on function public.keyword_search(
  text, int, text[], text, date, date, uuid
) to authenticated;
