import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg2.extras import Json

from ..auth import get_current_client
from ..database import get_connection
from ..schemas.jobs import JobCreate, JobCreated, JobResponse

DEFAULT_JOB_LIMIT = 20
MAX_JOB_LIMIT = 100

INTERNAL_SERVER_ERROR = "Internal server error."
JOB_NOT_FOUND_ERROR = "Job not found."
JOB_CREATE_FAILED_ERROR = "Failed to create job."
CLIENT_NOT_FOUND_ERROR = "Client not found."

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


def _get_connection_or_500():
    try:
        return get_connection()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=INTERNAL_SERVER_ERROR,
        ) from exc


def _row_to_job(row):
    return JobResponse(
        id=row[0],
        client_id=row[1],
        status=row[2],
        payload=row[3],
        result=row[4],
        created_at=row[5],
        updated_at=row[6],
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=JobCreated,
)
def create_job(
    job: JobCreate,
    current_client_id: int = Depends(get_current_client),
):
    sql = """
        INSERT INTO jobs (client_id, payload)
        VALUES (%s, %s)
        RETURNING id;
    """

    conn = _get_connection_or_500()

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (current_client_id, Json(job.payload)))

                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(
                        status_code=500,
                        detail=JOB_CREATE_FAILED_ERROR,
                    )

                (job_id,) = row

            return JobCreated(job_id=job_id, status="pending")

    finally:
        conn.close()

@router.get("/{job_id}")
def get_job(
    job_id: int,
    current_client_id: int = Depends(get_current_client),
):
    sql = """
        SELECT id, client_id, status, payload, result, created_at, updated_at
        FROM jobs
        WHERE id = %s AND client_id = %s
    """

    conn = _get_connection_or_500()

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (job_id, current_client_id,))
                row = cursor.fetchone()

                if row is None:
                    raise HTTPException(
                        status_code=404,
                        detail=JOB_NOT_FOUND_ERROR,
                    )

            return _row_to_job(row)
    finally:
        conn.close()

@router.get("/", response_model=list[JobResponse])
def list_jobs(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(DEFAULT_JOB_LIMIT, ge=1, le=MAX_JOB_LIMIT),
    current_client_id: int = Depends(get_current_client),
):
    sql = """
        SELECT id,
               client_id,
               status,
               payload,
               result,
               created_at,
               updated_at
        FROM jobs
        WHERE client_id = %s
    """
    params: list[object] = [current_client_id]

    if status_filter is not None:
        sql += " AND status = %s"
        params.append(status_filter)

    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    conn = _get_connection_or_500()

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()

                return [_row_to_job(row) for row in rows]
    finally:
        conn.close()
