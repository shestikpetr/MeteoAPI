# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8085"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging - use user-writable paths
accesslog = "/home/shestikpetr/MeteoAPI/logs/access.log"
errorlog = "/home/shestikpetr/MeteoAPI/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "meteoapi"

# Server mechanics
daemon = False
pidfile = "/home/shestikpetr/MeteoAPI/meteoapi.pid"
user = "shestikpetr"
group = "shestikpetr"
tmp_upload_dir = "/tmp"

# Preload application for better performance
preload_app = True

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"