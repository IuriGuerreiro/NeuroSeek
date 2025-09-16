# NeuroSeek

Traceback (most recent call last):
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\multiprocessing\process.py", line 315, in _bootstrap
    self.run()
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "F:\Nigger\Projects\Programmes\Browser\test\main.py", line 155, in databases_manager_process
    db = mongo.connect_to_mongo()
  File "F:\Nigger\Projects\Programmes\Browser\test\mongo.py", line 18, in connect_to_mongo
    client.list_database_names()
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2387, in list_database_names
    res = self._list_databases(session, nameOnly=True, comment=comment)
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2327, in _list_databases
    res = admin._retryable_read_command(cmd, session=session, operation=_Op.LIST_DATABASES)
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\database.py", line 1072, in _retryable_read_command
    return self._client._retryable_read(_cmd, read_preference, session, operation)
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2047, in _retryable_read
    return self._retry_internal(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\_csot.py", line 125, in csot_wrapper
    return func(self, *args, **kwargs)
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2003, in _retry_internal
    return _ClientConnectionRetryable(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2765, in run
    return self._read() if self._is_read else self._write()
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2910, in _read
    self._server = self._get_server()
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 2858, in _get_server
    return self._client._select_server(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\mongo_client.py", line 1833, in _select_server
    server = topology.select_server(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\topology.py", line 409, in select_server
    server = self._select_server(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\topology.py", line 387, in _select_server
    servers = self.select_servers(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\topology.py", line 294, in select_servers
    server_descriptions = self._select_servers_loop(
  File "C:\Users\iurif\AppData\Local\Programs\Python\Python39\lib\site-packages\pymongo\synchronous\topology.py", line 344, in _select_servers_loop
    raise ServerSelectionTimeoutError(
pymongo.errors.ServerSelectionTimeoutError: localhost:27018: timed out (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms), Timeout: 30s, Topology Description: <TopologyDescription id: 68c92478374bb62bbfdf7ef2, topology_type: Unknown, servers: [<ServerDescription ('localhost', 27018) server_type: Unknown, rtt: None, error=NetworkTimeout('localhost:27018: timed out (configured timeouts: socketTimeoutMS: 20000.0ms, connectTimeoutMS: 20000.0ms)')>]>