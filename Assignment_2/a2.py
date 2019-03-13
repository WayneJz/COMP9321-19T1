'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Zhou JIANG
Student ID: z5146092
'''
from flask import Flask, request
from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os


def create_db(db_file):
    if os.path.exists(db_file):
        print('Database already exists! Creating operation is not permitted.')
        return
    with sqlite3.connect(db_file) as connection:
        cursor = connection.cursor()
        cursor.execute('')

'''
Put your API code below. No certain requriement about the function name as long as it works.
'''

app = Flask(__name__)
api = Api(app, title="COMP9321 Assignment 2", description="API for World Bank Economic Indicators.")


@app.route("/", methods=["GET"])
def get():
    if request.method == "GET":
        return '123'


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8888, debug=True)


