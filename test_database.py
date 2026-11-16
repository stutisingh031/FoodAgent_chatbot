
from app.database import check_database_connection

if check_database_connection():
    print("MySQL connection successful!")
else:
    print("MySQL connection failed. Check the log for details.")
