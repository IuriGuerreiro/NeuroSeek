# MongoDB connection and data insertion
from datetime import datetime
import pymongo
from pymongo import MongoClient
import toml
import models

# get the database connection from config.toml

config = toml.load("config.toml")
mongo_uri = config["uri"]
mongo_db = config["db"]

def connect_to_mongo():
    client = MongoClient(mongo_uri)

    # check if the database exists
    client.list_database_names()
    if mongo_db not in client.list_database_names():
        client[mongo_db].create_collection("webpages")
        client[mongo_db]["webpages"].create_index("url", unique=True)
        client[mongo_db].create_collection("crawlTasks")
        client[mongo_db]["crawlTasks"].create_index("url", unique=True)

    db = client[mongo_db]
    return db

def insert_webpage(db, webpage):
    if (db["webpages"].count_documents({"url": webpage.url}) == 0):
        db["webpages"].insert_one(webpage.__dict__)
    else:
        db["webpages"].update_one({"url": webpage.url}, {"$set": webpage.__dict__})

def check_url_exists(db, url):
    return db["webpages"].count_documents({"url": url}) > 0

def get_waiting_tasks(db):
    return list(db["crawlTasks"].find({"status": "pending"}))

def update_task_status(db, url, status, error_message=None):
    update_fields = {"status": status}
    if error_message:
        update_fields["error_message"] = error_message
    db["crawlTasks"].update_one({"url": url}, {"$set": update_fields})

def create_task(db, url):
    if db["crawlTasks"].count_documents({"url": url}) == 0:
        db["crawlTasks"].insert_one({
            "url": url,
            "status": "pending",
            "attempts": 0,
            "last_attempted": None,
            "error_message": None
        })

def update_task_attempt(db, url, status):
    db["crawlTasks"].update_one(
        {"url": url},
        {
            "status": status,
            "$inc": {"attempts": 1},
            "$set": {"last_attempted": datetime.datetime.utcnow().isoformat()}
        }
    )

def get_image_by_url_count(db, image_url):
    return db["webpages"].count_documents({"image_data.url": image_url})



def insert_many_webpages(db, webpages):
    if webpages:
        webpage_dicts = [obj.__dict__ for obj in webpages]
        # Now you can insert them
        for webpage in webpage_dicts:
            if db["webpages"].count_documents({"url": webpage["url"]}) == 0:
                db["webpages"].insert_one(webpage)
            else:
                db["webpages"].update_one({"url": webpage["url"]}, {"$set": webpage})

def create_many_tasks(db, urls):
    if urls:
        for url in urls:
            # check if the url already exists in the tasks/alr curled, or was redirected to it on the collection
            if db["crawlTasks"].count_documents({"url": url}) == 0:
                if db["webpages"].count_documents({"url": url}) == 0:
                    if db["webpages"].count_documents({"redirect_url": url}) == 0:
                        db["crawlTasks"].insert_one({
                            "url": url,
                            "status": "pending",
                            "attempts": 0,
                            "last_attempted": None,
                            "error_message": None
                        })

def remove_tasks(db, urls):
    db["crawlTasks"].delete_many({"url": {"$in": urls}})