import os
import webapp2

import jinja2

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("")

class FizzBuzz(webapp2.RequestHandler):
    def get(self):
        self.write_form()


application = webapp2.WSGIApplication([
	('/', MainPage),
    ('/fizzbuzz', FizzBuzz),
], debug=True)
