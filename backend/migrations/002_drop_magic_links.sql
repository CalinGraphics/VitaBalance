-- Autentificarea prin magic link a fost eliminată (acum email + parolă).
-- Tabelul de tokenuri nu mai este folosit de aplicație.
drop table if exists public.magic_links;
