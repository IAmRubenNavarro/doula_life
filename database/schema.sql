-- =========================================
-- 🤱 DOULA LIFE BACKEND - DATABASE SCHEMA
-- =========================================
-- 
-- This schema supports:
-- ✅ User management with role-based access
-- ✅ Service and appointment booking
-- ✅ Training program enrollments  
-- ✅ Dual payment processing (Stripe + PayPal)
-- ✅ Comprehensive audit trails
-- ✅ Row Level Security (RLS)
--
-- Version: 1.0.0
-- Last Updated: 2025-01-27
-- Compatible with: PostgreSQL 13+, Supabase
-- =========================================

-- 🔑 Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================================
-- 👥 USERS TABLE
-- =========================================
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT NOT NULL,
  middle_name TEXT,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL CHECK (
    role IN (
      'administrator',
      'owner',
      'consultant',
      'healthcare_professional',
      'individual_client'
    )
  ),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================
-- 📍 STATES TABLE
-- =========================================
CREATE TABLE states (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL,
  abbreviation TEXT UNIQUE NOT NULL,
  psychedelics_legal BOOLEAN DEFAULT FALSE NOT NULL
);

-- =========================================
-- 🧠 SERVICES TABLE
-- =========================================
CREATE TABLE services (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  service_type TEXT NOT NULL CHECK (service_type IN ('consulting', 'training')),
  price NUMERIC(10,2) CHECK (price >= 0), -- 2 decimal places, non-negative
  duration_minutes INTEGER CHECK (duration_minutes > 0),
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================
-- 📅 APPOINTMENTS TABLE
-- =========================================
CREATE TABLE appointments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  service_id UUID NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
  appointment_time TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INTEGER CHECK (duration_minutes > 0),
  state_id INTEGER REFERENCES states(id),
  status TEXT DEFAULT 'scheduled' NOT NULL CHECK (
    status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')
  ),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =========================================
-- 🎓 TRAININGS TABLE
-- =========================================
CREATE TABLE trainings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  duration TIME,
  location TEXT,
  capacity INTEGER CHECK (capacity > 0),
  state_id INTEGER REFERENCES states(id),
  is_online BOOLEAN DEFAULT FALSE NOT NULL,
  is_onsite BOOLEAN DEFAULT FALSE NOT NULL,
  price NUMERIC(10,2) CHECK (price >= 0),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT valid_dates CHECK (end_date >= start_date),
  CONSTRAINT valid_delivery_method CHECK (is_online = TRUE OR is_onsite = TRUE)
);

-- =========================================
-- 📘 TRAINING ENROLLMENTS TABLE
-- =========================================
CREATE TABLE training_enrollments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  training_id UUID NOT NULL REFERENCES trainings(id) ON DELETE RESTRICT,
  enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  payment_status TEXT DEFAULT 'pending' NOT NULL CHECK (
    payment_status IN ('pending', 'paid', 'cancelled', 'refunded')
  ),
  passed_assessment BOOLEAN,
  completion_date DATE,
  certificate_issued BOOLEAN DEFAULT FALSE,
  UNIQUE(user_id, training_id) -- Prevent duplicate enrollments
);

-- =========================================
-- 💳 PAYMENTS TABLE (Stripe + PayPal Support)
-- =========================================
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  currency TEXT DEFAULT 'USD' NOT NULL,
  payment_method TEXT NOT NULL CHECK (
    payment_method IN ('stripe', 'paypal', 'cash', 'check', 'bank_transfer', 'other')
  ),
  status TEXT DEFAULT 'pending' NOT NULL CHECK (
    status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded', 'disputed')
  ),
  
  -- Business entity associations (nullable - payment can be for different things)
  service_id UUID REFERENCES services(id),
  appointment_id UUID REFERENCES appointments(id),
  training_id UUID REFERENCES trainings(id),
  
  -- Stripe-specific fields
  stripe_payment_intent_id TEXT UNIQUE,
  stripe_customer_id TEXT,
  stripe_charge_id TEXT,
  
  -- PayPal-specific fields  
  paypal_order_id TEXT UNIQUE,
  paypal_payment_id TEXT,
  paypal_payer_id TEXT,
  
  -- Additional tracking
  description TEXT,
  metadata JSONB, -- For storing additional provider-specific data
  payment_date TIMESTAMP WITH TIME ZONE, -- When payment was actually completed
  refund_amount NUMERIC(10,2) DEFAULT 0 CHECK (refund_amount >= 0),
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Ensure only one business entity is associated per payment
  CONSTRAINT single_business_entity CHECK (
    (service_id IS NOT NULL)::int + 
    (appointment_id IS NOT NULL)::int + 
    (training_id IS NOT NULL)::int <= 1
  ),
  
  -- Ensure refund doesn't exceed original amount
  CONSTRAINT valid_refund CHECK (refund_amount <= amount)
);

-- =========================================
-- 📝 CONSENTS TABLE
-- =========================================
CREATE TABLE consents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  consent_type TEXT NOT NULL, -- e.g., 'treatment', 'data_processing', 'marketing'
  consent_text TEXT NOT NULL,
  version TEXT, -- Track consent version for legal compliance
  signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- =========================================
-- 📊 PAYMENT AUDIT TRAIL
-- =========================================
CREATE TABLE payment_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
  old_status TEXT,
  new_status TEXT NOT NULL,
  changed_by UUID REFERENCES users(id),
  change_reason TEXT,
  provider_data JSONB, -- Store webhook data, error messages, etc.
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- =========================================
-- 🚀 PERFORMANCE INDEXES
-- =========================================

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Appointments  
CREATE INDEX idx_appointments_user_id ON appointments(user_id);
CREATE INDEX idx_appointments_service_id ON appointments(service_id);
CREATE INDEX idx_appointments_appointment_time ON appointments(appointment_time);
CREATE INDEX idx_appointments_status ON appointments(status);

-- Payments (Critical for payment processing performance)
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_method ON payments(payment_method);
CREATE INDEX idx_payments_stripe_intent ON payments(stripe_payment_intent_id);
CREATE INDEX idx_payments_paypal_order ON payments(paypal_order_id);
CREATE INDEX idx_payments_created_at ON payments(created_at);
CREATE INDEX idx_payments_payment_date ON payments(payment_date);

-- Training enrollments
CREATE INDEX idx_training_enrollments_user_id ON training_enrollments(user_id);
CREATE INDEX idx_training_enrollments_training_id ON training_enrollments(training_id);
CREATE INDEX idx_training_enrollments_payment_status ON training_enrollments(payment_status);

-- Payment audit
CREATE INDEX idx_payment_audit_payment_id ON payment_audit(payment_id);
CREATE INDEX idx_payment_audit_created_at ON payment_audit(created_at);

-- =========================================
-- 🔐 ROW LEVEL SECURITY (RLS)
-- =========================================

-- Enable RLS on all relevant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE states ENABLE ROW LEVEL SECURITY;
ALTER TABLE trainings ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_audit ENABLE ROW LEVEL SECURITY;

-- =========================================
-- 🔒 RLS POLICIES
-- =========================================

-- Admin/Owner full access to sensitive tables
DO $
DECLARE
  t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'users',
    'appointments', 
    'training_enrollments',
    'payments',
    'consents',
    'payment_audit'
  ])
  LOOP
    EXECUTE format($SQL$
      CREATE POLICY admin_full_access ON %I
      FOR ALL
      USING (
        EXISTS (
          SELECT 1 FROM users u
          WHERE u.id = auth.uid()
          AND u.role IN ('administrator', 'owner')
        )
      );
    $SQL$, t);
  END LOOP;
END $;

-- User self-access policies
CREATE POLICY users_own_data ON users
FOR ALL
USING (id = auth.uid());

CREATE POLICY users_own_appointments ON appointments  
FOR ALL
USING (user_id = auth.uid());

CREATE POLICY users_own_enrollments ON training_enrollments
FOR ALL 
USING (user_id = auth.uid());

CREATE POLICY users_own_payments ON payments
FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY users_own_consents ON consents
FOR ALL
USING (user_id = auth.uid());

-- Service role access (for webhooks and system operations)
CREATE POLICY service_role_payments ON payments
FOR ALL
USING (auth.role() = 'service_role');

CREATE POLICY service_role_audit ON payment_audit  
FOR ALL
USING (auth.role() = 'service_role');

-- Consultant access to their appointments
CREATE POLICY consultant_appointments ON appointments
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM users u 
    WHERE u.id = auth.uid() 
    AND u.role = 'consultant'
  )
);

-- Public read-only access
CREATE POLICY public_read_states ON states
FOR SELECT USING (true);

CREATE POLICY public_read_services ON services  
FOR SELECT USING (is_active = true);

CREATE POLICY public_read_trainings ON trainings
FOR SELECT USING (true);

-- Admin management of public tables
CREATE POLICY admin_manage_services ON services
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM users u
    WHERE u.id = auth.uid() AND u.role IN ('administrator', 'owner')
  )
);

CREATE POLICY admin_manage_trainings ON trainings
FOR ALL  
USING (
  EXISTS (
    SELECT 1 FROM users u
    WHERE u.id = auth.uid() AND u.role IN ('administrator', 'owner')
  )
);

CREATE POLICY admin_manage_states ON states
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM users u  
    WHERE u.id = auth.uid() AND u.role IN ('administrator', 'owner')
  )
);

-- =========================================
-- 📊 REPORTING VIEWS
-- =========================================

CREATE VIEW payment_summary AS
SELECT 
  payment_method,
  status,
  COUNT(*) as payment_count,
  SUM(amount) as total_amount,
  AVG(amount) as avg_amount,
  COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as payments_last_30_days
FROM payments 
GROUP BY payment_method, status;

CREATE VIEW user_payment_summary AS  
SELECT 
  u.id as user_id,
  u.email,
  u.first_name,
  u.last_name,
  COUNT(p.id) as total_payments,
  SUM(p.amount) as total_spent,
  MAX(p.created_at) as last_payment_date
FROM users u
LEFT JOIN payments p ON u.id = p.user_id AND p.status = 'completed'
GROUP BY u.id, u.email, u.first_name, u.last_name;

-- =========================================
-- 🔔 TABLE COMMENTS
-- =========================================

COMMENT ON TABLE payments IS 'Payment records supporting multiple providers (Stripe, PayPal, etc.)';
COMMENT ON COLUMN payments.stripe_payment_intent_id IS 'Stripe Payment Intent ID for tracking';
COMMENT ON COLUMN payments.paypal_order_id IS 'PayPal Order ID for tracking';
COMMENT ON COLUMN payments.metadata IS 'JSONB field for storing provider-specific data';
COMMENT ON TABLE payment_audit IS 'Audit trail for payment status changes and webhook events';

-- =========================================
-- 🔧 TRIGGERS FOR UPDATED_AT
-- =========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_trainings_updated_at BEFORE UPDATE ON trainings  
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================
-- ✅ SCHEMA CREATION COMPLETE
-- =========================================
-- 
-- 🎉 Your Doula Life database schema is ready!
-- 
-- Next steps:
-- 1. Run this script in your Supabase SQL editor
-- 2. Insert initial data (states, initial admin user, services)
-- 3. Test your FastAPI application
-- 4. Configure Stripe and PayPal webhooks
-- 
-- For questions or issues, refer to the README.md
-- =========================================