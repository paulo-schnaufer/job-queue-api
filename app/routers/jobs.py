import json
import psycopg2
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status, HTTPException, Query
from psycopg2.extras import Json
from ..database import get_connection

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)

class JobCreate(BaseModel):
    client_id: int
    payload: dict[str, Any]

class JobCreated(BaseModel):
    job_id: int
    status: str

class JobOut(BaseModel):
    id: int
    client_id: int
    status: str
    payload: dict[str, Any]
    result: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=JobCreated)
def create_job(job: JobCreate):
    sql = """
        INSERT INTO jobs (client_id, payload)
        VALUES (%s, %s)
        RETURNING id;
    """
    try:
        conn = get_connection()
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error.")

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (job.client_id, Json(job.payload)))
                (job_id,) = cursor.fetchone()
            return JobCreated(job_id=job_id, status="pending")
    except psycopg2.errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {job.client_id} não encontrado.",
        )
    finally:
        conn.close()

@router.get("/{job_id}")
def get_job(job_id: int):
    sql = """
        SELECT id, client_id, status, payload, result, created_at, updated_at
        FROM jobs
        WHERE id = %s
    """
    try:
        conn = get_connection()
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error.")

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (job_id,))
                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Job não encontrado.")
                (
                    job_id,
                    job_client_id,
                    job_status,
                    job_payload,
                    job_result,
                    job_created_at,
                    job_updated_at,
                ) = row

            return JobOut(
                id=job_id,
                client_id=job_client_id,
                status=job_status,
                payload=job_payload,
                result=job_result,
                created_at=job_created_at,
                updated_at=job_updated_at,
            )
    finally:
        conn.close()

@router.get("/", response_model=list[JobOut])
def list_jobs(status: str | None = None, limit: int = Query(20, ge=1, le=100)):
    sql = """
        SELECT id, client_id, status, payload, result, created_at, updated_at
        FROM jobs
    """
    params = []

    if status is not None:
        sql += " WHERE status = %s"
        params.append(status)

    sql += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    try:
        conn = get_connection()
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error.")

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()

                jobs = []
                for row in rows:
                    job_payload = row[3]

                    jobs.append(
                        JobOut(
                            id=row[0],
                            client_id=row[1],
                            status=row[2],
                            payload=job_payload,
                            result=row[4],
                            created_at=row[5],
                            updated_at=row[6],
                        )
                    )
                return jobs
    finally:
        conn.close()
