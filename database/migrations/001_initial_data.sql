-- =========================================
-- 🌱 INITIAL DATA SEEDING
-- =========================================
-- 
-- This file contains initial data to get your 
-- Doula Life application up and running
-- 
-- Run this AFTER the main schema.sql
-- =========================================

-- =========================================
-- 📍 SEED STATES DATA
-- =========================================

INSERT INTO states (name, abbreviation, psychedelics_legal) VALUES
('Alabama', 'AL', false),
('Alaska', 'AK', false),
('Arizona', 'AZ', false),
('Arkansas', 'AR', false),
('California', 'CA', false),
('Colorado', 'CO', true),
('Connecticut', 'CT', false),
('Delaware', 'DE', false),
('Florida', 'FL', false),
('Georgia', 'GA', false),
('Hawaii', 'HI', false),
('Idaho', 'ID', false),
('Illinois', 'IL', false),
('Indiana', 'IN', false),
('Iowa', 'IA', false),
('Kansas', 'KS', false),
('Kentucky', 'KY', false),
('Louisiana', 'LA', false),
('Maine', 'ME', false),
('Maryland', 'MD', false),
('Massachusetts', 'MA', false),
('Michigan', 'MI', false),
('Minnesota', 'MN', false),
('Mississippi', 'MS', false),
('Missouri', 'MO', false),
('Montana', 'MT', false),
('Nebraska', 'NE', false),
('Nevada', 'NV', false),
('New Hampshire', 'NH', false),
('New Jersey', 'NJ', false),
('New Mexico', 'NM', false),
('New York', 'NY', false),
('North Carolina', 'NC', false),
('North Dakota', 'ND', false),
('Ohio', 'OH', false),
('Oklahoma', 'OK', false),
('Oregon', 'OR', true),
('Pennsylvania', 'PA', false),
('Rhode Island', 'RI', false),
('South Carolina', 'SC', false),
('South Dakota', 'SD', false),
('Tennessee', 'TN', false),
('Texas', 'TX', false),
('Utah', 'UT', false),
('Vermont', 'VT', false),
('Virginia', 'VA', false),
('Washington', 'WA', true),
('West Virginia', 'WV', false),
('Wisconsin', 'WI', false),
('Wyoming', 'WY', false),
('District of Columbia', 'DC', true);

-- =========================================
-- 🧠 SEED SAMPLE SERVICES
-- =========================================

INSERT INTO services (id, title, description, service_type, price, duration_minutes, is_active) VALUES
(gen_random_uuid(), 'Initial Consultation', 'Comprehensive assessment and treatment planning session', 'consulting', 150.00, 60, true),
(gen_random_uuid(), 'Follow-up Session', 'Progress review and continued support', 'consulting', 100.00, 45, true),
(gen_random_uuid(), 'Group Therapy Session', 'Therapeutic group session for healing and growth', 'consulting', 75.00, 90, true),
(gen_random_uuid(), 'Psychedelic Integration Support', 'Professional integration support for psychedelic experiences', 'consulting', 125.00, 60, true),
(gen_random_uuid(), 'Doula Certification Program', 'Comprehensive training program for aspiring doulas', 'training', 2500.00, null, true),
(gen_random_uuid(), 'Integration Workshop', 'Weekend workshop on psychedelic integration techniques', 'training', 450.00, null, true),
(gen_random_uuid(), 'Harm Reduction Training', 'Evidence-based harm reduction training program', 'training', 750.00, null, true);

-- =========================================
-- 🎓 SEED SAMPLE TRAINING PROGRAMS
-- =========================================

INSERT INTO trainings (id, title, description, start_date, end_date, location, capacity, state_id, is_online, is_onsite, price) VALUES
(gen_random_uuid(), 
 'Psychedelic Doula Certification - Spring 2025', 
 'Comprehensive 3-month certification program covering all aspects of psychedelic doula practice',
 '2025-03-01', 
 '2025-05-31', 
 'Denver, CO', 
 25, 
 (SELECT id FROM states WHERE abbreviation = 'CO'), 
 false, 
 true, 
 2500.00),

(gen_random_uuid(), 
 'Online Integration Fundamentals', 
 'Virtual 6-week course on psychedelic integration principles and practices',
 '2025-02-15', 
 '2025-03-28', 
 'Virtual/Online', 
 50, 
 null, 
 true, 
 false, 
 750.00),

(gen_random_uuid(), 
 'Harm Reduction Intensive - West Coast', 
 'Weekend intensive on harm reduction practices in psychedelic contexts',
 '2025-04-12', 
 '2025-04-13', 
 'Portland, OR', 
 30, 
 (SELECT id FROM states WHERE abbreviation = 'OR'), 
 false, 
 true, 
 450.00);

-- =========================================
-- 👥 CREATE INITIAL ADMIN USER
-- =========================================
-- 
-- NOTE: In production, you should create this user 
-- through Supabase Auth, not directly in the database.
-- This is just for development/testing purposes.
-- 
-- Uncomment and modify the following if needed for development:
-- 

/*
INSERT INTO users (id, first_name, last_name, email, role) VALUES
(gen_random_uuid(), 'Admin', 'User', 'admin@doulalife.com', 'administrator');
*/

-- =========================================
-- ✅ INITIAL DATA SEEDING COMPLETE
-- =========================================
-- 
-- Your database now has:
-- ✅ All 50 US states + DC with psychedelic legal status
-- ✅ Sample services for consulting and training
-- ✅ Sample training programs
-- 
-- Next: Create your first admin user through Supabase Auth
-- =========================================