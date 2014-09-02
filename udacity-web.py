import os,json,jsonU
import webapp2
from google.appengine.ext import db
import jinja2

jinja = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

def jinja_render(template, **params):
    t = jinja.get_template(template)
    return t.render(params)

class Post(db.Model):
    subject = db.StringProperty(required =True)
    content = db.TextProperty(required =True)
    created = db.DateTimeProperty(auto_now_add=True)

class PostsHandler(webapp2.RequestHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc")
        self.response.out.write(jinja_render("home.html",posts=posts))

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
            self.redirect("/post/" + str(id))
        else:
            self.response.out.write(jinja_render("newpost.html",subject=subject,content=content))

class PostHandler(webapp2.RequestHandler):
    def get(self,id):
        post = Post.get_by_id(long(id))

        if not post:
            self.redirect("/")

        self.response.out.write(jinja_render("post.html",post=post))

class JSONPostHandler(webapp2.RequestHandler):
    def get(self,id):
        post = Post.get_by_id(long(id))

        if not post:
            self.redirect("/")
        self.response.headers["Content-type"]="application/json"
        self.response.out.write(jsonU.encode(post))

application = webapp2.WSGIApplication([
	('/', PostsHandler),
    ('/.json', JSONPostsHandler),
    ('/newpost', NewPostHandler),
    (r'/post/(\d+)', PostHandler),
    (r'/post/(\d+).json', JSONPostHandler),
], debug=True)
