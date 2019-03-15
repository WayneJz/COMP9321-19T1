'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Zhou JIANG
Student ID: z5146092
'''
from flask import Flask, request
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os
import json
import time
import re
import urllib.request as req

app = Flask(__name__)
api = Api(app, title="World Bank", description="API for World Bank Economic Indicators.")


def database_controller(database, command):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.executescript(command)
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return result


def create_db(db_file):
    if os.path.exists(db_file):
        print('Database already exists.')
        return False
    print('Creating database ...')
    database_controller(db_file,
                        'CREATE TABLE Collection('
                        'collection_id INTEGER UNIQUE NOT NULL,'
                        'indicator VARCHAR(100),'
                        'indicator_value VARCHAR(100),'
                        'creation_time DATE,'
                        'CONSTRAINT collection_fkey PRIMARY KEY (collection_id));'
                        +
                        'CREATE TABLE Entries('
                        'id INTEGER NOT NULL,'
                        'country VARCHAR(100),'
                        'date VARCHAR(10),'
                        'value VARCHAR(100),'
                        'CONSTRAINT entry_fkey FOREIGN KEY (id) REFERENCES Collection(collection_id));'
                        )
    return True


def remote_request(indicator, start=2013, end=2018, content_format='json', page=2):
    for i in range(1, page + 1):
        url = f'http://api.worldbank.org/v2/countries/all/indicators/' + \
              f'{indicator}?date={start}:{end}&format={content_format}&page={i}'
        resource = req.Request(url)
        data = req.urlopen(resource).read()
        return json.loads(data)[1]


def collection_table_updater(database, indicator, action):
    query = database_controller(database, f"SELECT * FROM Collection WHERE indicator = '{indicator}';")
    if query:
        if action == 'post':
            return query
        if action == 'delete':
            new_id = int(re.search('\d+', str(query)).group())
            database_controller(database, f"DELETE FROM Entries WHERE id = {new_id};")
            database_controller(database, f"DELETE FROM Collection WHERE indicator = '{indicator}';")
            return True
    else:
        if action == 'post':
            pass





def data_import(database, data):
    new_id = re.findall('\d+', str(database_controller(database, 'SELECT MAX(collection_id) FROM Collection;')))
    if not new_id:
        new_id = 1
    else:
        new_id = int(new_id[0]) + 1
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    collection = "INSERT INTO Collection(collection_id, indicator, indicator_value, creation_time) VALUES"
    collection += "({}, '{}', '{}', '{}');"\
        .format(new_id, data[0]['indicator']['id'], data[0]['indicator']['value'], cur_time)
    database_controller(database, collection)

    entry = "INSERT INTO Entries(id, country, date, value) VALUES"
    for sub_data in data:
        entry += "({}, '{}', '{}', '{}'),"\
            .format(new_id, sub_data['country']['value'], sub_data['date'], sub_data['value'])
    entry = entry.rstrip(',') + ';'
    database_controller(database, entry)


@api.route("/<string:collections>")
class Post(Resource):
    def post(self, collections=''):
        query = database_controller('test.db', "SELECT * FROM Collection WHERE indicator = '{}';".format(collections))
        if not query:
            pass


if __name__ == "__main__":
    create_db('test.db')
    # app.run(host='127.0.0.1', port=8888, debug=True)
    data_import('test.db', remote_request("NY.GDP.MKTP.CD"))


