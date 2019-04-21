from http.server import BaseHTTPRequestHandler, HTTPServer
from http import cookies
from urllib.parse import parse_qs
import json
import sys
from passlib.hash import bcrypt
from reservations_db import ReservationsDB
from reservations_db import MembersDB
from session_store import SessionStore

gSessionStore = SessionStore()

class MyRequestHandler(BaseHTTPRequestHandler):
    
    def end_headers(self):
        self.send_cookie()
        self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
        self.send_header("Access-Control-Allow-Credentials", "true")
        BaseHTTPRequestHandler.end_headers(self)
        

    def load_cookie(self):
        if "Cookie" in self.headers:
            self.cookie = cookies.SimpleCookie(self.headers["Cookie"])
        else:
            self.cookie = cookies.SimpleCookie()
    
    #overloaded end_headers
    def send_cookie(self):
        for morsel in self.cookie.values():
            self.send_header("Set-Cookie", morsel.OutputString())

    def load_session(self):
        self.load_cookie()
        if "sessionId" in self.cookie:
            sessionId = self.cookie["sessionId"].value
            self.session = gSessionStore.getSessionData(sessionId)
            if self.session == None:
                sessionId = gSessionStore.createSession()
                self.session = gSessionStore.getSessionData(sessionId)
                self.cookie["sessionId"] = sessionId
        else:
            sessionId = gSessionStore.createSession()
            self.session = gSessionStore.getSessionData(sessionId)
            self.cookie["sessionId"] = sessionId
        return

    def isLoggedIn(self):
        if "userId" in self.session:
            print("true")
            return True
        else:
            print("false")
            return False

    def handleCustomerList(self):
        if not self.isLoggedIn():
            self.send_response(401)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")

        self.end_headers()

        #local instance - destroyed at end of request
        db = ReservationsDB()
        customers = db.getAllCustomers()
        #write data back to client
        self.wfile.write(bytes(json.dumps(customers), "utf-8"))

    def handleCustomerCreate(self):
        if not self.isLoggedIn():
            self.send_response(401)
            self.end_headers()
            return

        length = self.headers["Content-length"]
        body = self.rfile.read(int(length)).decode("utf-8")
        print("the text body: ", body)
        parsed_body = parse_qs(body)
        print("the parsed body: ", parsed_body)

        first_name = parsed_body["first_name"][0]
        last_name = parsed_body["last_name"][0]
        phone = parsed_body["phone"][0]
        email = parsed_body["email"][0]
        day = parsed_body["day"][0]
        time = parsed_body["time"][0]

        db = ReservationsDB()
        db.createCustomer(first_name, last_name, phone, email, day, time)

        self.send_response(201)
        self.end_headers()

    def handleCustomerRetrieve(self, id):
        if not self.isLoggedIn():
            self.send_response(401)
            self.end_headers()
            return

        db = ReservationsDB()
        customer = db.getCustomer(id)

        if customer == None:
            self.handleNotFound()
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(customer), "utf-8"))

    def handleCustomerDelete(self, id):
        if not self.isLoggedIn():
            self.send_response(401)
            self.end_headers()
            return

        db = ReservationsDB()
        customer = db.getCustomer(id)

        if customer == None:
            self.handleNotFound()       
        else:
            db.deleteCustomer(id)
            self.send_response(200)
            self.send_header("Content-type", "application/json")        
            self.end_headers()

    def handleCustomerUpdate(self, id):
        if not self.isLoggedIn():
            self.send_response(401)
            self.end_headers()
            return

        db = ReservationsDB()
        customer = db.getCustomer(id)

        if customer == None:
            self.handleNotFound()       
        else:
            length = self.headers["Content-length"]
            body = self.rfile.read(int(length)).decode("utf-8")
            print("the text body: ", body)
            parsed_body = parse_qs(body)
            print("the parsed body: ", parsed_body)

            #save the customer
            id = parsed_body["id"][0]
            print('id is: ', id)
            first_name = parsed_body["first_name"][0]
            print('first name is: ', first_name)
            last_name = parsed_body["last_name"][0]
            phone = parsed_body["phone"][0]
            email = parsed_body["email"][0]
            day = parsed_body["day"][0]
            time = parsed_body["time"][0]
            id2 = parsed_body["id"][0]
            #send values to database
            db = ReservationsDB()
            db.updateCustomer(id, first_name, last_name, phone, email, day, time, id2)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

    def handleMemberCreate(self):
        length = self.headers["Content-length"]
        body = self.rfile.read(int(length)).decode("utf-8")
        print("the text body: ", body)
        parsed_body = parse_qs(body)
        print("the parsed body: ", parsed_body)

        fname = parsed_body["fname"][0]
        lname = parsed_body["lname"][0]
        email_address = parsed_body["email_address"][0]
        password = parsed_body["password"][0]

        enc_pass = bcrypt.hash(password)
        password = enc_pass

        db = MembersDB()
        email_check = db.getMember(email_address)
        if email_check:
            print("already registered")
            self.send_response(422)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("422: already registered", "utf-8"))
            return
        db.createMember(fname, lname, email_address, password)

        self.send_response(201)
        self.end_headers()

    def handleMemberVerification(self):
        length = self.headers["Content-length"]
        body = self.rfile.read(int(length)).decode("utf-8")
        print("the text body: ", body)
        parsed_body = parse_qs(body)
        print("the parsed body: ", parsed_body)

        email = parsed_body["email_address"][0]
        password = parsed_body["password"][0]

        db = MembersDB()
        member = db.getMember(email)

        if member == None:
            self.handle401()
        else:
            if bcrypt.verify(password, member["password"]):
                print('success')
                self.session["userId"] = member["id"]
                self.send_response(201)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(member), "utf-8"))
            else:
                self.send_response(422)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(bytes("422: incorrect password", "utf-8"))
                return         

    def handleNotFound(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Not found", "utf-8"))
    
    def handle401(self):
        self.send_response(401)
        self.end_headers()
        self.wfile.write(bytes("401: not logged in", "utf-8"))

    def do_OPTIONS(self):
        self.load_session()
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Acess-Control-Origin-Headers", "Content-type")
        self.end_headers()
   
    def do_GET(self):
        self.load_session()
        parts = self.path.split('/')[1:]
        collection = parts[0]
        if len(parts) > 1:
            id = parts[1]
        else:
            id = None

        if collection == "reservations":
            if id == None:
                self.handleCustomerList()
            else:
                self.handleCustomerRetrieve(id)
        else:
            self.handleNotFound()

    def do_POST(self):
        self.load_session()
        if self.path == "/reservations":
            self.handleCustomerCreate()
        elif self.path == "/members":
            self.handleMemberCreate()
        elif self.path == "/sessions":
            self.handleMemberVerification()
        else:
            self.handleNotFound()

    def do_DELETE(self):
        self.load_session()
        parts = self.path.split('/')[1:]
        collection = parts[0]

        if len(parts) > 1:
            id = parts[1]
        else:
            id = None
        
        if collection == "reservations":
            if id == None:
                self.handleNotFound()
            else:
                self.handleCustomerDelete(id)
        else:
            self.handleNotFound()

    def do_PUT(self):
        self.load_session()
        parts = self.path.split('/')[1:]
        collection = parts[0]

        if len(parts) > 1:
            id = parts[1]
        else:
            id = None

        if collection == "reservations":
            if id == None:
                self.handleNotFound()
            else:
                self.handleCustomerUpdate(id)
        else:
            self.handleNotFound()
     

def run():

    rdb = ReservationsDB()
    rdb.createReservationsTable()
    rdb = None

    mdb = MembersDB()
    mdb.createMembersTable()
    mdb = None

    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    listen = ("0.0.0.0", port)
    server = HTTPServer(listen, MyRequestHandler)

    print("Listening on ", "{}:{}".format(*listen))
    server.serve_forever()

run()