from .views import app
from . import models
from . import filters

# Connect sqlalchemy to app
models.db.init_app(app)


@app.cli.command()
def init_db():
    models.init_db()
