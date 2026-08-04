# Gunicorn configuration — auto-loaded from the working directory.
#
# Some build-time (SSG) GraphQL queries are heavy: collection pages read
# many image dimensions, and each dimension read fetches from S3. On the
# free-tier instance these can exceed gunicorn's default 30s worker
# timeout, which surfaces as "502 Bad Gateway" during the frontend build.
# Raise the timeout generously so these requests complete.
timeout = 300

# Recycle workers periodically to keep memory in check on small instances.
max_requests = 200
max_requests_jitter = 50
