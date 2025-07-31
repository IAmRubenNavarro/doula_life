# 🗄️ Database Schema & Migrations

This directory contains the complete database schema and migration files for the Doula Life backend application.

## 📁 Directory Structure

```
database/
├── README.md           # This file
├── schema.sql          # Complete database schema
└── migrations/         # Migration files
    ├── 001_initial_data.sql    # Initial data seeding
    └── future_migrations.sql   # Future schema changes
```

## 🚀 Quick Setup

### 1. **Create New Database in Supabase**

1. Go to your [Supabase Dashboard](https://app.supabase.com/)
2. Create a new project or select existing one
3. Navigate to **SQL Editor**

### 2. **Run Schema Creation**

Copy and paste the contents of `schema.sql` into the Supabase SQL Editor and execute:

```sql
-- Run the complete schema.sql file
-- This creates all tables, indexes, RLS policies, views, and triggers
```

### 3. **Seed Initial Data**

After schema creation, run the initial data seeding:

```sql
-- Run migrations/001_initial_data.sql
-- This adds US states, sample services, and training programs
```

### 4. **Verify Installation**

Check that tables were created successfully:

```sql
-- Verify all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check that states were populated
SELECT COUNT(*) FROM states; -- Should return 51 (50 states + DC)

-- Check sample services
SELECT title, service_type, price FROM services;
```

## 🏗️ Schema Overview

### Core Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| **users** | User accounts and profiles | Role-based access, RLS enabled |
| **services** | Available services/consultations | Pricing, duration, active status |
| **appointments** | Scheduled appointments | User-service bookings, status tracking |
| **trainings** | Training programs | Online/onsite support, capacity limits |
| **training_enrollments** | User training registrations | Payment status, completion tracking |
| **payments** | Payment records | Stripe + PayPal support, audit trail |
| **states** | US states | Psychedelic legal status tracking |
| **consents** | User consent records | Version tracking, expiration dates |
| **payment_audit** | Payment change history | Webhook data, status changes |

### Payment System Features

#### Supported Providers
- ✅ **Stripe** - Credit cards, Apple Pay, Google Pay
- ✅ **PayPal** - PayPal accounts, credit cards via PayPal

#### Payment Fields
```sql
-- Stripe fields
stripe_payment_intent_id TEXT UNIQUE
stripe_customer_id TEXT
stripe_charge_id TEXT

-- PayPal fields  
paypal_order_id TEXT UNIQUE
paypal_payment_id TEXT
paypal_payer_id TEXT

-- Common fields
amount NUMERIC(10,2)
currency TEXT DEFAULT 'USD'
status TEXT -- pending, completed, failed, etc.
metadata JSONB -- Provider-specific data
```

#### Payment Statuses
- `pending` - Payment initiated
- `processing` - Payment being processed
- `completed` - Payment successful
- `failed` - Payment failed
- `cancelled` - Payment cancelled
- `refunded` - Payment refunded
- `disputed` - Payment disputed/chargeback

## 🔐 Security Features

### Row Level Security (RLS)

All sensitive tables have RLS enabled with policies for:

- **Administrators/Owners** - Full access to all data
- **Users** - Access to their own data only
- **Service Role** - System access for webhooks
- **Consultants** - Read access to their appointments

### Access Patterns

```sql
-- Users can only see their own payments
CREATE POLICY users_own_payments ON payments
FOR SELECT USING (user_id = auth.uid());

-- Admins have full access
CREATE POLICY admin_full_access ON payments
FOR ALL USING (
  EXISTS (
    SELECT 1 FROM users u
    WHERE u.id = auth.uid()
    AND u.role IN ('administrator', 'owner')
  )
);
```

## 📊 Performance Optimizations

### Strategic Indexes

```sql
-- Payment processing performance
CREATE INDEX idx_payments_stripe_intent ON payments(stripe_payment_intent_id);
CREATE INDEX idx_payments_paypal_order ON payments(paypal_order_id);
CREATE INDEX idx_payments_status ON payments(status);

-- User lookup performance  
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_appointments_user_id ON appointments(user_id);
```

### Reporting Views

```sql
-- Payment summary by provider
SELECT * FROM payment_summary;

-- User spending summary  
SELECT * FROM user_payment_summary;
```

## 🔄 Migration Strategy

### Adding New Migrations

When you need to make schema changes:

1. **Create new migration file**:
   ```
   database/migrations/002_add_new_feature.sql
   ```

2. **Include rollback instructions**:
   ```sql
   -- Migration: Add new feature
   -- Date: 2025-XX-XX
   -- Description: Add new table for feature X
   
   -- UP Migration
   CREATE TABLE new_feature (...);
   
   -- Rollback (comment out for normal execution)
   -- DROP TABLE new_feature;
   ```

3. **Test thoroughly** in development environment

4. **Document changes** in this README

### Migration Checklist

- [ ] Test migration on development database
- [ ] Verify all foreign keys work correctly
- [ ] Check RLS policies apply to new tables
- [ ] Add appropriate indexes for performance
- [ ] Update API models to match schema changes
- [ ] Run application tests after migration

## 🧪 Development & Testing

### Local Development Setup

1. **Use Supabase local development** (recommended):
   ```bash
   # Install Supabase CLI
   npm install -g supabase
   
   # Start local instance
   supabase start
   
   # Apply migrations
   supabase db reset
   ```

2. **Or use cloud Supabase project** for development

### Sample Data for Testing

The initial data includes:
- All 50 US states + Washington DC
- Sample consultation services ($75-$150)
- Sample training programs ($450-$2500)
- Psychedelic legal status by state

### Testing Payment Integration

```sql
-- Create test payment records
INSERT INTO payments (user_id, amount, payment_method, status) VALUES
(auth.uid(), 100.00, 'stripe', 'completed');

-- Test payment lookup by provider
SELECT * FROM payments WHERE stripe_payment_intent_id = 'pi_test_123';
```

## 🚨 Production Considerations

### Before Going Live

1. **Remove test data** - Clear sample services/trainings
2. **Set up monitoring** - Monitor payment_audit table
3. **Configure backups** - Ensure regular database backups
4. **Review RLS policies** - Audit security policies
5. **Performance testing** - Test with realistic data volumes

### Monitoring Queries

```sql
-- Monitor payment processing
SELECT status, COUNT(*) FROM payments 
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY status;

-- Check for failed payments
SELECT * FROM payments 
WHERE status = 'failed' 
AND created_at >= CURRENT_DATE - INTERVAL '1 day';

-- Audit trail monitoring
SELECT * FROM payment_audit 
WHERE created_at >= CURRENT_DATE - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [PayPal API Documentation](https://developer.paypal.com/docs/api/)

## 🤝 Contributing

When making database changes:

1. **Always create a migration file**
2. **Test thoroughly in development**
3. **Update this README** with changes
4. **Consider backward compatibility**
5. **Document breaking changes**

---

**Last Updated**: 2025-01-27  
**Schema Version**: 1.0.0  
**Compatible with**: PostgreSQL 13+, Supabase