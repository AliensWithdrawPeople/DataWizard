from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


url = URL.create(
    drivername="postgresql",
    username="postgres",
    password="qwerty",
    host="/tmp/postgresql/socket",
    database="DataWizard"
)

engine = create_engine("postgresql+psycopg2://wizard:password@localhost/testtable1")
connection = engine.connect()

def get_session():
    Session = sessionmaker(bind=engine)
    return Session()