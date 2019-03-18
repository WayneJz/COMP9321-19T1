'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Zhou JIANG
Student ID: z5146092
'''
from flask import Flask, request
from flask_restplus import Resource, Api
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
                        'CONSTRAINT collection_pkey PRIMARY KEY (collection_id));'
                        +
                        'CREATE TABLE Entries('
                        'id INTEGER NOT NULL,'
                        'country VARCHAR(100),'
                        'date VARCHAR(10),'
                        'value VARCHAR(100),'
                        'CONSTRAINT entry_fkey FOREIGN KEY (id) REFERENCES Collection(collection_id));'
                        )
    return True


def remote_request(indicator, page, start=2013, end=2018, content_format='json'):
    url = f'http://api.worldbank.org/v2/countries/all/indicators/' + \
          f'{indicator}?date={start}:{end}&format={content_format}&page={page}'
    resource = req.Request(url)
    data = req.urlopen(resource).read()
    if re.findall('Invalid value', str(data), flags=re.I):
        return False
    return json.loads(data)[1]


def table_updater(database, indicator, action):
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
            data_first_page = remote_request(indicator, 1)
            data_second_page = remote_request(indicator, 2)
            if not data_first_page or not data_second_page:
                return False
            new_id = re.findall('\d+', str(database_controller(database, 'SELECT MAX(collection_id) FROM Collection;')))
            if not new_id:
                new_id = 1
            else:
                new_id = int(new_id[0]) + 1
            collection_table_updater(database, new_id, data_first_page)
            entry_table_updater(database, new_id, data_first_page)
            entry_table_updater(database, new_id, data_second_page)


def collection_table_updater(database, given_id, data):
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    collection = "INSERT INTO Collection(collection_id, indicator, indicator_value, creation_time) VALUES"
    collection += "({}, '{}', '{}', '{}');"\
        .format(given_id, data[0]['indicator']['id'], data[0]['indicator']['value'], cur_time)
    database_controller(database, collection)
    return {"location": "/{}/{}".format(data[0]['indicator']['id'], given_id),
            "collection_id": "{}".format(given_id),
            "creation_time": "{}".format(cur_time),
            "indicator": "{}".format(data[0]['indicator']['id'])}


def entry_table_updater(database, given_id, data):
    entry = "INSERT INTO Entries(id, country, date, value) VALUES"
    for sub_data in data:
        entry += "({}, '{}', '{}', '{}'),"\
            .format(given_id, sub_data['country']['value'], sub_data['date'], sub_data['value'])
    entry = entry.rstrip(',') + ';'
    database_controller(database, entry)


@api.route("/<string:collections>")
class Post(Resource):
    def post(self, collections=''):
        query = table_updater('data.db', collections, 'post')
        return query

if __name__ == "__main__":
    create_db('data.db')
    app.run(host='127.0.0.1', port=8888, debug=True)


