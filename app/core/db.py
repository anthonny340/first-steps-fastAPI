import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./blog.db')
# print(f'Conectado a: {DATABASE_URL}')

engine_kwargs = {}
if DATABASE_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}

# echo muestra el SQL ejecutado, util para ver las consultas que se estan haciendo
# future en True lo que dice es que queremos ocuparar la sintaxis moderna de SQLAlchemy 2
engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)

# autoflush lo que hace es no enviar cambios automaticos hasta hacer el commit
# autocommit en False lo que hace es que tenga control explicito sobre el commit
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
