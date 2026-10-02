-- Apply to a new Supabase project through its SQL editor or migrations.
begin;
create table public.binocular_profiles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 sleeper_username text check (sleeper_username ~ '^[a-z0-9_-]{1,64}$'),
 favorite_leagues text[] not null default '{}',
 revision bigint not null default 0,
 updated_at timestamptz not null default now()
);
alter table public.binocular_profiles enable row level security;
create policy own_profile_read on public.binocular_profiles for select to authenticated using ((select auth.uid()) = user_id);
revoke all on public.binocular_profiles from anon, authenticated;
grant select on public.binocular_profiles to authenticated;
-- Writes go through owner-bound functions, preventing clients bypassing revision checks.
create function public.get_profile() returns jsonb language plpgsql security definer set search_path = '' as $$
declare owner uuid := auth.uid(); result jsonb;
begin
 if owner is null then raise exception 'not_authenticated' using errcode='28000'; end if;
 insert into public.binocular_profiles(user_id) values (owner) on conflict do nothing;
 select to_jsonb(p) into result from public.binocular_profiles p where p.user_id=owner;
 return result;
end $$;
create function public.save_profile(expected_revision bigint, new_username text, new_favorites text[])
returns jsonb language plpgsql security definer set search_path = '' as $$
declare owner uuid := auth.uid(); saved public.binocular_profiles;
begin
 if owner is null then raise exception 'not_authenticated' using errcode='28000'; end if;
 if new_favorites is null or cardinality(new_favorites)>100 or exists(select 1 from unnest(new_favorites) x where x is null or x !~ '^[0-9]{1,30}$') then
  raise exception 'invalid_favorites' using errcode='22023';
 end if;
 update public.binocular_profiles set sleeper_username=new_username,
 favorite_leagues=new_favorites,revision=revision+1,updated_at=now()
 where user_id=owner and revision=expected_revision returning * into saved;
 if not found then raise exception 'sync_conflict' using errcode='P0001'; end if;
 return to_jsonb(saved);
end $$;
revoke all on function public.get_profile() from public, anon;
revoke all on function public.save_profile(bigint,text,text[]) from public, anon;
grant execute on function public.get_profile() to authenticated;
grant execute on function public.save_profile(bigint,text,text[]) to authenticated;
commit;
