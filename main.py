from google.appengine.ext import ndb
import webapp2
import json
import logging
import datetime
import time
from datetime import date
from datetime import time
from google.appengine.api import users

#taken from stackOverflow @ https://stackoverflow.com/questions/35869985/datetime-datetime-is-not-json-serializable
def datetime_handler(x):
    if isinstance(x, datetime.date):
        return x.isoformat()
    elif isinstance(x, datetime.time):
        return x.strftime('%I:%M%p')
    # raise TypeError("Unknown type")


class Trip(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty(required=True)
    destination = ndb.StringProperty(required=True)
    start_date = ndb.DateProperty(required=True)
    end_date = ndb.DateProperty()
    purpose = ndb.StringProperty()
    user_id = ndb.StringProperty(required=True)

class Activity(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty(required=True)
    date = ndb.DateProperty()
    start_time = ndb.TimeProperty()
    end_time = ndb.TimeProperty()
    trip = ndb.StringProperty(required=True)
    user_id = ndb.StringProperty(required=True)

class TripHandler(webapp2.RequestHandler):
    def post(self):
        trip_data = json.loads(self.request.body)
        if ('name' not in trip_data or 'destination' not in trip_data or 'start_date' not in trip_data):
            self.response.set_status(500)
            self.response.write("name, destination, start_date required.  please see documentation")
        else:
            new_trip = Trip(name = trip_data['name'], destination = trip_data['destination'], start_date = datetime.datetime.strptime(trip_data['start_date'], '%m/%d/%Y').date(), end_date = datetime.datetime.strptime(trip_data['end_date'], '%m/%d/%Y').date(), purpose = trip_data['purpose'], user_id = users.get_current_user().user_id())
            new_trip.put()
            new_trip.id = new_trip.key.urlsafe()
            new_trip.put()
            self.response.write(json.dumps(new_trip.to_dict(), default=datetime_handler))

    def get(self, id=None):
        if (id):
            trip = ndb.Key(urlsafe=id).get()
            if (trip == None):
                self.response.set_status(404)
                self.response.write('Trip with that ID does not exist')
            elif (trip.user_id != users.get_current_user().user_id()):
                self.response.set_status(403)
                self.response.write('You are not authorized to acccess that resource')
            else:
                self.response.write(json.dumps(trip.to_dict(), default=datetime_handler))
        else:
            trips = Trip.query(Trip.user_id == users.get_current_user().user_id()).fetch(30)
            output = []
            for trip in trips:
                output.append(json.dumps(trip.to_dict(), default=datetime_handler))
            self.response.write(json.dumps(output))

    def delete(self, id):
        trip = ndb.Key(urlsafe=id).get()
        if (trip == None):
            self.response.set_status(404)
            self.response.write('Trip does not exist')
        elif (trip.user_id != users.get_current_user().user_id()):
            self.response.set_status(403)
            self.response.write('You are not authorized to acccess that resource')
        else:
            activities = Activity.query(Activity.trip == trip.id).fetch(30)
            for activity in activities:
                activity.key.delete()
            ndb.Key(urlsafe=id).delete()
    
    def patch(self, id):
        data = json.loads(self.request.body)
        trip = ndb.Key(urlsafe=id).get()
        if (trip != None):
            if (trip.user_id == users.get_current_user().user_id()):
                if ('name' in data):
                    trip.name = data['name']
                if ('destination' in data):
                    trip.destination = data['destination']
                if ('start_date' in data):
                    trip.start_date = datetime.datetime.strptime(data['start_date'], '%m/%d/%Y').date()
                if ('end_date' in data):
                    trip.end_date = datetime.datetime.strptime(data['end_date'], '%m/%d/%Y').date()
                if ('purpose' in data):
                    trip.purpose = data['purpose']
                trip.put()
                self.response.write(json.dumps(trip.to_dict(), default=datetime_handler))
            else:
                self.response.set_status(403)
                self.response.write('You are not authorized to acccess that resource')
        else:
            self.response.set_status(404)
            self.response.write("trip not found")

class ActivityTripHandler(webapp2.RequestHandler):
    def post(self, id):
        data = json.loads(self.request.body)
        if ('name' not in data):
            self.response.set_status(500)
            self.response.write("name required.  please see documentation")
        else:
            trip = Trip.query(Trip.id == id).get()
            if (trip == None):
                self.response.set_status(404)
                self.response.write("trip not found")
            elif (trip.user_id != users.get_current_user().user_id()):
                self.response.set_status(403)
                self.response.write('You are not authorized to acccess that resource')
            else:
                startTime = datetime.datetime.strptime(data['start_time'], '%I:%M%p').time()
                endTime = datetime.datetime.strptime(data['end_time'], '%I:%M%p').time()
                new_act = Activity(name = data['name'], date = datetime.datetime.strptime(data['date'], '%m/%d/%Y').date(), start_time = startTime, end_time = endTime, trip = id, user_id = users.get_current_user().user_id())
                new_act.put()
                new_act.id = new_act.key.urlsafe()
                new_act.put()
                self.response.write(json.dumps(new_act.to_dict(), default=datetime_handler))

    def get(self, id):
        trip = ndb.Key(urlsafe=id).get()
        if (trip == None):
            self.response.set_status(404)
            self.response.write('Trip with that ID does not exist')
        elif (trip.user_id != users.get_current_user().user_id()):
            self.response.set_status(403)
            self.response.write('You are not authorized to acccess that resource')
        else:
            activities = Activity.query(Activity.trip == id).fetch(30)
            output = []
            for act in activities:
                output.append(json.dumps(act.to_dict(), default=datetime_handler))
            self.response.write(json.dumps(output))

class ActivityHandler(webapp2.RequestHandler):
    def get(self, id):
        activity = ndb.Key(urlsafe=id).get()
        if (activity == None):
            self.response.set_status(404)
            self.response.write("No activity found with that ID")
        elif (activity.user_id != users.get_current_user().user_id()):
            self.response.set_status(403)
            self.response.write('You are not authorized to acccess that resource')
        else:
            self.response.write(json.dumps(activity.to_dict(), default=datetime_handler))
    
    def patch(self, id):
        data = json.loads(self.request.body)
        activity = ndb.Key(urlsafe=id).get()
        if (activity == None):
            self.reponse.set_status(404)
            self.response.write("No activity found with that ID")
        elif (activity.user_id != users.get_current_user().user_id()):
            self.response.set_status(403)
            self.response.write('You are not authorized to acccess that resource')
        else:
            if ('name' in data):
                activity.name = data['name']
            if ('date' in data):
                activity.date = datetime.datetime.strptime(data['date'], '%m/%d/%Y').date()
            if ('start_time' in data):
                activity.start_time = datetime.datetime.strptime(data['start_time'], '%I:%M%p').time()
            if ('end_time' in data):
                activity.end_time = datetime.datetime.strptime(data['end_time'], '%I:%M%p').time()
            activity.put()
            self.response.write(json.dumps(activity.to_dict(), default=datetime_handler))

    def delete(self, id):
        activity = ndb.Key(urlsafe=id).get()
        if (activity == None):
            self.response.set_status(404)
            self.response.write('Activity does not exist')
        elif (activity.user_id != users.get_current_user().user_id()):
            self.response.set_status(403)
            self.response.write('You are not authorized to acccess that resource')
        else:
            ndb.Key(urlsafe=id).delete()
            



class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write('Mobile And Cloud Development Final Project Main Page')

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/trips', TripHandler),
    ('/trips/(.*)/activities', ActivityTripHandler),
    ('/trips/(.*)', TripHandler),
    ('/activities/(.*)', ActivityHandler),
], debug=True)