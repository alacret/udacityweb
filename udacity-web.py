import os,json,jsonU, webapp2, re, jinja2, hashlib, time
from google.appengine.ext import db

jinja = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return USER_RE.match(username)
PASS_RE = re.compile(r"^.{3,20}$")
def valid_pass(val):
    return PASS_RE.match(val)
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(val):
    return EMAIL_RE.match(val)
def duplicate_username(username):
    r = User.all().filter("username =", username)
    if r.count() > 0 :
        return True
    return False
def valid_credentiales(username,password):
    r = User.all().filter("username =", username).filter("password =", password)
    if r.count() > 0 :
        return True
    return False

sign_up_form="""
<!doctype html>
<html>
<body>
<h2>Signup</h2>
    <form method="post">
      <table>
        <tr>
          <td class="label">
            Username
          </td>
          <td>
            <input type="text" name="username" value="%(username)s">
          </td>
          <td class="error">%(username_error)s</td>
        </tr>
        <tr>
          <td class="label">
            Password
          </td>
          <td>
            <input type="password" name="password" value="">
          </td>
          <td class="error">%(password_error)s</td>
        </tr>
        <tr>
          <td class="label">
            Verify Password
          </td>
          <td>
            <input type="password" name="verify" value="">
          </td>
          <td class="error"></td>
        </tr>

        <tr>
          <td class="label">
            Email (optional)
          </td>
          <td>
            <input type="text" name="email" value="%(email)s">
          </td>
          <td class="error">%(email_error)s</td>
        </tr>
      </table>
      <input type="submit">
    </form>
</body>
</html>
"""

def jinja_render(template, **params):
    t = jinja.get_template(template)
    return t.render(params)

class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()

class Post(db.Model):
    subject = db.StringProperty(required =True)
    content = db.TextProperty(required =True)
    created = db.DateTimeProperty(auto_now_add=True)

CACHE = {}
TIMES = {}
home_cache_key = "home"
time_when_query = time.time()

def get_post(id):
    if not str(id) in CACHE:
        CACHE[str(id)] = Post.get_by_id(long(id))
        TIMES[str(id)] = time.time()
    return CACHE[str(id)]

def get_posts(update=False):
    if not home_cache_key in CACHE or update:
        print "making query"
        posts = db.GqlQuery("select * from Post order by created desc")
        CACHE[home_cache_key] = list(posts)
        global time_when_query
        time_when_query = time.time()
    return CACHE[home_cache_key]

class PostsHandler(webapp2.RequestHandler):
    def get(self):
        posts = get_posts()
        time_since = int(time.time() - time_when_query)
        print time_since
        self.response.out.write(jinja_render("home.html",posts=posts, time=time_since))

class JSONPostsHandler(webapp2.RequestHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc")
        posts = list(posts)
        self.response.headers["Content-type"]="application/json"
        self.response.out.write(jsonU.encode(posts))


class NewPostHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(jinja_render("newpost.html"))
    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            p = Post(subject = subject, content = content)
            p.put()
            id = p.key().id()
            get_posts(update = True)
            self.redirect("/post/" + str(id))
        else:
            self.response.out.write(jinja_render("newpost.html",subject=subject,content=content))

class PostHandler(webapp2.RequestHandler):
    def get(self,id):
        post = get_post(long(id))
        time_since = int(time.time() - TIMES[str(id)])
        if not post:
            self.redirect("/")

        self.response.out.write(jinja_render("post.html",post=post,time=time_since))

class JSONPostHandler(webapp2.RequestHandler):
    def get(self,id):
        post = Post.get_by_id(long(id))

        if not post:
            self.redirect("/")
        self.response.headers["Content-type"]="application/json"
        self.response.out.write(jsonU.encode(post))

class SignUpPage(webapp2.RequestHandler):
    def write_form(self,username="",username_error="",password_error="",email="",email_error=""):
        self.response.out.write(sign_up_form % {"username":username,
                                                "username_error":username_error,
                                                "password_error":password_error,
                                                "email":email,
                                                "email_error":email_error})
    def get(self):
        self.write_form()
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        username_error = ""
        password_error = ""
        email_error = ""

        if not valid_username(username):
            username_error = "Not a valid username"

        if duplicate_username(username):
            username_error = "Username already in database"

        if password:
            if not valid_pass(password):
                password_error = "Not a valid password"
            else:
                if password != verify:
                    password_error = "Password missmatch"
        else:
            password_error = "Must enter a password"

        if email:
            if not valid_email(email):
                email_error = "Not a valid email"

        if (username_error == "" and password_error == "" and email_error == ""):
            user = User(username = username,password=password)
            user.put()
            digest = hashlib.md5(username).hexdigest()
            cookie = str('username='+username+'|'+digest+'; Path=/')
            self.response.headers.add_header('Set-Cookie', cookie)
            self.redirect("/welcome")
        else:
            self.write_form(username, username_error, password_error, email, email_error)

class WelcomePage(webapp2.RequestHandler):
    def get(self):
        username_cookie = self.request.cookies.get("username")
        if not username_cookie:
            self.redirect("/signup")
        else:
            t = username_cookie.split("|")
            print username_cookie
            if len(t) > 1:
                hash = hashlib.md5(t[0]).hexdigest()
                if hash == t[1]:
                    self.response.out.write(jinja_render("thanks.html",username = t[0]))
                else:
                    self.redirect("/signup")
            else:
                self.redirect("/signup")

class LoginPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(jinja_render("login.html"))
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        if username and password and valid_credentiales(username,password):
            digest = hashlib.md5(username).hexdigest()
            cookie = str('username='+username+'|'+digest+'; Path=/')
            self.response.headers.add_header('Set-Cookie', cookie)
            self.redirect("/welcome")
        else:
            self.response.out.write(jinja_render("login.html",error="Invalid login"))

class LogoutPage(webapp2.RequestHandler):
    def get(self):
        self.response.delete_cookie("username", path='/')
        self.redirect("/signup")

class FlushPage(webapp2.RequestHandler):
    def get(self):
        CACHE.clear()
        self.redirect("/")

application = webapp2.WSGIApplication([
	('/', PostsHandler),
    ('/blog', PostsHandler),
    ('/.json', JSONPostsHandler),
    ('/newpost', NewPostHandler),
    (r'/post/(\d+)', PostHandler),
    (r'/post/(\d+).json', JSONPostHandler),
    ('/signup', SignUpPage),
    ('/welcome', WelcomePage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),
    ('/flush', FlushPage),
], debug=True)
