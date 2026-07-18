# scripts/setup_db.py
# AlphaEdge V13.0.7 – Database Setup Script
# Item 16: TimescaleDB Integration

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_validator import load_config


async def setup_database():
    """Initialize TimescaleDB database"""
    
    # Load config
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    config = load_config(config_path)
    db_config = config.get('timescaledb', {})
    
    # Get config values with defaults
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 5432)
    database = db_config.get('database', 'alphaedge')
    user = db_config.get('user', 'alphaedge')
    password = db_config.get('password', '')
    
    # Read schema
    schema_path = Path(__file__).parent.parent / 'database' / 'schema.sql'
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
        
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    # Connect and create schema
    try:
        # Step 1: Connect to default postgres database first
        print(f"🔗 Connecting to postgres at {host}:{port}...")
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database='postgres',
            user=user,
            password=password
        )
        
        # Step 2: Check if database exists
        result = await conn.fetch(
            "SELECT 1 FROM pg_database WHERE datname = $1", database
        )
        
        if not result:
            print(f"📁 Creating database: {database}")
            await conn.execute(f"CREATE DATABASE {database}")
        else:
            print(f"✅ Database {database} already exists")
            
        await conn.close()
        
        # Step 3: Connect to the new database
        print(f"🔗 Connecting to {database}...")
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # Step 4: Execute schema
        print("📊 Creating tables and extensions...")
        await conn.execute(schema)
        
        # Step 5: Verify tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print("\n📋 Created tables:")
        for table in tables:
            print(f"   - {table['tablename']}")
            
        await conn.close()
        
        print("\n✅ Database schema created successfully!")
        print(f"   Database: {database}")
        print(f"   Host: {host}:{port}")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


async def test_connection():
    """Test database connection"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    config = load_config(config_path)
    db_config = config.get('timescaledb', {})
    
    try:
        conn = await asyncpg.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'alphaedge'),
            user=db_config.get('user', 'alphaedge'),
            password=db_config.get('password', '')
        )
        
        # Get TimescaleDB version
        version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
        print(f"✅ TimescaleDB version: {version}")
        
        # Get table count
        count = await conn.fetchval("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
        print(f"📋 Tables: {count}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AlphaEdge Database Setup')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_connection())
    else:
        asyncio.run(setup_database())
