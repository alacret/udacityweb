import webapp2

months = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']

dmontsh = dict((m[:3],m) for m in months)

def valid_month(month):
    if month:
        month = month.capitalize()[:3]
        return dmontsh.get(month)

def valid_day(day):
    try:
        iday = int(day)
    except Exception:
        return
    else:
        return iday if (iday > 0 and iday <32) else None

def valid_year(year):
    try:
        iyear = int(year)
    except Exception:
        return
    else:
        return iyear if (iyear > 1899 and iyear < 2021) else None

form="""
<form method="post">
    What is your birthday?
    <br>
    <label> Month
    <input name="month" value="%(month)s">
    </label>
    <label> Day
    <input name="day">
    </label>
    <label> Year
    <input name="year">
    </label>
    <div style="color:red">%(error)s</div>
<input type="submit">
</form>
"""

class MainPage(webapp2.RequestHandler):
    def write_form(self,error="",month="",day="",year=""):
        self.response.out.write(form % {"error":error,
                                        "month":month,
                                        "day":day,
                                        "year":year})
    def get(self):
        self.write_form()
    def post(self):
        month = self.request.get('month')
        user_month = valid_month(month)
        day = self.request.get('day')
        user_day = valid_month(day)
        year = self.request.get('year')
        user_year = valid_month(year)

        if not (user_month and user_day and user_year):
            self.write_form("Error",month,day,year)
        else:
            self.response.out.write("Thanks! That's a totally valid day!");

application = webapp2.WSGIApplication([
	('/', MainPage),
], debug=True)
