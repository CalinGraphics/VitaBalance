-- Curățenie după trecerea pe Supabase Auth (007). Se aplică DUPĂ ce versiunea nouă e în producție (merge în main):
-- producția veche citește încă users.password_hash (login) și magic_links (magic link).
--
-- Înainte de rulare, verifică faptul că nu a rămas niciun cont cu parolă nemigrat (trebuie să întoarcă 0):
--   select count(*) from public.users where password_hash is not null and auth_user_id is null;
-- Conturile astfel rămase se migrează singure la primul login (services/auth.py::_migrate_legacy_account),
-- dar numai cât timp coloana există.

alter table public.users drop column if exists password_hash;

-- Înlocuiește 002_drop_magic_links.sql.
drop table if exists public.magic_links;
