'''
COMP9321 2019 Term 1 Assignment Two
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
api = Api(app, title="World Bank", description="API for World Bank Economic Indicators. Zhou JIANG z5146092")


# database controller, for executing SQL command and fetching results
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


# database initialization
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


# remote API request, fetching data from worldbank API
def remote_request(indicator, page, start=2013, end=2018, content_format='json'):
    url = f'http://api.worldbank.org/v2/countries/all/indicators/' + \
          f'{indicator}?date={start}:{end}&format={content_format}&page={page}'
    resource = req.Request(url)
    data = req.urlopen(resource).read()
    if re.findall('Invalid value', str(data), flags=re.I):
        return False
    return json.loads(data)[1]


# a template function, convert SQL query result to json-like format, format 1
def collection_table_json_template(query_result):
    return {"location": "/{}/{}".format(query_result[1], query_result[0]),
            "collection_id": "{}".format(query_result[0]),
            "creation_time": "{}".format(query_result[4]),
            "indicator": "{}".format(query_result[2])
            }


# a template function, convert SQL query result to json-like format, format 2
def retrieve_one_json_template(collection_query, entries_query):
    result = {"collection_id": "{}".format(collection_query[0]),
              "indicator": "{}".format(collection_query[2]),
              "indicator_value": "{}".format(collection_query[3]),
              "creation_time": "{}".format(collection_query[4]),
              "entries": []
              }
    for i in range(len(entries_query)):
        result["entries"].append({"country": entries_query[i][0],
                                  "date": entries_query[i][1],
                                  "value": entries_query[i][2]
                                  })
    return result


# uniform request handler, all requests received will be firstly handled by this function
def request_handler(database, collection, action, **kwargs):
    if action == 'post':
        return post_handler(database, collection, kwargs['indicator'])
    elif action == 'delete':
        return delete_handler(database, collection, kwargs['collection_id'])
    elif action == 'getall':
        return get_handler(database, collection, 'getall')
    elif action == 'getone':
        return get_handler(database, collection, 'getone', collection_id=kwargs['collection_id'])
    elif action == 'getoneyc':
        return get_handler(database, collection, 'getoneyc', collection_id=kwargs['collection_id'],
                           year=kwargs['year'], country=kwargs['country'])
    elif action == 'gettopbottom':
        top_test = re.search("^(top)(\d+)$", kwargs['query'])
        bottom_test = re.search("^(bottom)(\d+)$", kwargs['query'])
        if top_test:
            return get_handler(database, collection, 'gettopbottom', collection_id=kwargs['collection_id'],
                               year=kwargs['year'], flag='top', value=top_test.group(2))
        if bottom_test:
            return get_handler(database, collection, 'gettopbottom', collection_id=kwargs['collection_id'],
                               year=kwargs['year'], flag='bottom', value=bottom_test.group(2))
        else:
            return {"message":
                    "Your input arguments are not in correct format! Must be either top<int> or bottom<int>."}, 400


# dealing with all get requests, for question 3-6
def get_handler(database, collection, action, **kwargs):
    
    # question 3, get all collections info
    if action == 'getall':
        query = database_controller(database, f"SELECT * FROM Collection WHERE collection_name ='{collection}';")
        if query:
            result_list = list()
            for i in range(len(query)):
                result_list.append(collection_table_json_template(query[i]))
            return result_list, 200
        return {"message": f"The collection '{collection}' not found in data source!"}, 404

    # question 4, get one specified collection and its data
    elif action == 'getone':
        collection_query = database_controller(database,
                                               f"SELECT * "
                                               f"FROM Collection "
                                               f"WHERE collection_name = '{collection}'"
                                               f"AND collection_id = {kwargs['collection_id']};")

        entries_query = database_controller(database,
                                            f"SELECT country, date, value "
                                            f"FROM Entries "
                                            f"WHERE id = {kwargs['collection_id']};")
        if collection_query:
            return retrieve_one_json_template(collection_query[0], entries_query), 200
        return {"message":
                f"The collection '{collection}' with id {kwargs['collection_id']} not found in data source!"}, 404

    # question 5, get data for specified year, id and country
    elif action == 'getoneyc':
        join_query = database_controller(database,
                                         f"SELECT collection_id, indicator, country, date, value "
                                         f"FROM Collection "
                                         f"JOIN Entries ON (Collection.collection_id = Entries.id) "
                                         f"WHERE collection_id = {kwargs['collection_id']} "
                                         f"AND date = '{kwargs['year']}' "
                                         f"AND country = '{kwargs['country']}';")
        if join_query:
            return {"collection_id": "{}".format(join_query[0][0]),
                    "indicator": "{}".format(join_query[0][1]),
                    "country": "{}".format(join_query[0][2]),
                    "year": "{}".format(join_query[0][3]),
                    "value": "{}".format(join_query[0][4])
                    }, 200
        return {"message":
                f"The given arguments collections = '{collection}', {kwargs} not found in data source!"}, 404

    # question 6, get data for specified year, id, sort by its value, can be either descent or ascent.
    elif action == 'gettopbottom':
        insert_flag = ''
        if kwargs['flag'] == 'top':     # if get top, it should be reverse sort and limit first values
            insert_flag = 'DESC'

        collection_query = database_controller(database,
                                               f"SELECT * FROM Collection WHERE collection_name = '{collection}'"
                                               f"AND collection_id = {kwargs['collection_id']};")

        # should use cast(value as real), otherwise it sorted by string order
        entries_query = database_controller(database,
                                            f"SELECT country, date, value "
                                            f"FROM Entries "
                                            f"WHERE id = {kwargs['collection_id']} "
                                            f"AND date = '{kwargs['year']}' "
                                            f"AND value != 'None' "
                                            f"GROUP BY country, date, value "
                                            f"ORDER BY CAST(value AS REAL) {insert_flag} "
                                            f"LIMIT {kwargs['value']};")

        if collection_query:
            result_dict = retrieve_one_json_template(collection_query[0], entries_query)
            result_dict.pop("collection_id")
            result_dict.pop("creation_time")
            return result_dict, 200
        return {"message":
                f"No data matches your specified arguments in the database!"}, 404


# dealing with all post requests, for question 1
def post_handler(database, collection, indicator):
    query = database_controller(database, f"SELECT * FROM Collection WHERE indicator = '{indicator}';")
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
        return collection_table_json_template(new_query[0]), 201


# dealing with all delete requests, for question 2
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


# importing data, store in database for table collection, called by post handler
def collection_table_updater(database, given_id, given_collection_name, data):
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    collection = "INSERT INTO Collection VALUES ({}, '{}', '{}', '{}', '{}');"\
        .format(given_id, given_collection_name, data[0]['indicator']['id'], data[0]['indicator']['value'],
                cur_time)
    database_controller(database, collection)


# importing data, store in database for table collection, called by post handler
def entry_table_updater(database, given_id, data):
    entry = "INSERT INTO Entries VALUES"
    for sub_data in data:
        entry += f"({given_id}, '{sub_data['country']['value']}', '{sub_data['date']}', '{sub_data['value']}'),"
    entry = entry.rstrip(',') + ';'
    database_controller(database, entry)


post_model = api.model('POST Payload', {"indicator_id": fields.String("NY.GDP.MKTP.CD")})
parser = api.parser()
parser.add_argument('q', type=str, help='Your query here (e.g."top10")', location='args')


# single-path route class, for question 1 and 3
@api.route("/<string:collections>")
@api.response(200, 'OK')
@api.response(400, 'Bad Request')
@api.response(404, 'Not Found')
@api.response(201, 'Created')
class SingleRoute(Resource):
    @api.expect(post_model)
    def post(self, collections):
        if not api.payload or 'indicator_id' not in api.payload:
            return {
                "message": "Please check if the indicator_id is given!"
            }, 400
        return request_handler('data.db', collections, 'post', indicator=api.payload['indicator_id'])

    def get(self, collections):
        return request_handler('data.db', collections, 'getall')


# double-paths route class, for question 2 and 4
@api.route("/<string:collections>/<int:collection_id>")
@api.response(200, 'OK')
@api.response(400, 'Bad Request')
@api.response(404, 'Not Found')
class DualRoute(Resource):
    def delete(self, collections, collection_id):
        return request_handler('data.db', collections, 'delete', collection_id=collection_id)

    def get(self, collections, collection_id):
        return request_handler('data.db', collections, 'getone', collection_id=collection_id)


# quad-paths route class, for question 5
@api.route("/<string:collections>/<int:collection_id>/<int:year>/<string:country>")
@api.response(200, 'OK')
@api.response(400, 'Bad Request')
@api.response(404, 'Not Found')
class QuadRoute(Resource):
    def get(self, collections, collection_id, year, country):
        return request_handler('data.db', collections, 'getoneyc', collection_id=collection_id,
                               year=year, country=country)


# triple-paths route class, with argument required, for question 6
@api.route("/<string:collections>/<int:collection_id>/<int:year>")
@api.doc(parser=parser)
@api.response(200, 'OK')
@api.response(400, 'Bad Request')
@api.response(404, 'Not Found')
class ArgsRoute(Resource):
    def get(self, collections, collection_id, year):
        query = parser.parse_args()['q']
        return request_handler('data.db', collections, 'gettopbottom', collection_id=collection_id,
                               year=year, query=query)


if __name__ == "__main__":
    create_db('data.db')
    app.run(host='127.0.0.1', port=8888, debug=True)


