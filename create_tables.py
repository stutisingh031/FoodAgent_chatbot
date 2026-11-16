from sqlalchemy import inspect

from app.database import Base, engine
from app.models.order import Order, OrderItem


def create_tables():
    print("Starting table creation...")

    Base.metadata.create_all(bind=engine)

    print("Registered models:", list(Base.metadata.tables.keys()))

    inspector = inspect(engine)
    print("Tables in MySQL:", inspector.get_table_names())


if __name__ == "__main__":
    create_tables()
