import os

DB = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'port': '3306',
    'db_name': 'medicine',
}

DB_Query = {
    'conn_url': 'mysql://{user}:{password}@{host}:{port}'.format(**DB),
    'db_url': 'mysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8'.format(**DB),
    'create_db': 'CREATE DATABASE {db_name} DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;'.format(**DB),
}

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

Path = {
    'data_dir': os.path.join(ROOT_DIR, 'data'),
}
