# SQL Dialect Translator

A Claude Code **slash command** (`/sqltranslate`) that converts SQL between warehouse
dialects and explains what changed and why.

## What it solves
Migrating queries between BigQuery, Snowflake, Databricks, and Postgres means fixing
functions, quoting, and type casts by hand. This command does the rewrite and annotates
the differences.

## Usage
> `/sqltranslate from=bigquery to=snowflake` then paste your query.

## Supported
BigQuery · Snowflake · Databricks · PostgreSQL. Uses only the query text you provide.
