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

auth_token = os.environ.get('AUTH_TOKEN')

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
            ret.append({'service': service.service})
    
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

@app.route("/orders", methods = ['GET', 'POST'])
def orders():
    ret = []
    if request.method == 'GET':
        for order in Orders.query.all():
            ret.append({'service': order.service, 'cabin_id': order.cabin_id, 'date': order.date})
    
    if request.method == 'POST':
        try:
            body = request.get_json()
            url = 'https://moln-node.azurewebsites.net/cabins/owned/{}'.format(body['cabin_id'])
            header = { 'Authorization': 'Bearer {}'.format(auth_token)}
            response = requests.get(url, headers=header)
            print(response)
            services = []
            for s in Services.query.filter_by(service=body['service']):
                services.append(s.service)
            if len(services) < 0 and len(response) < 0:
                new_order = Orders(service=body['service'], cabin_id=body['cabin_id'])
                db.session.add(new_order)
                db.session.commit()
            

            ret = ['Added new service!']
        except Exception as e:
            return e
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