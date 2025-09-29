from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
from contextlib import contextmanager
import os

from flask import current_app, g

import psycopg2

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from datetime import datetime

pool = None

def setup():
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    # DATABASE_PW = os.environ['POSTGRES_PW']
    print('Connecting to database:', DATABASE_URL)
    pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL, sslmode='require')
    print('pool set up successfully, ', pool)


@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
      cursor = connection.cursor(cursor_factory=DictCursor)
      # cursor = connection.cursor()
      try:
          yield cursor
          if commit:
              connection.commit()
      finally:
          cursor.close()

def add_person (name):
    # Since we're using connection pooling, it's not as big of a deal to have
    # lots of short-lived cursors (I think -- worth testing if we ever go big)
    with get_db_cursor(True) as cur:
        cur.execute("INSERT INTO guestlist (response_timestamp, person) values (%s, %s)", (datetime.now(), name ))

def get_people(page = 0, people_per_page = 10):
    ''' note -- result can be used as list of dictionaries'''
    limit = people_per_page
    offset = page*people_per_page
    with get_db_cursor() as cur:
        cur.execute("select * from guestlist order by id limit %s offset %s", (limit, offset))
        return cur.fetchall()

@app.route('/')
def hello():
    return render_template('base.html')

@app.route('/guestList', methods=['GET', 'POST'])
def guestList(name=None):
    if request.method == 'POST':
        name = request.form.get('name')
        
        if name:
            # Process the name (save to database, etc.)
            print(f"Added guest: {name}")
            add_person(name)
            return redirect(url_for('guestList'))
    
    return render_template('guestList.html', names=get_people())

setup()
# if __name__ == '__main__':
#     print('fart')
#     setup()
#     app.run(host='127.0.0.1', port=5000, debug=True)