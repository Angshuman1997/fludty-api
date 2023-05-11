from flask import Flask
from flask_pymongo import PyMongo
import json
import os
from bson import json_util
from bson.objectid import ObjectId
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
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


app.run(debug=True, port=5000)