# Database Schema Synchronization Fix

## Problem Summary

When attempting to sign up or log in, the backend crashed with the error:
```
psycopg2.errors.UndefinedColumn: column users.username does not exist
```

## Root Cause

Your Docker volume contained a database with an old schema that was missing the `username` column. The code expected this column, but SQLAlchemy's `create_all()` method only creates missing tables—it doesn't add missing columns to existing tables.

## Solution Implemented

We've added **Alembic**, a database migration tool, to properly handle schema changes. The backend now automatically runs migrations on startup to keep your database schema in sync with the code.

## How to Fix Your Database

### Option 1: Reset Database (Recommended for Development)

This gives you a clean start:
```bash
docker compose down -v  # Removes volumes and stops containers
docker compose up --build  # Recreates everything fresh
```

### Option 2: Run Migrations (Preserves Existing Data)

The backend will automatically run migrations on startup. Just restart:
```bash
docker compose restart backend
```

Or run migrations manually:
```bash
cd backend
alembic upgrade head
```

## What Changed

1. **Alembic Integration**: Added database migration system
2. **Automatic Migrations**: Migrations run automatically when backend starts
3. **Two Migrations Created**:
   - `initial_schema`: Creates all tables if they don't exist
   - `add_username_column_if_missing`: Adds username column to existing databases

4. **Comprehensive Tests**: Added 11 new tests to catch schema issues early
5. **Updated Documentation**: README files now explain how to handle schema changes

## Testing

All 16 tests pass, including:
- ✅ Schema validation tests
- ✅ Integration test simulating your exact issue
- ✅ Tests verifying migrations fix the problem
- ✅ All existing API tests

## Future Schema Changes

Going forward, when the database schema changes:
1. A migration will be created
2. The backend will automatically apply it on startup
3. No manual intervention needed (unless you want to preserve specific data)

## Documentation

For more details, see:
- `README.md` - User-facing documentation with migration instructions
- `backend/README.md` - Backend-specific migration documentation with Alembic commands
