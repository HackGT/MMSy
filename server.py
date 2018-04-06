from aiohttp import web

from routes import routes
from db import pg_engine
from worker import worker

def create_app():
    app = web.Application()

    app.add_routes(routes)

    app.cleanup_ctx.append(pg_engine)
    app.cleanup_ctx.append(worker)

    return app

if __name__=='__main__':
    # TODO CLI arguments
    app = create_app()
    web.run_app(app, host='127.0.0.1', port=5000)
