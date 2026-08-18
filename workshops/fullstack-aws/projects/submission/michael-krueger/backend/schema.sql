-- ===========================================================================
-- Notice Board: database schema for Supabase (hosted PostgreSQL)
-- ===========================================================================
--
-- HOW TO RUN THIS
--   Supabase dashboard, SQL Editor, New query, paste this whole file, Run.
--
-- WHAT CHANGED, AND WHY THIS FILE WAS REWRITTEN
--   Authentication was added to the backend, which needs two things this
--   database did not have: a users table, and a user_id column on notices
--   saying who posted each one. A live check against the project confirmed
--   both were missing, which is what made GET /notices fail with
--
--       column notices.user_id does not exist   (SQLSTATE 42703)
--
--   The notices table itself already existed and held zero rows, which is
--   what makes the migration below simple: there is nothing to backfill.
--
--   After the backend switched to the service_role key, a second gap showed
--   up: GRANT and RLS are separate gates. RLS decides which rows a role
--   sees (service_role bypasses it). GRANT decides whether the role may
--   touch the table at all, and nothing grants that automatically for
--   tables created by raw SQL. The earlier grants only ever named anon, so
--   service_role had no table access until the GRANT block near the bottom
--   was added.
--
--   Reactions were added after that: a notice_reactions table so users can
--   like/heart/laugh a notice, independently toggleable per type.
--
-- SAFE TO RE-RUN
--   Every statement is guarded, so running the file again changes nothing
--   and reports notices rather than errors. GRANT is idempotent too, so
--   re-running the whole file is always safe.
--
--   Re-running does NOT delete existing rows. There is no DROP TABLE here.
--
-- WHY THE RLS SECTION LOOKS DIFFERENT NOW
--   The backend used to connect with the anon key, which row level security
--   applies to. It now connects with the service_role key, which bypasses
--   RLS completely (assuming service_role has BYPASSRLS on this project,
--   see the verification query at the bottom).
--
--   So the policies below no longer protect the API. What protects it is the
--   JWT check in app/dependencies.py and the ownership check in
--   app/services/notice_service.py. The policies still matter for anyone
--   else holding the anon key, above all the frontend bundle, where the key
--   is public by design.
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- USERS
-- ---------------------------------------------------------------------------
--
-- password_hash holds a bcrypt hash, never a password. The hash is around 60
-- characters and carries its own salt, so no separate salt column is needed.
--
-- username is UNIQUE because it is what people log in with, and because the
-- signup service relies on the database to be the final word on duplicates.
-- Its check runs before the insert, so two signups in the same instant can
-- both pass it. This constraint is what actually stops the duplicate.
--
-- The 50 character limit matches the max_length on UserCreate in
-- app/models/user.py, so keep the two in step.
CREATE TABLE IF NOT EXISTS public.users (
    id            bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      text        NOT NULL,
    password_hash text        NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT users_username_unique UNIQUE (username),

    CONSTRAINT users_username_not_blank
        CHECK (length(btrim(username)) > 0 AND length(username) <= 50)
);


-- ---------------------------------------------------------------------------
-- NOTICES
-- ---------------------------------------------------------------------------
--
-- Created only if it is not already there. On this project it already exists,
-- so this block does nothing and the ALTER statements below are what actually
-- run. It is kept so the file still builds the whole schema from empty, which
-- is what you want when setting up a second Supabase project.
--
-- See the users table above for why text plus CHECK is used instead of
-- varchar(n): changing a CHECK later is cheap, changing a varchar length
-- rewrites the table.
CREATE TABLE IF NOT EXISTS public.notices (
    id          bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        text        NOT NULL,
    message     text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT notices_name_not_blank
        CHECK (length(btrim(name)) > 0 AND length(name) <= 100),

    CONSTRAINT notices_message_not_blank
        CHECK (length(btrim(message)) > 0 AND length(message) <= 2000)
);


-- Add the owner column.
--
-- Added nullable first, on purpose. A plain "ADD COLUMN user_id bigint NOT
-- NULL" is refused outright by Postgres on a table that already has rows,
-- because there would be no value to put in them. Adding it nullable always
-- works, and the NOT NULL is applied further down once it is safe.
ALTER TABLE public.notices ADD COLUMN IF NOT EXISTS user_id bigint;


-- Point user_id at users.id.
--
-- Wrapped in a DO block because Postgres has no ADD CONSTRAINT IF NOT
-- EXISTS, and running the plain form twice is an error rather than a no-op.
--
-- ON DELETE CASCADE means deleting an account also removes the notices it
-- posted. That is the right call for a notice board: the alternative,
-- RESTRICT, would make an account impossible to delete until every notice
-- was removed by hand, and leaving orphaned rows is not an option while the
-- column is NOT NULL.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'notices_user_id_fkey'
    ) THEN
        ALTER TABLE public.notices
            ADD CONSTRAINT notices_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES public.users (id)
            ON DELETE CASCADE;
    END IF;
END
$$;


-- Make user_id required, but only once that cannot fail.
--
-- Every notice must have an owner: the delete endpoint compares
-- notices.user_id against the caller's id, and a NULL there would be a row
-- nobody could ever delete.
--
-- The guard exists because this file has to be safe to run against a table
-- that already holds pre-authentication rows. On this project notices is
-- empty, so the ELSE branch runs and the column becomes NOT NULL. If you run
-- this against a copy that does have old rows, it tells you what to do
-- instead of failing with a constraint violation.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.notices WHERE user_id IS NULL) THEN
        RAISE NOTICE
            'notices still has rows with no user_id, so the column was left '
            'nullable. Assign them an owner or delete them, then re-run.';
    ELSE
        ALTER TABLE public.notices ALTER COLUMN user_id SET NOT NULL;
    END IF;
END
$$;


-- ---------------------------------------------------------------------------
-- NOTICE REACTIONS
-- ---------------------------------------------------------------------------
--
-- One row per (notice, user, reaction_type). The unique constraint below is
-- what makes a reaction togglable: clicking "like" again finds this exact
-- row and deletes it instead of inserting a duplicate. A user CAN have
-- multiple different reaction types active on the same notice (like AND
-- heart), just not the same type twice.
CREATE TABLE IF NOT EXISTS public.notice_reactions (
    id            bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notice_id     bigint      NOT NULL REFERENCES public.notices (id) ON DELETE CASCADE,
    user_id       bigint      NOT NULL REFERENCES public.users (id)   ON DELETE CASCADE,
    reaction_type text        NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT notice_reactions_type_valid
        CHECK (reaction_type IN ('like', 'heart', 'laugh')),

    -- This is what makes toggling work: one row per person per kind per
    -- notice, so the backend can look for it and delete or insert.
    CONSTRAINT notice_reactions_unique_per_user
        UNIQUE (notice_id, user_id, reaction_type)
);

-- Needed so deleting a user does not scan the whole table to cascade.
-- No index on notice_id: the unique constraint above already creates one
-- with notice_id as its leading column, which the board's batch query uses.
CREATE INDEX IF NOT EXISTS notice_reactions_user_id_idx
    ON public.notice_reactions (user_id);

ALTER TABLE public.notice_reactions ENABLE ROW LEVEL SECURITY;
-- No policies, so anon and authenticated get nothing. The backend reaches it
-- as service_role, and the frontend never talks to Supabase directly.

-- Without this the next error is 42501, exactly as it was for users.
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notice_reactions TO service_role;


-- ---------------------------------------------------------------------------
-- INDEXES (notices)
-- ---------------------------------------------------------------------------
--
-- GET /notices sorts by created_at DESC, id DESC on every call. An index in
-- the same order lets Postgres read the rows already sorted instead of
-- fetching the whole table and sorting it. The column order has to match the
-- ORDER BY in app/services/notice_service.py for that to work.
CREATE INDEX IF NOT EXISTS notices_created_at_id_desc_idx
    ON public.notices (created_at DESC, id DESC);

-- Postgres indexes the primary key of users automatically but not the
-- referencing side of the foreign key. Without this, deleting a user makes
-- the ON DELETE CASCADE scan the whole notices table to find their rows.
CREATE INDEX IF NOT EXISTS notices_user_id_idx
    ON public.notices (user_id);


-- ---------------------------------------------------------------------------
-- ROW LEVEL SECURITY (users, notices)
-- ---------------------------------------------------------------------------
--
-- A table created by raw SQL does not get RLS automatically. Supabase only
-- pre-ticks "Enable RLS" when a table is made through the dashboard's table
-- editor, so without these lines both tables would be wide open to anyone
-- holding the anon key, which is a key designed to be published in a
-- frontend bundle.
ALTER TABLE public.notices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users   ENABLE ROW LEVEL SECURITY;

-- DROP before CREATE because Postgres has no CREATE POLICY IF NOT EXISTS.
-- This is what makes the file re-runnable.
DROP POLICY IF EXISTS notices_select_anon ON public.notices;
DROP POLICY IF EXISTS notices_insert_anon ON public.notices;
DROP POLICY IF EXISTS notices_delete_anon ON public.notices;

-- Anyone may read every notice.
--
-- USING (true) means no row is filtered out. That is the correct rule for a
-- public notice board: the whole idea is that everybody sees the same wall,
-- and GET /notices is deliberately open with no token required.
CREATE POLICY notices_select_anon
    ON public.notices
    FOR SELECT
    TO anon, authenticated
    USING (true);

-- The insert and delete policies for anon are deliberately NOT recreated.
--
-- They used to exist, and leaving them would now be a real hole. Posting and
-- deleting go through the backend, which checks a token and enforces that a
-- notice can only be deleted by whoever posted it. An anon insert or delete
-- policy would let anyone holding the anon key skip all of that and write
-- straight to the table, which would make the authentication decorative.
--
-- Dropping them costs nothing, because the backend authenticates with the
-- service_role key and bypasses RLS entirely, once it is also granted table
-- access below. It never needed these policies. Only a direct caller does,
-- and a direct caller is exactly what should be refused.
--
-- users and notice_reactions get no policies at all, which is the strictest
-- setting and the right one. RLS with no policy denies anon and
-- authenticated completely, so password hashes and reaction data cannot be
-- read with the public key under any query. The backend still reaches both
-- because service_role ignores RLS.


-- ---------------------------------------------------------------------------
-- GRANTS
-- ---------------------------------------------------------------------------
--
-- RLS and GRANT are two separate gates. RLS decides which ROWS a role sees.
-- GRANT decides whether the role may touch the TABLE at all, and it is
-- checked first. Nothing grants this automatically for tables created by
-- raw SQL (Supabase only auto-grants for tables made through the dashboard's
-- table editor).
--
-- service_role is what the backend now authenticates as. Without this
-- block, every query from the backend fails with "permission denied for
-- table ...", regardless of RLS or BYPASSRLS status, because it never gets
-- past the GRANT check to have RLS evaluated at all.
--
-- Do NOT grant users or notice_reactions to anon. That would expose password
-- hashes and let anyone forge reactions using someone else's key.
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notices           TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users             TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.notice_reactions  TO service_role;


-- ---------------------------------------------------------------------------
-- CHECK IT WORKED
-- ---------------------------------------------------------------------------
--
-- Run these afterwards. user_id should appear, as bigint and NOT nullable.
--
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'notices'
--   ORDER BY ordinal_position;
--
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'users'
--   ORDER BY ordinal_position;
--
--   SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'notice_reactions'
--   ORDER BY ordinal_position;
--
-- Expect one policy on notices (select) and none on users or
-- notice_reactions.
--
--   SELECT tablename, policyname, cmd FROM pg_policies
--   WHERE schemaname = 'public';
--
-- Confirm service_role actually bypasses RLS on this project (it normally
-- does on Supabase, but this proves it rather than assumes it):
--
--   SELECT rolname, rolbypassrls FROM pg_roles
--   WHERE rolname IN ('service_role', 'anon', 'authenticated');
--
-- There is no sample INSERT here any more. notices.user_id is required and
-- points at a real account, so the way to create a notice is to sign up
-- through POST /auth/signup, log in, and post with the token.