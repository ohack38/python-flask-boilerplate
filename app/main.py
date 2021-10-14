from datetime import date
import os, requests, json
from flask import Flask, jsonify, request
from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy

# Load variables from .env
load_dotenv()


# Create Flask instance
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

auth_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MTUyMDU3MGU2NjI4ZjUxZDY5ODg4MGUiLCJlbWFpbCI6InRvbW15c2hlbGJ5QGRvZS5jb20iLCJpYXQiOjE2MzQyMDM2OTUsImV4cCI6MTYzNDI5MDA5NX0.4G9uwdmEICXX8Wa6GYC9fLBy9Ud19qs9jo4IabezpaM'

class Services(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(255), unique=True, nullable=False)
    
class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(255), nullable=False)
    cabin_id = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime(), default=db.func.now())


# Default route to /
@app.route("/", methods = ['GET', 'POST'])
def index():
    return jsonify("/cabins, /orders, /services")

@app.route("/services", methods = ['GET', 'POST'])
def services():
    ret = []
    if request.method == 'GET':
        for service in Services.query.all():
            ret.append({'id': service.id, 'service': service.service})
    
    if request.method == 'POST':
        try:
            body = request.get_json()
            new_service = Services(service=body['service'])
            db.session.add(new_service)
            db.session.commit() 

            ret = ['Added new service!']
        except Exception as e:
            return e
    return jsonify(ret)

@app.route("/services/<id>", methods = ['PUT', 'DELETE'])
def filtered_services(id):
    ret = []
    if request.method == 'PUT':
        body = request.get_json()
        if not body['service']:
            return { 'error': 'Bad Request'}, 400
        update_service = Services.query.filter_by(id=id).first_or_404()
        update_service.service = body['service']
        db.session.commit()
        ret =[{ 'service': update_service.service}]



    if request.method == 'DELETE':
        delete_service = Services.query.filter_by(id=id).first_or_404()
        db.session.delete(delete_service)
        db.session.commit()
        ret = ['Successfully deleted service!']
    
    return jsonify(ret)

@app.route("/orders", methods = ['GET', 'POST'])
def orders():
    ret = []
    
    if request.method == 'GET':
        for order in Orders.query.all():
            ret.append({'id': order.id ,'service': order.service, 'cabin_id': order.cabin_id, 'date': order.date})
    
    if request.method == 'POST':
        try:
            body = request.get_json()
            url = 'https://moln-node.azurewebsites.net/cabins/owned/{}'.format(body['cabin_id'])
            header = { 'Authorization': 'Bearer {}'.format(auth_token)}
            response = requests.get(url, headers=header)
            
            services = []
            for s in Services.query.filter_by(service=body['service']):
                services.append(s.service)

            if body['cabin_id'] in response.json().values() and len(services)>0:
                new_order = Orders(service=body['service'], cabin_id=body['cabin_id'], date=body['date'])
                db.session.add(new_order)
                db.session.commit()
                ret = ['Service ordered']

        except Exception as e:
            return e

    return jsonify(ret)

@app.route("/orders/<id>", methods = ['PUT', 'DELETE'])
def filtered_orders(id):
    ret = []
  
    if request.method == 'PUT':
        body = request.get_json()
        update_order = Orders.query.filter_by(id=id).first_or_404()
        if body['service']:
            filtered_service = Services.query.filter_by(service=body['service']).first()
            if filtered_service is not None:
                update_order.service = body['service']
            

        if body['date']:
            print(body['date'])
            update_order.date = body['date']
        
        db.session.commit()            
        ret =[{ 'service': update_order.service, 'date': update_order.date}]
  
    if request.method == 'DELETE':
        delete_service = Orders.query.filter_by(id=id).first_or_404()
        db.session.delete(delete_service)
        db.session.commit()
        ret = ['Successfully deleted service!']
    
    return jsonify(ret)
    

@app.route("/cabins")
def cabins():
    try:
        print('GET cabins')
        url = 'https://moln-node.azurewebsites.net/cabins/owned'
        header = { 'Authorization': 'Bearer {}'.format(auth_token)}
        response = requests.get(url, headers=header)
        print(response)
        return jsonify(response.json())
    except json.decoder.JSONDecodeError:
        return "response error"


# Run app if called directly
if __name__ == "__main__":
    app.run()    