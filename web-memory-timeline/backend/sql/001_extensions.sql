-- Enable required extensions
create extension if not exists vector;
create extension if not exists pgcrypto; -- for gen_random_uuid()
