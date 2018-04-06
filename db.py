from aiopg.sa import create_engine

from config import POSTGRES_URL

async def pg_engine(app):
    engine = await create_engine(
        dsn = POSTGRES_URL,
        loop = app.loop
    )
    app['db'] = engine

    yield

    app['db'].close()
    await app['db'].wait_closed()
