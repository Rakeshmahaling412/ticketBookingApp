-- Fix: roles_users join table FK columns were created as integer in the Python-era schema.
-- The parent tables (user, role) were already migrated to bigint in V20260810,
-- so the FK columns must match.

ALTER TABLE roles_users ALTER COLUMN user_id TYPE bigint;
ALTER TABLE roles_users ALTER COLUMN role_id TYPE bigint;
