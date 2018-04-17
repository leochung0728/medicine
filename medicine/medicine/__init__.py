from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from medicine.config import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_Query['db_url']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
