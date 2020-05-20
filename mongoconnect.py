import pymongo
from pymongo import MongoClient
import urllib.parse


def connect():
    client = MongoClient("mongodb+srv://arques-mongo:" + urllib.parse.quote_plus("mongo10@(") + "@cluster0-4bebd.azure.mongodb.net/?authSource=admin")
    return client


def insert(dbName, docName, dic):
    client = connect()
    db = client[dbName]
    col = db[docName]    

    x = col.insert_one(dic)

    return x

def inserts(dbName, docName, list):
    client = connect()
    db = client[dbName]
    col = db[docName]    

    x = col.insert_many(list)

    return x


# mydic = { "name": "Hangyul Kim", "address": "Suwon" }
# x = insert_one('test', 'customers', mydic)
# print(x)

# client = connect()
# db = client['test']
# result = db.customers.find().sort({_id:1}).limit(2)

# for i in result:
#     print(i)
