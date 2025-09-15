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

multiprocessingThreadsCount = config.get("multiprocessForThreads", 1)
multiprocessingCount = config.get("multiprocess", 15)
threadCount = config.get("threads", 5)
batchSize = config.get("batch_size", 1000)

task_queue = multiprocessing.JoinableQueue()
webpage_processing_queue = multiprocessing.JoinableQueue()
#queues for storing intermediate results
webpage_queue = multiprocessing.JoinableQueue()

def worker(webpage_processing_queue, webpage_queue):
    print(f"Worker {multiprocessing.current_process().name} started")
    while True:
        try:
            webpage_item = webpage_processing_queue.get(timeout=1)
            
            if webpage_item.webpage_content:
                webpage = process_url(
                    webpage_item.webpage_content, 
                    webpage_item.status_code,
                    webpage_item.url, 
                    webpage_item.redirect_url
                )
                
                if webpage:
                    # Test serialization before putting in queue
                    try:
                        import pickle
                        pickle.dumps(webpage)
                        webpage_queue.put(webpage)
                        print(f"Worker processed: {webpage_item.url}")
                    except Exception as queue_error:
                        print(f"Queue serialization error for {webpage_item.url}: {type(queue_error).__name__} - {str(queue_error)[:200]}")
                    
        except queue.Empty:
            time.sleep(0.5)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else "No error message"
            if "timeout" not in str(e).lower() and "empty" not in str(e).lower():
                # Only try to access webpage_item if it exists
                url_info = f" for {webpage_item.url}" if 'webpage_item' in locals() else ""
                status_code = f"{webpage_item.status_code}" if 'webpage_item' in locals() and hasattr(webpage_item, 'status_code') else ""
                if status_code and status_code != "200":
                    print(f"Worker error ({status_code}){url_info}: {error_msg[:100]}")
                else:
                    print(f"Worker error ({error_type}){url_info}: {error_msg[:100]}")
            # For debugging, you can also add:
            if error_type != "Empty":
                import traceback
                traceback.print_exc()
            
            time.sleep(0.5)

def thread_worker(task_queue, webpage_processing_queue):
    thread_name = threading.current_thread().name
    print(f"curl thread {thread_name} started")
    while True:
        try:
            url = task_queue.get(timeout=5)
            try:
                redirected, response, redirectLink = curler.fetch_url(url)
                print(f"{thread_name} fetched {url}")
                
                if response is not None and hasattr(response, 'text') and hasattr(response, 'status_code'):
                    webpageQueueItem = models.webpageQueueItem(
                        url=url,
                        redirected=redirected,
                        redirect_url=redirectLink,
                        webpage_content=response.text,
                        status_code=response.status_code
                    )
                    webpage_processing_queue.put(webpageQueueItem)
                    print(f"{thread_name} successfully queued {url}")
                else:
                    print(f"{thread_name} skipping {url} - invalid response")
            except Exception as fetch_error:
                print(f"{thread_name} fetch error for {url}: {fetch_error}")
            
            task_queue.task_done()

        except Exception as e:
            print(f"Error in {thread_name}: {e}")
            time.sleep(1)

def process_url(webpage_content, status_code, url, redirectLink):
    if status_code == 200:
        info = processInfo.process_html_content(webpage_content, url)
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
    return None

def task_manager_process(task_queue):
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
                    if url.startswith(('http://', 'https://')):
                        task_queue.put(url)
                    else:
                        print(f"Skipping invalid URL: {url}")
            
            # Check for new tasks every 10 seconds (or adjust as needed)
            print(f"Task queue size: {task_queue.qsize()}")
            if task_queue.qsize() < batchSize:
                time.sleep(1)
            else:
                time.sleep(30)
        except Exception as e:
            print(f"Task manager process error: {e}")
            time.sleep(60) # Sleep longer on error to prevent tight loops

def databases_manager_process(webpage_queue, task_queue):
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
            print(f"Database manager process error: {e}")
            time.sleep(5)  # Sleep longer on error to prevent tight loops




def worker_threads_process(task_queue, webpage_processing_queue):
    threads = []
    for i in range(threadCount):
        thread = threading.Thread(target=thread_worker, args=(task_queue,webpage_processing_queue), daemon=True)
        threads.append(thread)
        thread.start()
    print(f"Started {threadCount} worker threads for URL fetching")
    
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass



if __name__ == "__main__":
    print("Starting SpiderCurl...")
    task_manager_proc = multiprocessing.Process(target=task_manager_process, args=(task_queue,), daemon=True)
    task_manager_proc.start()
    print("Started task manager process")

    time.sleep(1)  # Give some time for the task manager to populate the queue

    # start the worker thread processes for curling urls
    thread_manager_processes = []
    for i in range(multiprocessingThreadsCount):
        process = multiprocessing.Process(target=worker_threads_process, args=(task_queue, webpage_processing_queue), daemon=True)
        thread_manager_processes.append(process)
        process.start()
    print(f"Started {multiprocessingThreadsCount} thread manager processes")

    # start the worker processes for processing the webpages
    worker_processes = []
    for i in range(multiprocessingCount):
        process = multiprocessing.Process(target=worker, args=(webpage_processing_queue, webpage_queue), daemon=True)
        worker_processes.append(process)
        process.start()
    print(f"Started {multiprocessingCount} worker processes for webpage processing")

    db_manager_proc = multiprocessing.Process(target=databases_manager_process, args=(webpage_queue, task_queue), daemon=True)
    db_manager_proc.start()
    print("Started database manager process")
    
    total_processes = 1 + multiprocessingThreadsCount + multiprocessingCount + 1  # task manager + thread managers + worker processes + db manager
    print(f"Total processes running: {total_processes}")

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