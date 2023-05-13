from flask import Flask, request, session, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
import json
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from bson import json_util
from bson.objectid import ObjectId
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = os.getenv('CORS_HEADERS')
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
mongo = PyMongo(app)

def token_required(func):
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            if datetime.strptime(data['expiration'], '%Y-%m-%d %H:%M:%S') > datetime.now():
                pass
            else:
                return jsonify({'Message': 'Session Expired'}), 440
        except:
            return jsonify({'Message': 'Invalid token'}), 403
        return func(*args, **kwargs)
    return decorated

@app.route("/drinks", endpoint='all_drinks')
@token_required
def all_drinks():
    data = mongo.db.drinks.find({}, {'_id': 1, 'name': 1, 'image': 1}).skip(int(request.headers["offset"])).limit(10)
    format_data = [json.dumps(doc, default=json_util.default) for doc in data]
    return {"data": format_data}

@app.route("/drinks/<id>", endpoint='one_drink')
@token_required
def one_drink(id):
    data = mongo.db.drinks.find({'_id': ObjectId(id)})
    format_data = [json.dumps(doc, default=json_util.default) for doc in data]
    return {"data": format_data}

@app.route("/favdrink/<id>", endpoint='fav_one_drink', methods=['PUT'])
@token_required
def fav_one_drink(id):
    if request.form['fav_type'] == "add":
        data = mongo.db.drinks.update_one({'_id': ObjectId(id)}, {'$push': {'favourite': request.form['userid']}})
        msg = "Added to Favourites"
    else:
        data = mongo.db.drinks.update_one({'_id': ObjectId(id)}, {'$pull': {'favourite': request.form['userid']}})
        msg = "Removed from Favourites"
    if data:
        return jsonify({'Message': msg}), 200
    else:
        return jsonify({'Message': "Something Went Wrong"}), 400

@app.route('/login', methods=['POST'])
def login():
    if request.form['login_type'] == "login":
        fetch_data = mongo.db.accounts.find_one({'userid': request.form['userid']})
        if fetch_data:
            if fetch_data['password'] == request.form['password']:
                session['logged_in'] = True
                token = jwt.encode({'user': request.form['userid'],'expiration': str(datetime.now() + timedelta(seconds=180)).split(".")[0]},app.config['SECRET_KEY'])
                return jsonify({'token': token}), 200
            else:
                return jsonify({'Message': "Invalid Password"}), 400
        else:
            return jsonify({'Message': "Account doesn't exists, please register"}), 400
    else:
        fetch_userid = mongo.db.accounts.find_one({'userid': request.form['userid']})
        fetch_email = mongo.db.accounts.find_one({'email': request.form['email']})

        if fetch_userid and fetch_email:
            return jsonify({'Message': "Please provide a different userid and email"}), 400 
        elif fetch_email:
            return jsonify({'Message': "Please provide a different email"}), 400
        elif fetch_userid:
            return jsonify({'Message': "Please provide a different userid"}), 400
        else:
            upData = mongo.db.accounts.insert_one({'userid': request.form['userid'], 'password': request.form['password'], 'name': request.form['name'], 'email': request.form['email'], 'createdAt': datetime.now()})
            if upData:
                return jsonify({'Message': "Account Added"}), 200
            else:
                return jsonify({'Message': "Account Addition failed"}), 400

if __name__ == "__main__":
    app.run(debug=True)