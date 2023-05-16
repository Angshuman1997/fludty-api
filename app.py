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

def jumble_func(word, pattern, action):
    word_len = len(word)
    temp_patt = [pattern] * word_len
    temp_patt = [item for sublist in temp_patt for item in sublist][:word_len]
    temp_word = []
    
    for i in range(len(word)):
        if action == "up":
            temp_word.append(chr(ord(word[i]) + int(temp_patt[i])))
        else:
            temp_word.append(chr(ord(word[i]) - int(temp_patt[i])))
    
    return "".join(temp_word)

def decode_func(str_val):
    mot = os.getenv('SECRET_MOTION')
    pat = os.getenv('SECRET_PATTERN').split(",")
    decode  = jwt.decode(str_val, app.config['SECRET_KEY'], algorithms=[os.getenv("ALGO")])
    if decode["lt"] == "login":
        temp = {
            "login_type": "login",
            "userid": jumble_func(decode["ud"], pat, mot),
            "password": jumble_func(decode["pd"], pat, mot)
        }
    else:
        temp = {
            "login_type": "register",
            "userid": jumble_func(decode["ud"], pat, mot),
            "password": jumble_func(decode["pd"], pat, mot),
            "name": jumble_func(decode["ne"], pat, mot),
            "email": jumble_func(decode["el"], pat, mot)
        }

    return temp

def token_required(func):
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[os.getenv("ALGO")])
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
    doc = {}
    if len(request.headers["search"].strip()) > 0:
        search_value = request.headers["search"].strip()
        doc = {"name": { "$regex": search_value, "$options": "i" }}
        
    elif request.headers["favSort"] == "true":
        doc = {"favourite": request.headers["userid"]}
    
    count = mongo.db.drinks.count_documents(doc)
    data = mongo.db.drinks.find(doc, {'_id': 1, 'name': 1, 'image': 1, 'favourite': 1}).skip(int(request.headers["offset"])).limit(10)
    format_data = [json.dumps(doc, default=json_util.default) for doc in data]
    return {"data": format_data, "total": count}

@app.route("/drinks/<id>", endpoint='one_drink')
@token_required
def one_drink(id):
    data = mongo.db.drinks.find({'_id': ObjectId(id)})
    format_data = [json.dumps(doc, default=json_util.default) for doc in data]
    return {"data": format_data}

@app.route("/favdrink/<id>", endpoint='fav_one_drink', methods=['PUT'])
@token_required
def fav_one_drink(id):
    if request.headers['fav_type'] == "add":
        data = mongo.db.drinks.update_one({'_id': ObjectId(id)}, {'$push': {'favourite': request.headers['userid']}})
        msg = "Added to Favourites"
    else:
        data = mongo.db.drinks.update_one({'_id': ObjectId(id)}, {'$pull': {'favourite': request.headers['userid']}})
        msg = "Removed from Favourites"
    if data:
        return jsonify({'Message': msg}), 200
    else:
        return jsonify({'Message': "Something Went Wrong"}), 400

@app.route('/login', methods=['POST'])
def login():
    val_data = decode_func(request.headers['Validate'])
    
    if val_data['login_type'] == "login":
        fetch_data = mongo.db.accounts.find_one({'userid': val_data['userid']})
        if fetch_data:
            if fetch_data['password'] == val_data['password']:
                session['logged_in'] = True
                token = jwt.encode({'user': val_data['userid'], 'name': fetch_data["name"], 'email': fetch_data["email"], 'expiration': str(datetime.now() + timedelta(seconds=3600)).split(".")[0]},app.config['SECRET_KEY'])
                return jsonify({'token': token }), 200
            else:
                return jsonify({'Message': "Invalid Password"}), 400
        else:
            return jsonify({'Message': "Account doesn't exists, please register"}), 400
    else:
        fetch_userid = mongo.db.accounts.find_one({'userid': val_data['userid']})
        fetch_email = mongo.db.accounts.find_one({'email': val_data['email']})

        if fetch_userid and fetch_email:
            return jsonify({'Message': "Please provide a different userid and email"}), 400 
        elif fetch_email:
            return jsonify({'Message': "Please provide a different email"}), 400
        elif fetch_userid:
            return jsonify({'Message': "Please provide a different userid"}), 400
        else:
            upData = mongo.db.accounts.insert_one({'userid': val_data['userid'], 'password': val_data['password'], 'name': val_data['name'], 'email': val_data['email'], 'createdAt': datetime.now()})
            if upData:
                return jsonify({'Message': "Account Added"}), 200
            else:
                return jsonify({'Message': "Account Addition failed"}), 400

if __name__ == "__main__":
    app.run(debug=True)