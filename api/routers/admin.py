import hmac
import os

from fastapi import APIRouter, Header, HTTPException

from backend import pipeline

router = APIRouter()


@router.post("/admin/refresh")
def refresh_data(x_refresh_token: str | None = Header(default=None)):
    expected = os.getenv("REFRESH_TOKEN")
    if not expected or not x_refresh_token or not hmac.compare_digest(x_refresh_token, expected):
        raise HTTPException(status_code=401, detail="Ugyldig eller manglende refresh-token")
    rows = pipeline.run(days=30)
    return {"rows_stored": rows}
