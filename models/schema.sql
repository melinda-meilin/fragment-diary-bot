-- ============================================================
-- Supabase schema for Fragment Diary (WeChat Mini Program)
-- Run this in Supabase SQL Editor to set up your database.
-- ============================================================

-- 1. Users table (WeChat openid as primary key)
create table if not exists users (
    id            text primary key,            -- WeChat openid
    nickname      text,
    avatar_url    text,
    timezone      text default 'Asia/Shanghai',
    created_at    timestamptz default now()
);

-- 2. Fragments — each text / voice / photo the user sends
create table if not exists fragments (
    id            uuid primary key default gen_random_uuid(),
    user_id       text references users(id) on delete cascade,
    type          text not null check (type in ('text', 'voice', 'photo')),
    content       text,                        -- text or transcription
    media_url     text,                        -- Supabase Storage URL for photo/voice
    metadata      jsonb default '{}',          -- extra info (duration, caption, etc.)
    created_at    timestamptz default now()
);

create index if not exists idx_fragments_user_date
    on fragments (user_id, created_at);

-- 3. Diaries — the AI-synthesized daily diary
create table if not exists diaries (
    id            uuid primary key default gen_random_uuid(),
    user_id       text references users(id) on delete cascade,
    diary_date    date not null,
    content       text not null,               -- Markdown formatted diary
    fragment_ids  uuid[] default '{}',         -- which fragments were used
    created_at    timestamptz default now(),
    unique (user_id, diary_date)
);

-- 4. Storage bucket (create via Supabase Dashboard → Storage → New Bucket)
-- Name: fragments, Public: false
