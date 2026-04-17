#!/usr/bin/env python3
"""
Database Migration Runner
Executes SQL migration files to update the database schema
"""

import os
import sys
from pathlib import Path
from app import mysql, create_app

def run_migrations():
    """Run all SQL migration files in the migrations directory"""
    
    app = create_app()
    
    with app.app_context():
        migrations_dir = Path(__file__).parent / 'migrations'
        
        if not migrations_dir.exists():
            print(f"❌ Migrations directory not found: {migrations_dir}")
            return False
        
        # Get all SQL files sorted by name (e.g., 001_*.sql, 002_*.sql)
        migration_files = sorted([f for f in migrations_dir.glob('*.sql')])
        
        if not migration_files:
            print("ℹ️  No migration files found")
            return True
        
        cur = mysql.connection.cursor()
        
        try:
            for migration_file in migration_files:
                print(f"\n📝 Running migration: {migration_file.name}")
                
                with open(migration_file, 'r') as f:
                    sql_content = f.read()
                
                # Split by semicolon and execute each statement
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                
                for statement in statements:
                    try:
                        cur.execute(statement)
                        print(f"   ✅ Executed: {statement[:80]}...")
                    except Exception as e:
                        # Check if error is "column already exists" - this is fine
                        if "already exists" in str(e) or "Duplicate column" in str(e):
                            print(f"   ⚠️  Column already exists (skipping): {statement[:80]}...")
                        else:
                            print(f"   ❌ Error: {str(e)}")
                            raise
                
                mysql.connection.commit()
                print(f"✅ Migration {migration_file.name} completed successfully!")
            
            print("\n" + "="*60)
            print("✅ All migrations completed successfully!")
            print("="*60)
            return True
            
        except Exception as e:
            mysql.connection.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            return False
        finally:
            cur.close()

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
