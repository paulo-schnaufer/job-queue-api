import logging
import time
from typing import List, Any
from app.database import get_connection

SQL_STATUS_RUNNING = """
    UPDATE jobs SET status = 'running'
    WHERE id = %s 
"""

SQL_STATUS_DONE = """
    UPDATE jobs SET status = 'done', result = %s
    WHERE id = %s
"""

SQL_STATUS_FAILED = """
    UPDATE jobs SET status = 'failed' WHERE id = %s
"""

SQL_JOB_LOGS = """
    INSERT INTO job_logs (job_id, message)
    VALUES (%s, %s)
"""

MESSAGE_RUNNING = "Job running."

MESSAGE_DONE = "Job done."

MESSAGE_FAILED = "Job failed with {}."

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def execute_and_log(
    cursor,
    sql: str,
    params: List[Any],
    job_id: int,
    message: str
) -> None:
    cursor.execute(sql, tuple(params))
    cursor.execute(SQL_JOB_LOGS, (job_id, message))

def mark_failed(cursor, conn, job_id, error):
    conn.rollback()
    logger.error(f"Job content error. {job_id}: {error}")

    execute_and_log(
        cursor,
        SQL_STATUS_FAILED,
        [job_id],
        job_id,
        MESSAGE_FAILED.format(str(error))
    )
    conn.commit()

    
def main_cycle():
    while True:
        conn = None
        try:
            conn = get_connection()
            conn.autocommit = False
    
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, payload
                    FROM jobs
                    WHERE status = 'pending'
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                """
                )
                row = cursor.fetchone()

                if row is None:
                    conn.commit()
                    time.sleep(2)
                    continue

                job_id, payload = row
                logger.info(f"Processing job {job_id}...")
                try:
                    execute_and_log(
                        cursor, SQL_STATUS_RUNNING, [job_id], job_id, MESSAGE_RUNNING
                    )
                    conn.commit()
                except Exception as e:
                    mark_failed(cursor, conn, job_id, e)

                try:
                    time.sleep(1)
                    if len(payload) == 1:
                        result = f"Processed {len(payload)} field."
                    else:
                        result = f"Processed {len(payload)} fields."

                    execute_and_log(
                        cursor, SQL_STATUS_DONE, [result, job_id], job_id, MESSAGE_DONE
                    )
                    conn.commit()
                    logger.info(f"Job {job_id} successfully finished.")
                except Exception as e:
                    mark_failed(cursor, conn, job_id, e)
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            
            logger.error(f"Internal server error: {e}")
            time.sleep(5)
    
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

def main():
    logger.info("Worker running. Awaiting jobs...")
    main_cycle()

if __name__ == "__main__":
    main()