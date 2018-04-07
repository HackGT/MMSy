from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import POSTGRES_URL

async def init_pg(app):
    engine = create_engine(POSTGRES_URL)
    app['db'] = engine
    app['session'] = sessionmaker(bind=engine)
