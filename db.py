from sqlalchemy import create_engine, text
import os
import config

# Create the SQLAlchemy engine for the PostgreSQL database
engine = create_engine(config.DATABASE_URI)

def init_db():
    # Initialize the database schema if not already present
    with engine.connect() as conn:
        # Check if a core table (amenities) exists
        result = conn.execute(text("SELECT to_regclass('public.amenities')"))
        if result.scalar() is None:
            # If not, execute schema SQL file to create all tables
            schema_path = os.path.join(os.path.dirname(__file__), 'model-citizen.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            # Execute each statement within a transaction
            with engine.begin() as trans_conn:
                for statement in schema_sql.split(';'):
                    if statement.strip():
                        trans_conn.execute(text(statement))
