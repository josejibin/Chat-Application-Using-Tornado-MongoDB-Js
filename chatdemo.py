
import logging
import os.path
import uuid
import mail
import pymongo
from bson.objectid import ObjectId

import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
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
            (r'/confirmation/([^/]+)', ConfirmationHandler),
            
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)



class ChatSocketHandler(tornado.websocket.WebSocketHandler):

    waiters = []
    cache = []
    cache_size = 200
  
    def check_origin(self, origin):
        return True

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        
        user_json = self.get_secure_cookie("user")
        new_user = {}
        new_user['id'] = id(self)
        new_user['name'] = tornado.escape.json_decode(user_json)
        new_user[tornado.escape.json_decode(user_json)] = self
        ChatSocketHandler.waiters.append(new_user)

        print ChatSocketHandler.waiters

    def on_close(self):
        """ when websocket close, remove connection from waiters"""

        user_json = self.get_secure_cookie("user")
        #ChatSocketHandler.waiters[tornado.escape.json_decode(user_json)]
        ChatSocketHandler.waiters = [ d for d in ChatSocketHandler.waiters if d.get('id') != id(self)]
       

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    def on_message(self, message):
        user_json = self.get_secure_cookie("user")
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        chat = {
            "id": str(uuid.uuid4()),
            "body": parsed["body"],
            "user" : tornado.escape.json_decode(user_json)
            }
        
        logined_users = [v for d in ChatSocketHandler.waiters for k,v in d.iteritems() if k=='name']
        print logined_users,
        chat['logined_users'] = str(logined_users)
        
        ChatSocketHandler.update_cache(chat)
        #ChatSocketHandler.send_updates(chat)

        #sending message to all socket connections
        logging.info("sending message to %d waiters", len(ChatSocketHandler.waiters))
        for waiter in ChatSocketHandler.waiters:
            try:
            	current_user =  waiter['name'] 
            	
            	chat['current_user'] = current_user
            	chat["html"] = tornado.escape.to_basestring(
                  self.render_string("message.html", message=chat))
            	
            	
            	waiter[current_user].write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)


class BaseHandler(tornado.web.RequestHandler):

    def get_login_url(self):
      return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
       
        if user_json:
           return tornado.escape.json_decode(user_json)
        else:
           return None

class LoginHandler(BaseHandler):

    def get(self):
	self.render("login_new.html", next=self.get_argument("next","/"))
	client = pymongo.Connection("localhost", 27017)
	db = client.chat_database
	print db.collection_names()

    def post(self):
	username = self.get_argument("username", "")
	password = self.get_argument("password", "")  
	
	client = pymongo.Connection("localhost", 27017)
	db = client.chat_database

	try:
	    if password == db.users.find_one({"Username": username})['password']:
    		 self.set_current_user(username)
		 self.redirect(self.get_argument("next", u"/"))
	except:
 		error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect.")
		self.redirect(u"/login" + error_msg)

    def set_current_user(self, user):
	if user:
		self.set_secure_cookie("user", tornado.escape.json_encode(user))
	else:
		self.clear_cookie("user")

class LogoutHandler(BaseHandler):
    
    def post(self):
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
        db = client.chat_database
        collection = db.test_collection
        user = { "Username": username ,"email": email, "password": password ,'conf_status' : 0}
        users = db.users
        user_id = users.insert(user)

        #print username,email,password
        obj_id = db.users.find_one({"Username": username})['_id']

        #defaultly set to send mailt to my mail for testing
        mail.send_mail_to('jibin.jacob13@gmail.com',obj_id)
        
        #to see saved usernames and passwords
        for post in users.find():
           print post
        client.close()
        self.finish("<html><body>A verfication mail is sent to your mail <a href=email ></body></html>")


class ConfirmationHandler(tornado.websocket.WebSocketHandler):
   ''' make confirmation status to 1 '''

   def get(self, obj_id):
	user = {}
	client = pymongo.Connection("localhost", 27017)
	db = client.chat_database
	users = db.users
	user['conf_status'] = 1
	db.users.update({'_id': ObjectId(obj_id)}, {"$set": user}, upsert=False)
	self.redirect(u"/login")

      
class MainHandler(BaseHandler):

    def get(self):
        if self.get_current_user():
            self.render("ui_home.html", messages=ChatSocketHandler.cache)
        else:
            self.redirect(u"/login")


def main():
    print "\n\tsever starts default at localhost:9090"
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
