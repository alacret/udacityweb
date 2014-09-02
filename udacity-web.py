import os,json,jsonU, webapp2, re, jinja2, hashlib, time, logging as LOG
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

def is_session(request):
    username_cookie = request.cookies.get("username")
    if not username_cookie:
        return False
    else:
        t = username_cookie.split("|")
        if len(t) > 1:
            hash = hashlib.md5(t[0]).hexdigest()
            if hash == t[1]:
                return t[0]

class User(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()

class Page(db.Model):
    name = db.StringProperty()
    html = db.TextProperty()


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
            self.redirect("/")
        else:
            self.response.out.write(jinja_render("login.html",error="Invalid login"))

class LogoutPage(webapp2.RequestHandler):
    def get(self):
        self.response.delete_cookie("username", path='/')
        self.redirect("/signup")

class WikiPage(webapp2.RequestHandler):
    def get(self,page_name):
        a = Page.all().filter("name =", page_name)
        print "Page:" + page_name
        if a.count() == 0:
            if is_session(self.request):
                self.redirect("/_edit"+page_name)
            else:
                self.redirect("/signup")
        else:
            self.response.out.write(jinja_render("view.html",html=a[0].html, username=is_session(self.request),page_name = page_name))

class EditPage(webapp2.RequestHandler):
    def get(self,page_name):
        if not is_session(self.request):
            self.redirect("/signup")
            return

        p = Page.all().filter("name =", page_name)

        if p.count() == 0:
            p = Page(name=page_name,html="")
            p.put()
            time.sleep(1)
        else:
            p = p[0]

        self.response.out.write(jinja_render("edit.html",html=p.html, page_name = page_name))
    def post(self,page_name):
        if not is_session(self.request):
            self.redirect("/signup")
            return

        html = self.request.get('html')
        p = Page.all().filter("name =",page_name).get()
        if p is None:
            p = Page(name = page_name)
        p.html = html
        p.put()
        time.sleep(1)
        self.redirect(page_name)

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

application = webapp2.WSGIApplication([
    ('/signup', SignUpPage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),
    ('/_edit' + PAGE_RE, EditPage),
    (PAGE_RE, WikiPage),
], debug=True)