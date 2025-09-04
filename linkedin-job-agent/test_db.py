#!/usr/bin/env python3
"""Test database connection."""

from src.database.models import Base
from src.config import Settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def test_connection():
    """Test database connection."""
    settings = Settings()
    print(f"Connecting to: {settings.database_url}")
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    
    try:
        # Create tables
        Base.metadata.create_all(engine)
        print("✓ Tables created successfully")
        
        # Test connection
        session = SessionLocal()
        result = session.execute(text("SELECT 1"))
        session.close()
        print("✓ Database connection successful!")
        
        # List tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)