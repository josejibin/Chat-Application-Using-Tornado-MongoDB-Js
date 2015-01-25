
import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import mail
import pymongo

from tornado.options import define, options

define("port", default=9090, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
            (r'/login', LoginHandler),
            (r'/logout', LogoutHandler),
            (r'/signup', SignUpHandler),
           
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)



class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = {}
    cache = []
    cache_size = 200
    print "waiters"+str(waiters)
    print "cache"+str(cache)+"  len=="+str(cache_size)


    def check_origin(self, origin):
        return True

    def get_compression_options(self):
        # Non-None enables compression with default options.
        
        return {}

    def open(self):
        #ChatSocketHandler.waiters[str(id(self))] = self
        #self.clear_cookie("user")
        #print "on opening",
        #print type(self),
        #print id(self)
        
        user_json = self.get_secure_cookie("user")
        if user_json:
            print tornado.escape.json_decode(user_json)
        else:
            print "Noooooooooooooooooooooooooooo"
        ChatSocketHandler.waiters[tornado.escape.json_decode(user_json)] = self
        #ChatSocketHandler.waiters.add(self)

    def on_close(self):
        user_json = self.get_secure_cookie("user")
       
        
        del ChatSocketHandler.waiters[tornado.escape.json_decode(user_json)]
        #print "on closing",
        #print type(self),
        #print id(self)

        #ChatSocketHandler.waiters.remove(self)

    @classmethod
    def update_cache(cls, chat):
        #print "id of users in first",
        #print id(cls)
        #print "new cahat is ",
        #print chat
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
       
        logging.info("sending message to %d waiters", len(cls.waiters))
        #print cls.waiters.keys()
        for waiter in cls.waiters:
            try:
         #       print "needed connection"
          #      print cls.waiters['jibin']
                cls.waiters[waiter].write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
       
        #print "id of user messaged",
        #print id(self)
        print   "MMMMMMMMMMMMMMMMMMMMMMMMMMM",
        print message
        #print id(ChatSocketHandler.ws_connection)
        user_json = self.get_secure_cookie("user")
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        chat = {
            "id": str(uuid.uuid4()),
            "body": parsed["body"],
           # "user" : str(id(self))
             "user" : tornado.escape.json_decode(user_json)
            }
        chat["html"] = tornado.escape.to_basestring(
            self.render_string("message.html", message=chat))
        #print chat
        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)






class BaseHandler(tornado.web.RequestHandler):

    

    def get_login_url(self):
      return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        print "in BASEEEEEEEEEEEEEEEEE"
        print user_json, self
        if user_json:
           return tornado.escape.json_decode(user_json)
        else:
           return None






class LoginHandler(BaseHandler):

    def get(self):
        self.render("login_new.html", next=self.get_argument("next","/"))

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")  
       # auth = (username == 'jibin' and password == "j")
        #if auth:
        self.set_current_user(username)

        self.redirect(self.get_argument("next", u"/"))
        #else:
         #   error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect.")
#            self.redirect(u"/login" + error_msg)

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")

class LogoutHandler(BaseHandler):
    print "in log out"

    def post(self):
        print "ffffffffffffffffffffffffffffff"
        self.clear_cookie("user")
        self.redirect(u"/login")
    
    get = post

class SignUpHandler(tornado.websocket.WebSocketHandler):
    def get(self):
        self.render("signup.html")
    def post(self):
        username = self.get_argument("username", "")
        email = self.get_argument("email", "")
        password = self.get_argument("password", "")  

        client = pymongo.Connection("localhost", 27017)
        db = client.test_database
        collection = db.test_collection
        user = { "Username": username ,"email": email, "password": password }
        users = db.users
        user_id = users.insert(user)

        #print username,email,password
       # mail.send_mail_to('jibin.jacob13@gmail.com')
        print user_id
        print db.collection_names()
        for post in users.find():
           print post
        self.finish("<html><body>A verfication mail is sent to your mail <a href=email ></body></html>")

      
      

    
        

class MainHandler(BaseHandler):
    def get(self):
        #{'name':'jibin'},{'name''mary'},{'name''kevin'}
        if self.get_current_user():

            # current_user=self.get_current_user()
            print self.get_current_user()
           #self.render("fb.html", messages=ChatSocketHandler.cache, users=['three','two','one' ] )
            self.render("ui_home.html", messages=ChatSocketHandler.cache)
        else:
            #self.get_login_url()
            self.redirect(u"/login")
def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
