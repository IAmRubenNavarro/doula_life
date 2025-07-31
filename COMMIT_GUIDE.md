# 📝 Git Commit Guide

## ✅ **SAFE TO COMMIT - Include in Git**

### **Database Schema & Migrations**
- ✅ `database/schema.sql` - Complete database schema
- ✅ `database/migrations/` - All migration files
- ✅ `database/README.md` - Database documentation

### **Application Code**
- ✅ `app/` - All Python application code
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Project documentation
- ✅ `test_*.py` - Test files
- ✅ `unified_payments_app.py` - Standalone payment API

### **Configuration Templates**
- ✅ `.env.example` - Environment variable template (no secrets)
- ✅ `config/` - Configuration files (without secrets)
- ✅ `.gitignore` - Git ignore rules
- ✅ `Dockerfile` - Container configuration
- ✅ `docker-compose.yml` - Docker setup (without secrets)

### **Documentation & Guides**
- ✅ All `*.md` files - Documentation
- ✅ `docs/` - Project documentation
- ✅ API documentation files

## ❌ **NEVER COMMIT - Keep Secret**

### **Environment Files with Secrets**
- ❌ `.env` - Contains API keys and secrets
- ❌ `.env.production` - Production secrets
- ❌ `.env.local` - Local development secrets
- ❌ `secrets.json` - Any file with secrets

### **API Keys & Credentials**
- ❌ Stripe secret keys (`sk_live_*`, `sk_test_*`)
- ❌ PayPal client secrets
- ❌ Database passwords
- ❌ JWT secret keys
- ❌ Any `*_SECRET_*` environment variables

### **SSL Certificates & Keys**
- ❌ `*.pem` - Private keys
- ❌ `*.key` - Private keys  
- ❌ `*.crt` - Certificates
- ❌ `*.p12` - Certificate bundles

### **Generated Files**
- ❌ `__pycache__/` - Python cache
- ❌ `logs/` - Application logs
- ❌ `venv/` - Virtual environment
- ❌ `node_modules/` - If you add Node.js tools

## 🔧 **SETUP: Create Environment Template**

Create `.env.example` for team members:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
SECRET_KEY=your-super-secret-key-here

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Stripe Payment Processing
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# PayPal Payment Processing
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=sandbox
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id

# Application Settings
ENVIRONMENT=development
DEBUG=true
```

## 🚀 **GIT WORKFLOW**

### **Before First Commit**
```bash
# 1. Ensure .env is in .gitignore
git status
# .env should NOT appear in untracked files

# 2. Check what you're about to commit
git add .
git status

# 3. Verify no secrets are being committed
git diff --cached | grep -i "secret\|key\|password"
# Should return nothing

# 4. Commit safely
git commit -m "feat: add payment system with Stripe and PayPal support

- Complete database schema with payment tables
- Stripe Payment Intent integration  
- PayPal Order and capture flow
- Unified payment interface
- Comprehensive error handling and logging
- Row Level Security policies
- Payment audit trail"
```

### **Regular Development**
```bash
# Always check before committing
git status
git diff

# Commit specific features
git add app/api/payments.py
git commit -m "feat: add PayPal webhook handling"

git add database/
git commit -m "docs: update database schema documentation"
```

### **Team Collaboration**
```bash
# New team member setup
git clone <repository>
cp .env.example .env
# Edit .env with actual values (never commit this file)
```

## 🔍 **SECURITY CHECKLIST**

Before every commit, verify:

- [ ] No `.env` files in git status
- [ ] No API keys in code comments
- [ ] No hardcoded passwords or secrets
- [ ] All sensitive config uses environment variables
- [ ] `.env.example` contains only placeholder values
- [ ] SSL certificates/keys are not included

## 🚨 **IF YOU ACCIDENTALLY COMMIT SECRETS**

**DO THIS IMMEDIATELY:**

```bash
# 1. Remove from latest commit (if not pushed)
git reset --soft HEAD~1
git reset .env  # Remove .env from staging
git commit  # Recommit without secrets

# 2. If already pushed to GitHub
# IMMEDIATELY rotate all exposed credentials:
# - Generate new Stripe API keys
# - Generate new PayPal credentials  
# - Change database passwords
# - Generate new JWT secrets

# 3. Use BFG Repo-Cleaner to remove from history
# https://rtyley.github.io/bfg-repo-cleaner/
```

## 📚 **WHY THIS MATTERS**

### **Security Benefits**
- 🔒 Prevents API key theft
- 🔒 Protects customer payment data
- 🔒 Maintains compliance (PCI DSS)
- 🔒 Prevents unauthorized access

### **Collaboration Benefits**  
- 👥 Clean repository for team members
- 👥 Easy environment setup with `.env.example`
- 👥 No accidental secret overwrites
- 👥 Clear separation of code and config

### **Deployment Benefits**
- 🚀 Environment-specific configurations
- 🚀 Secure CI/CD pipelines
- 🚀 Easy secret management
- 🚀 Rollback safety

## 🎯 **BEST PRACTICES**

1. **Always use environment variables** for secrets
2. **Keep .env.example updated** but without real values
3. **Use descriptive commit messages** for better tracking
4. **Commit database schemas** for team synchronization
5. **Document breaking changes** in commit messages
6. **Review diffs before committing** to catch accidents

---

**Remember**: When in doubt, don't commit! It's better to be safe than expose sensitive data.

**Need help?** Check if a file should be committed by looking at `.gitignore` or asking the team.