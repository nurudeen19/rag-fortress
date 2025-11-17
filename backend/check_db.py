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
        # Get users with hashed password
        result = conn.execute(text('SELECT id, username, email, password_hash FROM users'))
        for row in result:
            print(f"User: {row[1]} ({row[2]})")
            print(f"  Password Hash: {row[3][:50]}...")
except Exception as e:
    print(f"Error: {e}")




