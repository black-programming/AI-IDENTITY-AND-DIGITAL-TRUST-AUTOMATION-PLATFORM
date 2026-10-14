# Database Migrations & Supabase Instructions

## Structure
- `migrations/`: Versioned, immutable PostgreSQL migration scripts executed in alphanumeric order.
- `seed.sql`: Seed data for local automated testing and development.

## Running Migrations
### Using Supabase CLI:
```bash
# Start local Supabase containers (if using Docker)
supabase start

# Apply pending migrations
supabase db push

# Reset local database and run migrations + seed
supabase db reset
```

### Applying Manually via SQL Editor:
Execute `migrations/20261014000000_initial_schema.sql` in the Supabase SQL editor.
All tables enforce Row-Level Security (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
Direct public queries without valid user tokens will return zero rows.
