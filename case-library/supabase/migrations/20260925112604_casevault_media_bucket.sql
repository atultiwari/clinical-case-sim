-- The private Storage bucket for case figures (SPEC §9; PLAN L0.3).
-- Files live at <case id>/<figure id>.<ext>, masked copies beside them. The
-- bucket is private and has no client policies: the game server hands out
-- short-lived signed links. Skipped where Storage is not installed (the
-- database-only stack that CI starts).

do $$
begin
  if to_regclass('storage.buckets') is null then
    raise notice 'storage.buckets not found; case-media bucket not created';
    return;
  end if;

  insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
  values ('case-media', 'case-media', false, 20 * 1024 * 1024,
          array['image/jpeg', 'image/png', 'image/tiff', 'image/webp'])
  on conflict (id) do nothing;
end
$$;
