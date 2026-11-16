
from sqlalchemy import inspect

from app.database import Base, engine
from app.models.order import Order, OrderItem


print("Starting table creation...")

Base.metadata.create_all(bind=engine)

print("Registered models:", list(Base.metadata.tables.keys()))

inspector = inspect(engine)
print("Tables in MySQL:", inspector.get_table_names())
