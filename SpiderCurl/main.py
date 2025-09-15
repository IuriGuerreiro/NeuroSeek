import threading
import _asyncio
from django import urls
from matplotlib.pyplot import title
from sympy import content
import toml
import asyncio
import mongo 
import curler
import processInfo
import models
import time
import queue
import multiprocessing

config = toml.load("config.toml")

StartUrls = config.get("start_urls", ["https://www.en.wikipedia.org", "https://www.wikipedia.org","https://www.nytimes.com/international/"])

threadCount = config.get("threads", 500)
batchSize = config.get("batch_size", 1000)

task_queue = queue.Queue()

#queues for storing intermediate results
webpage_queue = queue.Queue()




def process_task():
    thread_name = threading.current_thread().name
    while True:
        try:
            url = task_queue.get(timeout=30)
            print(f"{thread_name} processing {url}")
            redirected, response, redirectLink= curler.fetch_url(url)
            if redirected:
                print(f"301 Redirect for URL: {url} to {response}")
            if response:
                # run it and dont wait for it to finish
                webpage = process_url(response, url, redirectLink)
                if not webpage:
                    mongo.update_task_status(url, "failed", "Failed to process webpage")
                    continue
                
                print(f"Processed {url}: Title: {webpage.title}, Meta Description: {webpage.meta_description}, Text length: {len(webpage.text_content) if webpage.text_content else 0}, Extracted URLs: {len(webpage.extracted_urls)}, Images: {len(webpage.image_data)}")
                # Store the webpage object in the database
                webpage_queue.put(webpage)

        except queue.Empty:
            time.sleep(1)  # Sleep briefly if no task is available
        except Exception as e:
            print(f"An error occurred in a worker thread for {url}: {e}")
        finally:
            task_queue.task_done()

def process_url(response, url, redirectLink):
    if response.status_code == 200:
        # create a new webpage object
        info = processInfo.process_html_content(response.text, url)
        if not info:
            return None


        webpage = models.WebPage(
            url=url,
            redirect_url=redirectLink,
            redirected=redirectLink is not None,
            title=info.get("title"),
            meta_description=info.get("meta_description"),
            text_content=info.get("text_content"),
            extracted_urls=info.get("extracted_urls"),
            image_data=info.get("images_info"),
            metadata=info.get("metadata"),
            last_fetched=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        )
        return webpage


def task_manager_thread():
    db = mongo.connect_to_mongo()
    while True:
        try:
            # Check for new tasks from the database
            new_tasks = mongo.get_waiting_tasks(db)
            if not new_tasks:
                # If no new tasks, check for start URLs
                new_tasks = StartUrls

            for task_url in new_tasks:
                url = task_url.get("url") if isinstance(task_url, dict) else task_url
                if not mongo.check_url_exists(db, url):
                    task_queue.put(url)
            
            # Check for new tasks every 10 seconds (or adjust as needed)
            if task_queue.qsize() < batchSize:
                time.sleep(1)
            else:
                time.sleep(30)
        except Exception as e:
            print(f"Task manager thread error: {e}")
            time.sleep(60) # Sleep longer on error to prevent tight loops

def databases_manager_thread():
    db = mongo.connect_to_mongo()
    while True:
        try:
            if not webpage_queue.empty():
                if webpage_queue.qsize() >= batchSize or task_queue.qsize() < batchSize:
                        print(f"Database manager processing batch of {batchSize} webpages")
                        print(f"Webpage queue size before processing: {webpage_queue.qsize()}")
                        print("aaaaaaaaaaaaaaaaaa")
                        batch = []
                        for _ in range(batchSize):
                            if not webpage_queue.empty():
                                batch.append(webpage_queue.get())
                        mongo.insert_many_webpages(db, batch)

                        # create tasks for extracted urls
                        extracted_urls = []
                        for webpage in batch:
                            for url in webpage.extracted_urls:
                                extracted_urls.append(url)

                        mongo.create_many_tasks(db, extracted_urls)

                        urls = []
                        for webpage in batch:
                            urls.append(webpage.url)
                        mongo.remove_tasks(db, urls) 
            time.sleep(1)

        except Exception as e:
            print(f"Database manager thread error: {e}")
            time.sleep(5)  # Sleep longer on error to prevent tight loops

if __name__ == "__main__":

    print("Starting SpiderCurl...")
    task_manager = threading.Thread(target=task_manager_thread, daemon=True)
    task_manager.start()

    threads = []
    for _ in range(threadCount):
        thread = threading.Thread(target=process_task, daemon=True)
        threads.append(thread)
        thread.start()
    
    task_manager = threading.Thread(target=databases_manager_thread, daemon=True)
    task_manager.start()


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        db = mongo.connect_to_mongo()
        batch = []
        for _ in range(batchSize):
            if not webpage_queue.empty():
                batch.append(webpage_queue.get())
        mongo.insert_many_webpages(db, batch)
        extracted_urls = []
        for webpage in batch:
            for url in webpage.extracted_urls:
                extracted_urls.append(url)

        mongo.create_many_tasks(db, extracted_urls)

        urls = []
        for webpage in batch:
            urls.append(webpage.url)
        mongo.remove_tasks(db, urls)

    except Exception as e:
        print(f"Main thread error: {e}")