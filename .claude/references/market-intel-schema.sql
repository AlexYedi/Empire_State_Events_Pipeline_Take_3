-- Market-Intelligence Engine — thin graph spine v1 (Milestone 1)
-- Applied 2026-06-28 to Supabase project Signal_Pipeline_Analytical_Spine (ref abkvgihlbwfloentugtd)
-- via migration `market_intel_graph_spine_v1`. Kept here for version control.
-- 4 first-class objects (company, person, topic, event) + event_entity hyperedge.
-- Event is the temporal hyperedge AND the signal model (a signal = a market-kind event).
-- relevance_score / last_engaged_at / engagement_count = decay+reinforcement lifecycle (stored now, computed later).

create extension if not exists "pgcrypto";

create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;

create table company (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  description     text,
  website         text,
  industry        text[] default '{}',
  funding_stage   text,
  company_type    text default 'operating',
  linkedin_url    text,
  notion_page_id  text,
  source          text,
  relevance_score numeric default 0,
  last_engaged_at timestamptz,
  engagement_count integer default 0,
  metadata        jsonb default '{}',
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);
create unique index company_name_lower_uniq on company (lower(name));
create trigger company_set_updated_at before update on company for each row execute function set_updated_at();

create table person (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  title           text,
  company_id      uuid references company(id) on delete set null,
  linkedin_url    text,
  email           text,
  bio             text,
  role_context    text,
  notion_page_id  text,
  source          text,
  relevance_score numeric default 0,
  last_engaged_at timestamptz,
  engagement_count integer default 0,
  metadata        jsonb default '{}',
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);
create index person_company_idx on person (company_id);
create trigger person_set_updated_at before update on person for each row execute function set_updated_at();

create table topic (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  description     text,
  notion_page_id  text,
  source          text,
  relevance_score numeric default 0,
  last_engaged_at timestamptz,
  engagement_count integer default 0,
  metadata        jsonb default '{}',
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);
create unique index topic_name_lower_uniq on topic (lower(name));
create trigger topic_set_updated_at before update on topic for each row execute function set_updated_at();

create table event (
  id              uuid primary key default gen_random_uuid(),
  title           text not null,
  kind            text not null,
  event_date      timestamptz,
  description     text,
  url             text,
  source          text,
  confidence      numeric,
  notion_page_id  text,
  metadata        jsonb default '{}',
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);
create index event_kind_idx on event (kind);
create index event_date_idx on event (event_date);
create trigger event_set_updated_at before update on event for each row execute function set_updated_at();

create table event_entity (
  id           uuid primary key default gen_random_uuid(),
  event_id     uuid not null references event(id) on delete cascade,
  entity_type  text not null,
  entity_id    uuid not null,
  role         text,
  created_at   timestamptz default now(),
  unique (event_id, entity_type, entity_id, role)
);
create index event_entity_event_idx on event_entity (event_id);
create index event_entity_entity_idx on event_entity (entity_type, entity_id);

alter table company enable row level security;
alter table person enable row level security;
alter table topic enable row level security;
alter table event enable row level security;
alter table event_entity enable row level security;
