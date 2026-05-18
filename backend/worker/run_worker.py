from __future__ import annotations

import logging
import os

from redis import Redis
from rq import Queue, Worker


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    worker = Worker([Queue("default", connection=conn)], connection=conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
