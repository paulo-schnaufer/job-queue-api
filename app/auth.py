from fastapi import Header, HTTPException

from .database import get_connection

INTERNAL_SERVER_ERROR = "Internal server error."
INVALID_API_KEY_ERROR = "Invalid API key."


def get_current_client(x_api_key: str = Header(...)) -> int:
    try:
        conn = get_connection()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=INTERNAL_SERVER_ERROR,
        )

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM clients
                    WHERE api_key = %s
                    """,
                    (x_api_key,),
                )

                result = cursor.fetchone()

                if result is None:
                    raise HTTPException(
                        status_code=401,
                        detail=INVALID_API_KEY_ERROR,
                    )

                (client_id,) = result
                return client_id
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=INTERNAL_SERVER_ERROR,
        ) from exc
    finally:
        conn.close()
