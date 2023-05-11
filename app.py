from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
import json
import os
from bson import json_util
from bson.objectid import ObjectId
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

@app.route("/drinks")
def all_drinks():
    data = mongo.db.drinks.find({}, {'_id': 1, 'name': 1, 'image': 1})
    format_data = [json.dumps(doc, default=json_util.default) for doc in data]
    return {"data": format_data}

@app.route("/drinks/<id>")
def one_drinks(id):
    data = mongo.db.drinks.find({'_id': ObjectId(id)})
    format_data = [json.dumps(doc, default=json_util.default) for doc in data]
    return {"data": format_data}

if __name__ == "__main__":
    app.run()