#!/usr/bin/env python3

from models import db, Activity, Camper, Signup
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask import Flask, make_response, jsonify, request
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
api = Api(app)

db.init_app(app)


@app.route('/')
def home():
    return ''

class Campers(Resource):
    def get(self):
        try:
            campers_data = [camper.to_dict(rules=('-signups',)) for camper in Camper.query.all()]
            return make_response(campers_data, 200)
        except ValueError:
            return make_response({"errors" : ["validation error"]}, 400)

    def post(self):
        try:
            new_camper = Camper(
                name = request.get_json()['name'], 
                age = request.get_json()['age']
            )
            db.session.add(new_camper)
            db.session.commit()
            return make_response(new_camper.to_dict(rules=('-signups',)), 200)
        except ValueError:
            db.session.rollback()
            return make_response({"errors" : ["validation errors"]}, 400)  

api.add_resource(Campers, '/campers')

class CampersById(Resource):
    def get(self, id):
        if camper := db.session.get(Camper, id):
            return camper.to_dict()
        return make_response({"error" : "Camper not found"}, 404)  
    
    def patch(self, id):
        camper_by_id = Camper.query.filter(Camper.id==id).first()
        if not camper_by_id:
            return make_response({"error" : "Camper not found"}, 404) 
        try:
            for k in request.get_json():
                setattr(camper_by_id, k, request.get_json()[k])
            db.session.add(camper_by_id)
            db.session.commit()
            return make_response(camper_by_id.to_dict(rules=('-signups',)), 202)
        except ValueError:
            db.session.rollback()
            return make_response({"errors" : ["validation errors"]}, 400)  
    
api.add_resource(CampersById, '/campers/<int:id>')

class Activities(Resource):
    def get(self):
        try:
            activity_data = [activity.to_dict() for activity in Activity.query.all()]
            return make_response(activity_data, 200)
        except ValueError:
            return make_response({"errors" : ["validation error"]}, 400)
        
api.add_resource(Activities, '/activities')

class ActivitiesById(Resource):
    def delete(self, id):
        activity_by_id = Activity.query.filter(Activity.id==id).first()
        if activity_by_id:
            db.session.delete(activity_by_id)
            db.session.commit()
            return make_response({}, 204)
        else:
            return make_response({"error" : "Activity not found"}, 404)

api.add_resource(ActivitiesById, '/activities/<int:id>')

class Signups(Resource):
    def post(self):
        try:
            new_signup = Signup(camper_id=request.get_json()['camper_id'], activity_id=request.get_json()['activity_id'], time=request.get_json()['time'])
            db.session.add(new_signup)
            db.session.commit()
            return make_response(new_signup.to_dict(), 201)
        except ValueError:
            return make_response({"errors" : ["validation errors"]}, 400)
        
api.add_resource(Signups, '/signups')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
