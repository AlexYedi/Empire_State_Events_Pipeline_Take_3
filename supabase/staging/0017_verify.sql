-- =====================================================================
-- 0017 VERIFY: behavioural assertions for the international-phone backstop
-- (supabase/migrations/0017_pii_backstop_intl_phone.sql, YED-309).
--
-- One DO block = one transaction. It inserts probe rows, asserts what must
-- succeed and what must be REJECTED, deletes the probes, and checks that
-- pre-existing row counts are unchanged. Any miss RAISEs, which rolls back
-- every probe automatically. Success prints:
--   NOTICE  0017 VERIFY: PASS (n checks)
--
-- Same doctrine as staging/s04_d1_verify.sql: refusals are exercised, not
-- read off the catalog.
--
-- Fixture hygiene: every phone-shaped string is reserved or fictional
-- (UK Ofcom drama range 020 7946 0xxx, FR ARCEP 01 99 00, the 555-01xx
-- exchange, all-zero subscriber numbers). Nothing here is contact data.
--
-- The "known false positive" row is asserted REFUSED on purpose: the backstop
-- must behave exactly like the client guard (spine_client.PHONE_RE), and
-- that class is accepted per decision YED-319 (measured by the YED-320 watcher).
-- =====================================================================
do $verify$
declare
  n             int := 0;
  c             int;
  people_before bigint;
  cv2_before    bigint := 0;
  cv2_exists    boolean;
  s             text;
  must_refuse   text[] := array[
    'Call +44 20 7946 0958 after six',                 -- UK, spaces
    '+44-20-7946-0958',                                -- UK, dashes
    '+44.20.7946.0958',                                -- UK, dots
    'Berlin office +49 (0)30 0000 0000',               -- DE, (0) trunk
    'Paris: +33 1 99 00 12 34',                        -- FR, 5 groups
    '+44' || chr(160) || '20' || chr(160) || '7946' || chr(160) || '0958',  -- NBSP separators
    'tel:+44 20 7946 0958',                            -- URI prefix
    '(+44 20 7946 0958)',                              -- parenthesised
    'Call (212) 555-0134 now',                         -- regression: US alt 1
    '1-212-555-0134',                                  -- regression: leading-1 (S-04 A2)
    'E.164 +12125550134 compact',                      -- regression: alt 2
    'revenue +12 345 678 EUR'                          -- KNOWN FALSE POSITIVE (YED-319): pinned refused
  ];
  must_pass     text[] := array[
    'Raised +3.2M ARR on 2026-11-04 12:30:45',
    'Shipped v2.3.4 and 1.2.3-rc.4',
    'Office at +40.7128 -74.0060',
    'Scored +12 345 points',
    'Short +44 20 dial code only',
    'Version +1.2.3.4.5.6.7 chain',
    'ISBN 978-3-16-148410-0'
  ];
begin
  select count(*) into people_before from public.person;
  select exists (select 1 from information_schema.tables
                 where table_schema = 'canonical_v2' and table_name = 'person')
    into cv2_exists;
  if cv2_exists then
    execute 'select count(*) from canonical_v2.person' into cv2_before;
  end if;

  -- ---------- structure: the 0017 function body carries the 3-alternative pattern ----------
  select count(*) into c from pg_proc
   where pronamespace = 'public'::regnamespace
     and proname = 'assert_no_contact_pii'
     and position('\(0\)' in prosrc) > 0;   -- the (0) trunk group only exists in alt 3
  if c <> 1 then raise exception 'FAIL: assert_no_contact_pii does not carry the 0017 international alternative'; end if;
  n := n + 1;

  -- ---------- must REFUSE, each in bio, on public.person ----------
  foreach s in array must_refuse loop
    begin
      insert into public.person (id, name, bio, source)
      values (gen_random_uuid(), '__0017_probe__ refuse', s, '0017_verify');
      raise exception 'FAIL: ACCEPTED on public.person.bio: %', s;
    exception when raise_exception then
      if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
    end;
    n := n + 1;
  end loop;

  -- ---------- the same refusal in title, role_context and metadata (the other scanned surfaces) ----------
  begin
    insert into public.person (id, name, title, source)
    values (gen_random_uuid(), '__0017_probe__ title', 'Desk +44 20 7946 0958', '0017_verify');
    raise exception 'FAIL: ACCEPTED intl phone in title';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
  end;
  n := n + 1;

  begin
    insert into public.person (id, name, role_context, source)
    values (gen_random_uuid(), '__0017_probe__ role', 'reach via +33 1 99 00 12 34', '0017_verify');
    raise exception 'FAIL: ACCEPTED intl phone in role_context';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
  end;
  n := n + 1;

  begin
    insert into public.person (id, name, metadata, source)
    values (gen_random_uuid(), '__0017_probe__ meta',
            '{"note": "desk +44 20 7946 0958"}'::jsonb, '0017_verify');
    raise exception 'FAIL: ACCEPTED intl phone in metadata';
  exception when raise_exception then
    if sqlerrm not like 'ADR-9 tier-2 violation%public.person%' then raise; end if;
  end;
  n := n + 1;

  -- ---------- must PASS ----------
  foreach s in array must_pass loop
    insert into public.person (id, name, bio, source)
    values (gen_random_uuid(), '__0017_probe__ pass', s, '0017_verify');
    n := n + 1;
  end loop;

  -- ---------- cv2 leg (catalog-guarded, like Part 3) ----------
  if cv2_exists then
    begin
      execute $q$insert into canonical_v2.person (id, name, bio, source)
                 values (gen_random_uuid(), '__0017_probe__ cv2', 'Call +44 20 7946 0958', '0017_verify')$q$;
      raise exception 'FAIL: ACCEPTED intl phone on canonical_v2.person';
    exception when raise_exception then
      if sqlerrm not like 'ADR-9 tier-2 violation%' then raise; end if;
    end;
    n := n + 1;
  end if;

  -- ---------- cleanup: probes gone, counts unchanged ----------
  delete from public.person where source = '0017_verify';
  if cv2_exists then
    execute $q$delete from canonical_v2.person where source = '0017_verify'$q$;
  end if;

  select count(*) into c from public.person where source = '0017_verify';
  if c <> 0 then raise exception 'FAIL: probe rows survived cleanup'; end if;
  n := n + 1;

  if (select count(*) from public.person) <> people_before then
    raise exception 'FAIL: public.person row count changed by the verify block';
  end if;
  if cv2_exists then
    execute 'select count(*) from canonical_v2.person' into c;
    if c <> cv2_before then raise exception 'FAIL: canonical_v2.person row count changed'; end if;
  end if;
  n := n + 1;

  raise notice '0017 VERIFY: PASS (% checks)', n;
end
$verify$;
