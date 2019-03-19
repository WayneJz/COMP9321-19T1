'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Zhou JIANG
Student ID: z5146092
'''
from flask import Flask
from flask_restplus import Resource, Api, fields
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
    if len(re.findall(';', command)) > 1:
        cursor.executescript(command)
    else:
        cursor.execute(command)
    result = cursor.fetchall()      # If multiple commands, no output will be fetched
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
                        'collection_name VARCHAR(100),'
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


def collection_table_json_template(query_result):
    return {"location": "/{}/{}".format(query_result[1], query_result[0]),
            "collection_id": "{}".format(query_result[0]),
            "creation_time": "{}".format(query_result[4]),
            "indicator": "{}".format(query_result[2])
            }


def retrieve_one_json_template(collection_query, entries_query):
    result = {"collection_id": "{}".format(collection_query[0]),
              "indicator": "{}".format(collection_query[2]),
              "indicator_value": "{}".format(collection_query[3]),
              "creation_time": "{}".format(collection_query[4]),
              "entries": []
              }
    for i in range(len(entries_query)):
        result["entries"].append({"country": entries_query[i][1],
                                  "date": entries_query[i][2],
                                  "value": entries_query[i][3]
                                  })
    return result


def request_handler(database, collection, action, **kwargs):
    if action == 'post':
        return post_handler(database, collection, kwargs['indicator'])
    elif action == 'delete':
        return delete_handler(database, collection, kwargs['collection_id'])
    elif action == 'getall':
        return get_handler(database, collection, 'getall')
    elif action == 'getone':
        return get_handler(database, collection, 'getone', collection_id=kwargs['collection_id'])


def get_handler(database, collection, action, **kwargs):
    if action == 'getall':
        query = database_controller(database, f"SELECT * FROM Collection WHERE collection_name ='{collection}';")
        if query:
            result_list = list()
            for i in range(len(query)):
                result_list.append(collection_table_json_template(query[i]))
            return result_list, 200
        return {"message": f"The collection '{collection}' not found in data source!"}, 404

    elif action == 'getone':
        collection_query = database_controller(database,
                                    f"SELECT * FROM Collection WHERE collection_name = '{collection}' "
                                    f"AND collection_id = {kwargs['collection_id']};")
        entries_query = database_controller(database,
                                    f"SELECT * FROM Entries WHERE id = {kwargs['collection_id']};")
        if collection_query:
            return retrieve_one_json_template(collection_query[0], entries_query), 200
        return {"message":
                    f"The collection '{collection} with id {kwargs['collection_id']}'not found in data source!"}, 404


def post_handler(database, collection, indicator):
    query = database_controller(database, f"SELECT * FROM Collection WHERE indicator ='{indicator}';")
    if query:
        return collection_table_json_template(query[0]), 200
    else:
        data_first_page = remote_request(indicator, 1)
        data_second_page = remote_request(indicator, 2)
        if not data_first_page or not data_second_page:
            return {"message": f"The indicator '{indicator}' not found in data source!"}, 404
        new_id = re.findall('\d+', str(database_controller(database, 'SELECT MAX(collection_id) FROM Collection;')))
        if not new_id:
            new_id = 1
        else:
            new_id = int(new_id[0]) + 1
        collection_table_updater(database, new_id, collection, data_first_page)
        entry_table_updater(database, new_id, data_first_page)
        entry_table_updater(database, new_id, data_second_page)
        new_query = database_controller(database, f"SELECT * FROM Collection WHERE indicator = '{indicator}';")
        return collection_table_json_template(query[0]), 201


def delete_handler(database, collection, collection_id):
    query = database_controller(database,
                                f"SELECT * FROM Collection WHERE collection_name = '{collection}' "
                                f"AND collection_id = {collection_id};")
    if not query:
        return {"message": f"Collection = {collection_id} NOT FOUND in the database!"}, 404
    else:
        database_controller(database, f"DELETE FROM Entries WHERE id = {collection_id};")
        database_controller(database, f"DELETE FROM Collection WHERE collection_name = '{collection}';")
        return {"message": f"Collection = {collection_id} is removed from the database!"}, 200


def collection_table_updater(database, given_id, given_collection_name, data):
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    collection = "INSERT INTO Collection VALUES ({}, '{}', '{}', '{}', '{}');"\
        .format(given_id, given_collection_name, data[0]['indicator']['id'], data[0]['indicator']['value'],
                cur_time)
    database_controller(database, collection)


def entry_table_updater(database, given_id, data):
    entry = "INSERT INTO Entries VALUES"
    for sub_data in data:
        entry += f"({given_id}, '{sub_data['country']['value']}', '{sub_data['date']}', '{sub_data['value']}'),"
    entry = entry.rstrip(',') + ';'
    database_controller(database, entry)


post_model = api.model('POST Payload', {"indicator_id": fields.String("NY.GDP.MKTP.CD")})


@api.route("/<collections>")
class SingleRoute(Resource):
    @api.expect(post_model)
    def post(self, collections):
        if not api.payload or 'indicator_id' not in api.payload:
            api.abort(400)
        return request_handler('data.db', collections, 'post', indicator=api.payload['indicator_id'])

    def get(self, collections):
        return request_handler('data.db', collections, 'getall')


@api.route("/<collections>/<collection_id>")
class DualRoute(Resource):
    def delete(self, collections, collection_id):
        return request_handler('data.db', collections, 'delete', collection_id=collection_id)

    def get(self, collections, collection_id):
        return request_handler('data.db', collections, 'getone', collection_id=collection_id)


if __name__ == "__main__":
    create_db('data.db')
    app.run(host='127.0.0.1', port=8888, debug=True)


