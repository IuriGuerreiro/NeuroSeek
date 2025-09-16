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
    client = MongoClient(
        mongo_uri,
        maxPoolSize=50,  # Increase connection pool
        serverSelectionTimeoutMS=5000
    )

    # check if the database exists
    client.list_database_names()
    if mongo_db not in client.list_database_names():
        client[mongo_db].create_collection("webpages")
        client[mongo_db].create_collection("crawlTasks")

    db = client[mongo_db]
    try:
        db["webpages"].create_index("url", unique=True, background=True)
        db["webpages"].create_index([("url", 1), ("last_fetched", -1)], background=True)
        db["crawlTasks"].create_index("url", unique=True, background=True)
        db["crawlTasks"].create_index([("status", 1), ("url", 1)], background=True)
    except:
        pass  # Indexes might already exist
    
    return db


def insert_webpage(db, webpage):
    if (db["webpages"].count_documents({"url": webpage.url}) == 0):
        db["webpages"].insert_one(webpage.__dict__)
    else:
        db["webpages"].update_one({"url": webpage.url}, {"$set": webpage.__dict__})

def check_url_exists(db, url):
    return db["webpages"].count_documents({"url": url}, limit=1) > 0

def get_waiting_tasks(db, limit=1000):
    return list(db["crawlTasks"].find({"status": "pending"}).limit(limit))

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
    if not webpages:
        return
    
    webpage_dicts = [obj.__dict__ if hasattr(obj, '__dict__') else obj for obj in webpages]
    
    # Use upsert operations in bulk
    operations = []
    for webpage in webpage_dicts:
        operations.append(
            pymongo.UpdateOne(
                {"url": webpage["url"]}, 
                {"$set": webpage}, 
                upsert=True
            )
        )
    
    if operations:
        db["webpages"].bulk_write(operations, ordered=False)


def create_many_tasks(db, urls):
    if not urls:
        return
    
    # Single aggregation to get all existing URLs
    pipeline = [
        {"$match": {"$or": [
            {"url": {"$in": urls}},
            {"redirect_url": {"$in": urls}}
        ]}},
        {"$project": {"url": 1, "redirect_url": 1}},
        {"$group": {"_id": None, "existing_urls": {"$addToSet": "$url"}, "redirect_urls": {"$addToSet": "$redirect_url"}}}
    ]
    
    existing_in_webpages = db["webpages"].aggregate(pipeline)
    existing_urls = set()
    
    for result in existing_in_webpages:
        existing_urls.update(result.get("existing_urls", []))
        existing_urls.update(result.get("redirect_urls", []))
    
    # Check existing tasks
    existing_tasks = set(doc["url"] for doc in db["crawlTasks"].find({"url": {"$in": urls}}, {"url": 1}))
    
    # Filter new URLs
    new_tasks = []
    for url in urls:
        if url not in existing_tasks and url not in existing_urls:
            new_tasks.append({
                "url": url,
                "status": "pending",
                "attempts": 0,
                "last_attempted": None,
                "error_message": None
            })
    
    # Bulk insert with ignore duplicates
    if new_tasks:
        try:
            db["crawlTasks"].insert_many(new_tasks, ordered=False)
        except pymongo.errors.BulkWriteError as e:
            # Ignore duplicate key errors
            pass

def remove_tasks(db, urls):
    if urls:
        db["crawlTasks"].delete_many({"url": {"$in": urls}})