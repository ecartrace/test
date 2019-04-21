import os
import psycopg2
import psycopg2.extras
import urllib.parse


class ReservationsDB:

    def __init__(self):
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

        self.connection = psycopg2.connect(
            cursor_factory=psycopg2.extras.RealDictCursor,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        self.cursor = self.connection.cursor()
    
    def __del__(self):
        self.connection.close()

    def createReservationsTable(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS reservations (id serial PRIMARY KEY, first_name VARCHAR(25), last_name VARCHAR(25), phone VARCHAR(12), email VARCHAR(25), day VARCHAR(10), time VARCHAR(10))")
        self.connection.commit()

    def createCustomer(self, first_name, last_name, phone, email, day, time):
        sql = "INSERT INTO reservations (first_name, last_name, phone, email, day, time) VALUES (%s, %s, %s, %s, %s, %s)"
        self.cursor.execute(sql, [first_name, last_name, phone, email, day, time])
        self.connection.commit()
        return

    def getAllCustomers(self):
        self.cursor.execute("SELECT * FROM reservations")
        return self.cursor.fetchall()

    def getCustomer(self, id):
        sql = "SELECT * FROM reservations WHERE id = %s"
        self.cursor.execute((sql), [id])
        return self.cursor.fetchone()

    def deleteCustomer(self, id):
        sql = "DELETE FROM reservations WHERE id = %s"
        self.cursor.execute((sql), [id])
        self.connection.commit()

    def updateCustomer(self, id, first_name, last_name, phone, email, day, time, id2):
        sql = ("UPDATE reservations SET id = %s, first_name = %s, last_name = %s, phone = %s, email = %s, day = %s, time = %s WHERE id = %s")
        self.cursor.execute(sql, [id, first_name, last_name, phone, email, day, time, id2])
        self.connection.commit()
        return

class MembersDB:

    def __init__(self):
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

        self.connection = psycopg2.connect(
            cursor_factory=psycopg2.extras.RealDictCursor,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        self.cursor = self.connection.cursor()
    
    def __del__(self):
        self.connection.close()

    def createMembersTable(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS members (id serial PRIMARY KEY, fname VARCHAR(25), lname VARCHAR(25), email_address VARCHAR(25), password VARCHAR(255))")
        self.connection.commit()

    def createMember(self, fname, lname, email_address, password):
        sql = "INSERT INTO members (fname, lname, email_address, password) VALUES (%s, %s, %s, %s)"
        self.cursor.execute(sql, [fname, lname, email_address, password])
        self.connection.commit()
        return

    def getMember(self, email):
        sql = "SELECT * FROM members WHERE email_address = %s"
        self.cursor.execute((sql), [email])
        return self.cursor.fetchone()





