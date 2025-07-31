# 🔧 Database Troubleshooting Guide

## Common Issues & Solutions

### 🚫 **Schema Creation Issues**

#### **Error: "relation already exists"**
```sql
-- Solution: Drop existing tables first (CAREFUL!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Then run schema.sql again
```

#### **Error: "permission denied"**
- Ensure you're running SQL as the database owner
- Check that you're in the correct Supabase project
- Verify your connection string in Supabase settings

### 🔐 **RLS (Row Level Security) Issues**

#### **Error: "new row violates row-level security policy"**
```sql
-- Common cause: User not authenticated
-- Solution: Ensure user is logged in via Supabase Auth

-- Check current user context
SELECT auth.uid(); -- Should return UUID, not null

-- Temporarily disable RLS for testing (NEVER in production)
ALTER TABLE payments DISABLE ROW LEVEL SECURITY;
```

#### **Users can't access their own data**
```sql
-- Check if user exists in users table
SELECT * FROM users WHERE id = auth.uid();

-- If user doesn't exist, create them:
INSERT INTO users (id, first_name, last_name, email, role) 
VALUES (auth.uid(), 'Test', 'User', 'test@example.com', 'individual_client');
```

### 💳 **Payment Issues**

#### **Foreign key constraint violations**
```sql
-- Error: insert or update on table "payments" violates foreign key constraint
-- Solution: Ensure referenced records exist

-- Check if user exists
SELECT id FROM users WHERE id = 'user-uuid-here';

-- Check if service exists  
SELECT id FROM services WHERE id = 'service-uuid-here';
```

#### **Payment amount validation errors**
```sql
-- Error: new row for relation "payments" violates check constraint "payments_amount_check"
-- Solution: Ensure amount is positive
INSERT INTO payments (user_id, amount, payment_method, status) 
VALUES (auth.uid(), 100.00, 'stripe', 'pending'); -- ✅ Positive amount

-- NOT: 
-- VALUES (auth.uid(), -100.00, 'stripe', 'pending'); -- ❌ Negative amount
```

### 🔄 **Migration Issues**

#### **Error: "column already exists"**
```sql
-- When running migrations multiple times
-- Solution: Use IF NOT EXISTS
ALTER TABLE payments ADD COLUMN IF NOT EXISTS stripe_payment_intent_id TEXT;
```

#### **Data type mismatches**
```sql
-- Error: column "amount" is of type numeric but expression is of type text
-- Solution: Cast values properly
UPDATE payments SET amount = '100.00'::NUMERIC;
```

### 🚀 **Performance Issues**

#### **Slow payment queries**
```sql
-- Check if indexes exist
SELECT indexname, tablename FROM pg_indexes 
WHERE tablename = 'payments';

-- If missing, create indexes:
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
```

#### **Large table scans**
```sql
-- Use EXPLAIN to check query performance
EXPLAIN ANALYZE SELECT * FROM payments WHERE status = 'completed';

-- Should show "Index Scan" not "Seq Scan"
```

### 🔍 **Debugging Queries**

#### **Check RLS policy effects**
```sql
-- See what policies are active
SELECT schemaname, tablename, policyname, cmd, qual 
FROM pg_policies 
WHERE tablename = 'payments';
```

#### **Test queries as different users**
```sql
-- Check what data a specific user can see
SET row_security = on;
SET LOCAL role = 'authenticated';
-- Run your query here
```

### 🚨 **Data Recovery**

#### **Accidentally deleted data**
```sql
-- Check if you have point-in-time recovery enabled in Supabase
-- You can restore from backups in the Supabase dashboard

-- For future: Enable logical replication for better recovery options
```

#### **Corrupted payment records**
```sql
-- Find inconsistent payment states
SELECT * FROM payments 
WHERE status = 'completed' 
AND payment_date IS NULL;

-- Find payments with invalid amounts
SELECT * FROM payments 
WHERE amount <= 0;
```

### 🔧 **Connection Issues**

#### **Cannot connect to database**
```bash
# Check your connection string
DATABASE_URL=postgresql+asyncpg://postgres:[password]@[project].supabase.co:5432/postgres

# Common issues:
# 1. Wrong password
# 2. Wrong project reference URL
# 3. Wrong port (should be 5432)
# 4. Missing database name at the end
```

#### **SSL connection errors**
```bash
# Add SSL mode to connection string
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require
```

### 📊 **Monitoring & Health Checks**

#### **Check database health**
```sql
-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Recent payments
SELECT COUNT(*) FROM payments 
WHERE created_at >= CURRENT_DATE - INTERVAL '24 hours';
```

### 🆘 **Emergency Commands**

#### **Reset everything (NUCLEAR OPTION)**
```sql
-- ⚠️ THIS DELETES ALL DATA ⚠️
-- Only use in development!

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Then re-run schema.sql and migrations
```

#### **Disable all RLS temporarily**
```sql
-- ⚠️ ONLY FOR DEBUGGING ⚠️
-- Never leave this in production!

ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE payments DISABLE ROW LEVEL SECURITY;
ALTER TABLE appointments DISABLE ROW LEVEL SECURITY;

-- Remember to re-enable:
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

### 📞 **Getting Help**

1. **Check Supabase Dashboard** - Logs tab for errors
2. **Supabase Discord** - Community support
3. **PostgreSQL Documentation** - For SQL-specific issues
4. **FastAPI Documentation** - For ORM/SQLAlchemy issues

### 🔍 **Useful Debugging Queries**

```sql
-- Check user permissions
SELECT * FROM users WHERE id = auth.uid();

-- See all payment statuses
SELECT status, COUNT(*) FROM payments GROUP BY status;

-- Find recent errors in audit log
SELECT * FROM payment_audit 
WHERE provider_data->>'error' IS NOT NULL
ORDER BY created_at DESC LIMIT 10;

-- Check for orphaned records
SELECT p.* FROM payments p
LEFT JOIN users u ON p.user_id = u.id
WHERE u.id IS NULL;
```