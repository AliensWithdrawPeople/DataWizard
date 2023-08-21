from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from . import Models


url = URL.create(
    drivername="postgresql",
    username="postgres",
    password="qwerty",
    host="/tmp/postgresql/socket",
    database="DataWizard"
)

engine = create_engine("postgresql+psycopg2://wizard:password@localhost/test")
connection = engine.connect()
Models.Base.metadata.create_all(engine)

def get_session():
    Session = sessionmaker(bind=engine)
    return Session()