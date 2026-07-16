from db.db import engine
from db.models import Base

def init_db():
    Base.metadata.create_all(bind=engine)
    print("tablas creadas OK")

if __name__ == "__main__":
    init_db()