# Hypercorn configuration for Content Generation Solution Accelerator

import os

# Bind address
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Workers
workers = int(os.environ.get("WORKERS", "4"))

# Timeout
graceful_timeout = 120
read_timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

# Keep alive
keep_alive_timeout = 120
