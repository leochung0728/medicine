from medicine import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from medicine.config import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_Query['db_url']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db, directory=config.Path['MIGRATION_DIR'])

manager = Manager(app)
manager.add_command('db', MigrateCommand)

from medicine.models import medicine, alias, compound, medicine_compound, property
import medicine.views.index
