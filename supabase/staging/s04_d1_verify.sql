-- =====================================================================
-- S-04 D1 VERIFY — behavioural assertions for the PII Phase-2 backstop
-- (docs/adr/proposals/pii-db-check.sql as fixed in PR #249) plus the
-- legacy-column drop (supabase/migrations/0014_drop_legacy_person_email.sql).
--
-- One DO block = one transaction. It inserts probe rows, asserts what must
-- succeed AND what must be REJECTED, deletes the probes, and checks that
-- pre-existing row counts are unchanged. Any miss RAISEs, which rolls back
-- every probe automatically. Success prints:
--   NOTICE  S-04 D1 VERIFY: PASS (n checks)
--
-- Same behavioural doctrine as staging/s1a_verify.sql (review finding 1d):
-- reading catalog rows proves what was ADDED, never what a trigger actually
-- refuses. The refusals are exercised, not assumed.
--
-- Fixture hygiene (AGENTS.md rule 4): every PII-shaped string below is fake —
-- `*.example` domains and the reserved-fiction 555-01xx exchange. Nothing here
-- is contact data.
--
-- The file must pass on BOTH legs of the rehearsal:
--   pre-drop  (pii-db-check.sql applied, legacy email column still present)
--   post-drop (0014 applied, email column gone — populated-column refusal is
--              then structurally unreachable and the catalog is the proof;
--              the nulling-update tolerance test is likewise skipped)
-- =====================================================================
do $verify$
declare
  n            int := 0;
  c            int;
  people_before bigint;
  probe_id     uuid;
  cv2_exists   boolean;
  email_col    boolean;
begin
  select count(*) into people_before from public.person;
  select exists (select 1 from information_schema.tables
                 where table_schema = 'canonical_v2' and table_name = 'person')
    into cv2_exists;
  select exists (select 1 from information_schema.columns
                 where table_schema = 'public' and table_name = 'person'
                   and column_name = 'email')
    into email_col;

  -- ---------- structure: the backstop's functions and triggers exist ----------
  select count(*) into c from pg_proc
   where pronamespace = 'public'::regnamespace
     and proname in ('assert_no_contact_pii', 'assert_no_pii_columns');
  if c <> 2 then raise exception 'FAIL: expected 2 assert_no_* functions in public, found %', c; end if;
  n := n + 1;

  select count(*) into c from pg_trigger
   where not tgisinternal
     and tgrelid = 'public.person'::regclass
     and tgname in ('person_no_contact_pii', 'person_no_pii_columns');
  if c <> 2 then raise exception 'FAIL: expected 2 PII triggers on public.person, found %', c; end if;
  n := n + 1;

  -- Part 3's catalog guard: cv2 triggers exist IFF canonical_v2.person does.
  if cv2_exists then
    select count(*) into c from pg_trigger
     where not tgisinternal
       and tgrelid = 'canonical_v2.person'::regclass
       and tgname in ('cv2_person_no_contact_pii', 'cv2_person_no_pii_columns');
    if c <> 2 then raise exception 'FAIL: canonical_v2.person exists but its 2 cv2 PII triggers were not found, found %', c; end if;
  else
    select count(*) into c from pg_trigger
     where not tgisinternal and tgname like 'cv2\_person\_no\_%';
    if c <> 0 then raise exception 'FAIL: cv2 PII triggers exist but canonical_v2.person does not'; end if;
  end if;
  n := n + 1;

  -- ---------- clean spine write passes (normal spine shape, allowlisted columns) ----------
  insert into public.person (id, name, title, bio, role_context, source, metadata)
  values (gen_random_uuid(), '__s04_probe__ clean', 'Probe Title',
          'Documentarian covering NYC AI showcases; writes about agentic systems.',
          'probe', 's04_d1_verify', '{"probe": true}'::jsonb)
  returning id into probe_id;
  n := n + 1;

  -- ---------- the gate must CATCH: email pattern in bio ----------
  -- Each refusal must carry the ADR-9 prefix AND name the table (Part 3's
  -- label promise — rehearse_s04_d1.py bring-up fixed a template that
  -- rendered "in person.public.person.").
  begin
    insert into public.person (id, name, bio, source)
    values (gen_random_uuid(), '__s04_probe__ email-in-bio',
            'Ping me at s04.probe@company.example and I will reply.', 's04_d1_verify');
    raise exception 'FAIL: email pattern in bio was ACCEPTED';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
  end;
  n := n + 1;

  -- ---------- the gate must CATCH: US phone pattern in title ----------
  begin
    insert into public.person (id, name, title, source)
    values (gen_random_uuid(), '__s04_probe__ phone-in-title',
            'Call (212) 555-0134 now', 's04_d1_verify');
    raise exception 'FAIL: phone pattern in title was ACCEPTED';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
  end;
  n := n + 1;

  -- ---------- the gate must CATCH: E.164 compact phone in bio ----------
  begin
    insert into public.person (id, name, bio, source)
    values (gen_random_uuid(), '__s04_probe__ e164',
            'Direct line +12125550134.', 's04_d1_verify');
    raise exception 'FAIL: E.164 compact phone in bio was ACCEPTED';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%' then raise; end if;
  end;
  n := n + 1;

  -- ---------- the gate must CATCH: populated forbidden column (pre-drop only) ----------
  if email_col then
    begin
      insert into public.person (id, name, email, source)
      values (gen_random_uuid(), '__s04_probe__ populated-email',
              's04.probe@company.example', 's04_d1_verify');
      raise exception 'FAIL: populating the legacy email column was ACCEPTED';
    exception when raise_exception then
      if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
    end;
  else
    -- Post-drop leg: the column is gone on public.person — the populated-column
    -- refusal cannot fire because the column cannot be populated. The catalog
    -- absence is the assertion (and cv2 must not quietly retain it either).
    if exists (select 1 from information_schema.columns
               where table_schema = 'canonical_v2' and table_name = 'person'
                 and column_name = 'email') then
      raise exception 'FAIL: public.person.email was dropped but canonical_v2.person.email survives';
    end if;
  end if;
  n := n + 1;

  -- ---------- nulling-update tolerance (YED-279 defect 1) + clean update ----------
  if email_col then
    update public.person set title = 'Probe Title v2', email = null where id = probe_id;
    n := n + 1;
  end if;

  update public.person set title = 'Probe Title v3' where id = probe_id;
  n := n + 1;

  -- ---------- canonical_v2 leg (only when that table exists) ----------
  if cv2_exists then
    insert into canonical_v2.person (id, name, title, bio, source, metadata)
    values (gen_random_uuid(), '__s04_probe__ cv2 clean', 'Probe Title',
            'Cluster-carried person row without contact detail.', 's04_d1_verify',
            '{"probe": true}'::jsonb);
    n := n + 1;

    begin
      insert into canonical_v2.person (id, name, bio, source)
      values (gen_random_uuid(), '__s04_probe__ cv2 email-in-bio',
              'Reach s04.probe@company.example for a coffee.', 's04_d1_verify');
      raise exception 'FAIL: email pattern in canonical_v2.person.bio was ACCEPTED';
    exception when raise_exception then
      if sqlerrm not like 'ADR-9 tier-2 violation%canonical_v2.person%' then raise; end if;
    end;
    n := n + 1;
  end if;

  -- ---------- cleanup: probes gone, counts unchanged ----------
  delete from public.person where source = 's04_d1_verify';
  if cv2_exists then
    delete from canonical_v2.person where source = 's04_d1_verify';
  end if;

  select count(*) into c from public.person where source = 's04_d1_verify';
  if c <> 0 then raise exception 'FAIL: probe rows survived cleanup'; end if;
  n := n + 1;

  if (select count(*) from public.person) <> people_before then
    raise exception 'FAIL: public.person row count changed by the verify block';
  end if;
  n := n + 1;

  raise notice 'S-04 D1 VERIFY: PASS (% checks)', n;
end
$verify$;
