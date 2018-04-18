from sqlalchemy import create_engine
from medicine.flask_app import db
from medicine import config
from medicine.models import medicine, alias, compound, medicine_compound, property


if __name__ == '__main__':
    engine = create_engine(config.DB_Query['conn_url'], encoding='utf-8', echo=False)
    existing_databases = engine.execute("SHOW DATABASES;")
    existing_databases = [d[0] for d in existing_databases]

    database = config.DB['db_name']
    if database not in existing_databases:
        engine.execute(config.DB_Query['create_db'])
        print("Created database {}".format(database))
        db.create_all()
