#!/usr/bin/env python3
"""
Database initialization and setup script
Creates database, tables, and adds production indexes
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "nlcs_db")

# Root connection (without database)
ROOT_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/"

# Database connection
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

def create_database():
    """Create database if it doesn't exist"""
    print("\n" + "="*60)
    print("🗄️  DATABASE INITIALIZATION")
    print("="*60)
    
    engine = create_engine(ROOT_URL)
    try:
        with engine.connect() as conn:
            # Create database if not exists
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
            conn.commit()
            print(f"✅ Database '{DB_NAME}' created/verified")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    finally:
        engine.dispose()
    
    return True

def create_tables():
    """Create tables with proper schema"""
    print("\n📊 Creating tables...")
    
    engine = create_engine(DB_URL)
    try:
        with engine.connect() as conn:
            # Create candidates table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS candidates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                category VARCHAR(100) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                doc_id VARCHAR(255),
                tree_json LONGTEXT,
                tree_compressed LONGTEXT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_category (category),
                KEY idx_uploaded (uploaded_at),
                KEY idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ Table 'candidates' created/verified")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        engine.dispose()
    
    return True

def verify_indexes():
    """Verify and display indexes on candidates table"""
    print("\n🔍 Verifying indexes...")
    
    engine = create_engine(DB_URL)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SHOW INDEX FROM candidates"))
            indexes = result.fetchall()
            
            if indexes:
                print("✅ Indexes found:")
                for idx in indexes:
                    print(f"   - {idx[2]}")
            else:
                print("⚠️  No indexes found")
                
    except Exception as e:
        print(f"❌ Error checking indexes: {e}")
    finally:
        engine.dispose()

def verify_connection():
    """Verify database connection"""
    print("\n🔗 Verifying connection...")
    
    engine = create_engine(DB_URL)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ MySQL connection successful")
            
            # Get record count
            count_result = conn.execute(text("SELECT COUNT(*) FROM candidates"))
            count = count_result.fetchone()[0]
            print(f"📊 Candidates in database: {count}")
            
            return True
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    finally:
        engine.dispose()

def main():
    try:
        # Step 1: Create database
        if not create_database():
            return False
        
        # Step 2: Create tables
        if not create_tables():
            return False
        
        # Step 3: Verify indexes
        verify_indexes()
        
        # Step 4: Verify connection
        if not verify_connection():
            return False
        
        print("\n" + "="*60)
        print("🎉 DATABASE SETUP COMPLETE")
        print("="*60)
        print("\nNext: Run 'python backend/main.py' to start FastAPI server")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
