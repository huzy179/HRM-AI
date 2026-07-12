from __future__ import annotations

import logging
import os

from redis import Redis
from rq import Queue, Worker

from backend.observability.telemetry import setup_worker_telemetry


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    setup_worker_telemetry()
    queues_env = os.environ.get("WORKER_QUEUES", "parse,index,llm,default")
    queue_names = [q.strip() for q in queues_env.split(",") if q.strip()]
    conn = Redis.from_url(redis_url)
    queues = [Queue(name, connection=conn) for name in queue_names] or [Queue("default", connection=conn)]
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
