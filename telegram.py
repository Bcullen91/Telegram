from telethon import TelegramClient
from telethon.tl.functions.messages import (GetHistoryRequest)
import sqlite3
from sqlite3 import Error

# Enter your channel name here
channel_name = ''

# Enter the PATH to your SQL Database, or if you are running this for the first time, where you want the DB stored.
# The path should end in a .db, example below:
# database = '/Users/user/SQL_db/database.db'
database = ''

# Enter your Telegram API information below. The ID should be an integer and the hash should be a string.
api_id = 0
api_hash = ''

# Add a date range here if you want to get user comment count between certain date ranges.
# MAKE SURE the from_date and to_date are = '' if you do not want to to limit by date.
# MAKE SURE the date range is in YYYY-MM-DD format.
from_date = '2020-01-01'
to_date = ''


def telegram_connection():
    '''
    This function connects to the Telegram api. Need to make sure your api_id
    is an integer and your api_has is a string.
    '''
    client = TelegramClient('telegram_Bot', api_id, api_hash).start()
    return client


def create_connection(db_file):
    ''' create a database connection to a SQLite DB'''
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    ''' CREATES A TABLE WHEN CALLED '''
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_user(conn, user):
    '''
    THIS CREATES THE SQL STATEMENT. YOU CALL THIS FUNCTION IN YOUR FOR LOOP
    WHILE YOU ARE LOOPING OVER ALL THE USER DATA, SO YOU SEND IT HERE FORMATTED
    CORRECTLY.
    '''
    sql = ''' INSERT INTO users(user_id,name,message_count) VALUES(?,?,?) '''
    cur = conn.cursor()
    checker = (user[0],)
    cur.execute('SELECT * FROM users WHERE user_id=?', checker)
    entry = cur.fetchone()
    if entry is None:
        cur.execute(sql, user)
        conn.commit()
    return cur.lastrowid


def create_message(conn, message):
    '''
    THIS CREATES THE SQL STATEMENT. YOU CALL THIS FUNCTION IN YOUR FOR LOOP
    WHILE YOU ARE LOOPING OVER ALL THE MESSAGE DATA, SO YOU SEND IT HERE FORMATTED
    CORRECTLY.
    '''
    sql = ''' INSERT INTO messages(id,date,message,user_id)
                VALUES(?,?,?,?) '''
    cur = conn.cursor()
    checker = (message[0],)
    cur.execute('SELECT * FROM messages WHERE id=?', checker)
    entry = cur.fetchone()
    if entry is None:
        cur.execute(sql, message)
    conn.commit()
    return cur.lastrowid


async def get_all_users(client):
    '''
    THIS FUNCTION GETS A LIST OF ALL CURRENT USERS OF A TELEGRAM GROUP
    THEN IT LOOPS THROUGH THE INFORMATION TO CREATE A NAME. SOME USERS DO NOT HAVE
    A FIRST NAME, SOME DO NOT HAVE A LAST NAME, SOME DO NOT HAVE A USERNAME, SO
    I HAVE WRITTEN IF STATEMENTS TO GET THE USERS DISPLAY NAME CORRECTLY.
    '''
    me = await client.get_me()
    all_users = []
    async for users in client.iter_participants(channel_name):
        fullName = str(users.first_name) + " " + str(users.last_name)
        if users.first_name == None:
            fullName = str(users.last_name)
        if users.last_name == None:
            if users.first_name == None:
                fullName = str(users.username)
            else:
                fullName = str(users.first_name)
        all_users.append({'id': users.id, 'name': fullName, 'message_count': 0})
    return all_users


async def get_messages(conn, client):
    '''
    THIS FUNCTION GRABS ALL OF THE MESSAGES FROM YOUR GROUP.
    IT MAKES A CONNECTION TO THE SQL MESSAGES DB, AND PULLS THE LAST
    MESSAGE_ID, THEN USES THAT AS A STARTING POINT, TO ONLY PULL
    MESSAGES AFTER THAT. EACH MESSAGE IN THE CHAT HAS AN AUTOINCREMENT
    USER_ID.
    '''
    me = await client.get_me()
    my_channel = await client.get_entity(channel_name)

    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0

    cur = conn.cursor()
    cur.execute('SELECT MAX(id) FROM messages')
    last_id = cur.fetchone()[0]
    if last_id is None:
        last_id = 1

    try:
        while True:
            if total_messages > 0:
                print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
            history = await client(GetHistoryRequest(
                peer=my_channel,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=last_id,
                hash=0
            ))
            if not history.messages:
                return all_messages
            messages = history.messages
            for message in messages:
                all_messages.append({'id': message.id, 'date': message.date.strftime('%Y-%m-%d'),
                                     'message': message.message, 'user_id': message.from_id.user_id})
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                return all_messages
    except Error as e:
        print(e)
        return all_messages


def insert_users(conn, users):
    '''
    THIS FUNCTION TAKES THE VARIABLE USERS WHICH IS A LIST OF USERS,
    AND IT LOOPS OVER THAT LIST, PULLS ALL THE CORRECT INFORMATION AND FORMATS
    IT CORRECTLY, THEN SEND THE CORRECTLY FORMATTED DATE TO THE CREATE_USER FUNCTION
    '''
    with conn:
        for item in users:
            user = (item['id'], item['name'], item['message_count'])
            create_user(conn, user)


def insert_messages(conn, messages):
    '''
    THIS FUNCTION TAKES THE VARIABLE MESSAGES WHICH IS A LIST OF ALL OF THE MESSAGES,
    AND IT LOOPS OVER THAT LIST, PULLS ALL THE CORRECT INFORMATION AND FORMATS
    IT CORRECTLY, THEN SEND THE CORRECTLY FORMATTED DATE TO THE CREATE_MESSAGE FUNCTION
    '''
    with conn:
        for item in messages:
            message = (item['id'], item['date'], item['message'], item['user_id'])
            create_message(conn, message)


def update_user_names(conn, users):
    '''
    THIS FUNCTION TAKES THE LIST OF USERS AND CHECKS TO SEE IF THEY HAVE CHANGED
    THEIR NAME. IF THEY HAVE CHANGED THEIR DISPLAY NAME, THIS WILL UPDATE IT IN
    THE DATABASE, SO YOUR OUTPUT WILL ALWAYS BE THE CURRENT NAMES.
    '''
    cur = conn.cursor()
    for item in users:
        id = (item['id'],)
        cur.execute('SELECT name FROM users WHERE user_id = ?', id)
        if item['name'] != cur.fetchone()[0]:
            cur.execute('UPDATE users SET name = ? WHERE user_id = ?', (item['name'], item['id']))
            conn.commit()
        conn.commit()


def update_user_message_count(conn):
    '''
    THIS FUNCTION PULLS ALL DISTINCT ID'S FROM THE MESSAGES DB, THEN COUNTS
    HOW MANY TIMES THEY POSTED, AND UPDATES THEIR MESSAGE COUNT.
    '''
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT user_id FROM messages')
    all_ids = cur.fetchall()
    for item in all_ids:
        cur.execute('SELECT COUNT(*) FROM messages WHERE user_id=?', item)
        count = cur.fetchone()[0]
        if count is None:
            count = 0
        cur.execute('UPDATE users SET message_count = ? WHERE user_id = ?', (count, item[0]))
        conn.commit()


async def all_users(conn, client):
    '''
    THIS FUNCTION LOOPS THROUGH THE MESSAGES, AND PULLS A DISTINCT LIST OF USER_ID'S
    AND IF THE USER_ID IS NOT IN THE ACTIVE USERS LIST, IT LOOKS UP THEIR INFO, AND THEN
    ADDS IT TO THE ACTIVE USERS LIST.

    This can only run 100 users per 30 seconds. If you do not care about how many posts are from
    deleted users you can comment out the call to this function on line 331 to speed up this program.
    '''
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT user_id FROM messages')
    all_users_list = cur.fetchall()
    print('There are {} total users.'.format(len(all_users_list)))
    for user in all_users_list:
        cur.execute('SELECT name FROM users WHERE user_id = ?', user)
        if cur.fetchone() is None:
            try:
                unknown_user = await client.get_entity(user[0])
                fullName = str(unknown_user.first_name) + " " + str(unknown_user.last_name)
                if unknown_user.first_name == None:
                    fullName = str(unknown_user.last_name)
                if unknown_user.last_name == None:
                    if unknown_user.first_name == None:
                        fullName = str(unknown_user.username)
                    else:
                        fullName = str(unknown_user.first_name)
                fullName = fullName + ' (Removed)'
                enter_user = (user[0], fullName, 0)
                create_user(conn, enter_user)
            except ValueError:
                cur.execute("INSERT OR IGNORE INTO users(user_id, name) VALUES(1, 'deleted')")
                cur.execute('UPDATE messages SET user_id = 1 WHERE user_id = ?', user)
                conn.commit()
    conn.commit()


def return_list(conn):
    cur = conn.cursor()
    if from_date != '':
        if to_date != '':
            cur.execute(''' SELECT u.name, COUNT(m.user_id) AS cnt_messages
                            FROM users u
                            LEFT JOIN messages m
                            ON m.user_id = u.user_id AND m.date >= ? AND m.date < ?
                            GROUP BY u.user_id, u.name
                            ORDER BY count(m.user_id) DESC''', (from_date, to_date))
        else:
            cur.execute(''' SELECT u.name, COUNT(m.user_id) AS cnt_messages
                            FROM users u
                            LEFT JOIN messages m
                            ON m.user_id = u.user_id AND m.date >= ? AND m.date < '2030-1-1'
                            GROUP BY u.user_id, u.name
                            ORDER BY count(m.user_id) DESC''', (from_date,))
    else:
        cur.execute('SELECT name, message_count FROM users ORDER BY message_count DESC')
    results = cur.fetchall()
    for result in results:
        print(result[0], ' - ', result[1])


def delete_all_messages(conn):
    """
    YOU CAN YOU THIS TO DELETE ALL MESSAGES IN THE MESSAGES TABLE IF YOU WANT.
    THIS FUNCTION IS NOT CALLED IN THE MAIN SCRIPT, BUT IS SIMPLY HERE IF YOU
    WANT TO USE IT.
    Delete all rows in the messages table
    :param conn: Connection to the SQLite database
    :return:
    """
    sql = 'DELETE FROM messages'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()


def main():
    client = telegram_connection()
    conn = create_connection(database)

    with client:
        users = client.loop.run_until_complete(get_all_users(client))

    # COMMENT OUT THE BELOW SECTION (Lines 305 - 326) AFTER THE FIRST TIME YOU RUN THIS SCRIPT.
    # YOU CAN LEAVE IT UNCOMMENTED EVERY TIME YOU RUN IT, IT WILL JUST SLOW DOWN THE SCRIPT.

    sql_create_users_table = '''CREATE TABLE IF NOT EXISTS users (
                                    key integer PRIMARY KEY,
                                    user_id integer UNIQUE,
                                    name text NOT NULL,
                                    message_count integer DEFAULT 0
                                    );'''


    sql_create_messages_table = '''CREATE TABLE IF NOT EXISTS messages (
                                    id integer PRIMARY KEY,
                                    date text NOT NULL,
                                    message text,
                                    user_id integer,
                                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                                    );'''

    if conn is not None:
        create_table(conn, sql_create_messages_table)
        create_table(conn, sql_create_users_table)
    else:
        print('Error | Cannot create the database connection')


    with client:
        messages = client.loop.run_until_complete(get_messages(conn, client))
        client.loop.run_until_complete(all_users(conn, client))

    if len(messages) > 0:
        insert_users(conn, users)
        insert_messages(conn, messages)
    update_user_names(conn, users)
    update_user_message_count(conn)
    return_list(conn)

    conn.close()


if __name__ == '__main__':
    main()
