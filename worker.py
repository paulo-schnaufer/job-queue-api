import logging
import time
from app.database import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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

                cursor.execute(
                    "UPDATE jobs SET status = 'running' WHERE id = %s",
                    (job_id,)
                )
                conn.commit()
                try:
                    time.sleep(1)
                    if len(payload) == 1:
                        resultado = f"processado {len(payload)} campo"
                    else:
                        resultado = f"processado {len(payload)} campos"
                    cursor.execute(
                        "UPDATE jobs SET status = 'done', result = %s WHERE id = %s",
                        (
                            resultado,
                            job_id,
                        ),
                    )
                    conn.commit()
                    logger.info(f"Job {job_id} successfully finished.")

                except Exception as e:
                    logger.error(f"Job content error. {job_id}: {e}")
                    cursor.execute(
                        "UPDATE jobs SET status = 'failed' WHERE id = %s",
                        (job_id,)
                    )
                    conn.commit()
            
        except Exception as e:
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