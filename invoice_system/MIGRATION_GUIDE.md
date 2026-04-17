# Database Migration Guide

## Quick Setup

You have two options to apply the database schema updates:

### Option 1: Using Python Migration Runner (Recommended) ⚡

This is the easiest method. Run the migration script from your invoice system folder:

```bash
cd E:\all projects\myapp\invoice_system
python migrate.py
```

This will automatically:
- ✅ Add `bank_name`, `bank_account`, `ifsc_code` columns to `company_settings` table
- ✅ Add `address`, `contact` columns to `customers` table
- ✅ Handle cases where columns already exist
- ✅ Show clear feedback on what was applied

**Expected Output:**
```
📝 Running migration: 001_add_company_bank_details.sql
   ✅ Executed: ALTER TABLE company_settings ADD COLUMN bank_name VARCHAR(100)...
   ✅ Executed: ALTER TABLE company_settings ADD COLUMN bank_account VARCHAR(50)...
   ✅ Executed: ALTER TABLE company_settings ADD COLUMN ifsc_code VARCHAR(20)...
   ✅ Executed: ALTER TABLE customers ADD COLUMN address VARCHAR(255)...
   ✅ Executed: ALTER TABLE customers ADD COLUMN contact VARCHAR(20)...
✅ Migration 001_add_company_bank_details.sql completed successfully!

============================================================
✅ All migrations completed successfully!
============================================================
```

---

### Option 2: Using MySQL Client Directly 🔧

If you prefer using MySQL directly, run these SQL commands in your MySQL client:

```sql
-- Add bank details to company_settings
ALTER TABLE company_settings ADD COLUMN bank_name VARCHAR(100) DEFAULT '';
ALTER TABLE company_settings ADD COLUMN bank_account VARCHAR(50) DEFAULT '';
ALTER TABLE company_settings ADD COLUMN ifsc_code VARCHAR(20) DEFAULT '';

-- Add address and contact to customers
ALTER TABLE customers ADD COLUMN address VARCHAR(255) DEFAULT '';
ALTER TABLE customers ADD COLUMN contact VARCHAR(20) DEFAULT '';
```

**Using MySQL Command Line:**
```bash
mysql -u root -p invoice_db < migrations/001_add_company_bank_details.sql
```

---

### Option 3: Using MySQL Workbench 🖥️

1. Open MySQL Workbench
2. Connect to your database
3. Paste the SQL commands from your `migrations/001_add_company_bank_details.sql` file
4. Click "Execute" button

---

## Verify Migration Success

After applying migrations, verify the columns were created:

```sql
-- Check company_settings table columns
DESC company_settings;

-- Check customers table columns  
DESC customers;
```

You should see the new columns in both tables.

---

## Troubleshooting

### "Column already exists" Warning
This is **NOT an error** - it means the columns were already in your database. You can safely ignore this message.

### "Unknown column 'bank_account'" Error
This means the migrations haven't been applied yet. Choose one of the options above to apply them.

### Connection Error When Running Python Migration
Make sure:
1. ✅ MySQL server is running
2. ✅ Your database credentials in `.env` are correct
3. ✅ You're in the correct directory (`invoice_system`)

---

## Files Created

- `migrations/001_add_company_bank_details.sql` - SQL migration file
- `migrate.py` - Python migration runner script

## Features Added After Migration

Once migration is complete, you'll have:

- ✅ Bank account details in company settings page
- ✅ Customer address and contact number fields
- ✅ Complete invoice PDFs with all company and customer information
- ✅ Better payment tracking with customer details
- ✅ Enhanced customer management interface

---

## Need Help?

If you encounter any issues:

1. Check that MySQL is running
2. Verify your database credentials in `.env`
3. Ensure the `migrations` folder exists in `invoice_system`
4. Check the error message - it usually indicates what's wrong

For additional help, you can manually check your database structure:

```sql
USE invoice_db;
SHOW TABLES;
DESCRIBE company_settings;
DESCRIBE customers;
```
