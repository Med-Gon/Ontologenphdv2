# mongodb_utils.py
from pymongo import MongoClient

def get_mongo_db(request):
    connection_string = request.session.get('connection_string')
    if not connection_string:
        raise ValueError("No MongoDB connection string found in session.")
    client = MongoClient(connection_string)
    db = client.get_default_database()
    return db
