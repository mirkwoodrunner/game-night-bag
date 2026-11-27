from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate(render_as_batch=True)  # batch mode so SQLite can alter tables
