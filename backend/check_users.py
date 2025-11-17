from app.config.database_settings import DatabaseSettings
from sqlalchemy import create_engine, text

db_settings = DatabaseSettings()
db_config = db_settings.get_database_config()

# Build the connection URL
if db_config['provider'] == 'mysql':
    url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
elif db_config['provider'] == 'postgresql':
    url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
else:
    url = f"sqlite:///{db_config['path']}"

try:
    # Connect and check users table
    engine = create_engine(url)
    with engine.connect() as conn:
        # Get users
        result = conn.execute(text('SELECT id, username, email, is_active, is_verified, is_suspended FROM users'))
        print("All Users:")
        for row in result:
            print(f"  ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Active: {row[3]}, Verified: {row[4]}, Suspended: {row[5]}")
except Exception as e:
    print(f"Error: {e}")
