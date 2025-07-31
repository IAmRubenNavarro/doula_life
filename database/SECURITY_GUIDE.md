# 🔐 Database Security Guide

## Row Level Security (RLS) Policies

Your database uses Row Level Security to ensure users can only access their own data. Here's what you need to know:

### 🔑 **Authentication Context**

The policies rely on Supabase Auth context:
- `auth.uid()` - Returns the authenticated user's UUID
- `auth.role()` - Returns the user's role ('authenticated', 'service_role', etc.)

### 👤 **User Access Patterns**

#### **Regular Users (`individual_client`)**
```sql
-- Users can only see their own data
SELECT * FROM payments WHERE user_id = auth.uid();
SELECT * FROM appointments WHERE user_id = auth.uid();
```

#### **Administrators (`administrator`, `owner`)**
```sql
-- Admins can see everything
SELECT * FROM payments; -- All payments
SELECT * FROM users;    -- All users
```

#### **Service Role (for webhooks)**
```sql
-- System operations (webhooks, background jobs)
-- Has full access when using service_role key
```

### ⚠️ **Important Security Notes**

1. **Service Role Key** - Only use for server-side operations (webhooks)
2. **Anon Key** - Safe for client-side, but users must authenticate
3. **Never expose service_role key** in frontend code

### 🧪 **Testing RLS Policies**

```sql
-- Test as authenticated user
SELECT auth.uid(); -- Should return user UUID
SELECT * FROM payments; -- Should only show user's payments

-- Test admin access
UPDATE users SET role = 'administrator' WHERE id = auth.uid();
SELECT * FROM payments; -- Should now show all payments
```

## 🔒 **Payment Security**

### **PCI Compliance Considerations**

1. **No Card Data Storage** - Never store credit card numbers
2. **Stripe/PayPal Handle Sensitive Data** - We only store transaction IDs
3. **Encrypted Fields** - All payment provider IDs are encrypted at rest
4. **Audit Trail** - All payment changes are logged in `payment_audit`

### **Webhook Security**

```sql
-- Webhook requests use service_role for database access
-- This bypasses RLS but is necessary for system operations
```

## 🚨 **Emergency Procedures**

### **Suspected Security Breach**

1. **Immediately rotate API keys**:
   - Stripe secret keys
   - PayPal credentials
   - Database passwords

2. **Check audit logs**:
   ```sql
   SELECT * FROM payment_audit 
   WHERE created_at >= NOW() - INTERVAL '24 hours'
   ORDER BY created_at DESC;
   ```

3. **Review user access**:
   ```sql
   SELECT email, role, created_at 
   FROM users 
   WHERE role IN ('administrator', 'owner')
   ORDER BY created_at DESC;
   ```

### **Failed Payment Investigation**

```sql
-- Check payment audit trail
SELECT pa.*, p.amount, p.payment_method
FROM payment_audit pa
JOIN payments p ON pa.payment_id = p.id
WHERE pa.new_status = 'failed'
AND pa.created_at >= CURRENT_DATE - INTERVAL '1 day';
```