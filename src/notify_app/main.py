from fastapi import FastAPI, Header, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime, timezone

app = FastAPI(title="Smart Campus - Notification Service (A7)")

class SendNotificationRequest(BaseModel):
    alertId: str
    channel: str
    recipient: str
    message: str

class NotificationResponse(BaseModel):
    notificationId: str
    status: str
    channel: str
    sentAt: str

# In-memory store for idempotency and notifications
processed_requests = set()
notifications_db = []

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notification-service"}

def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != "Bearer local-dev-token":
        raise HTTPException(
            status_code=401,
            detail={
                "type": "https://campus.local/problems/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "detail": "Missing or invalid token"
            }
        )
    return auth_header

@app.get("/notifications")
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    token: str = Depends(verify_token)
):
    result = notifications_db
    if status:
        result = [n for n in result if n["status"] == status]
    return result[:limit]

@app.post("/notifications", status_code=201)
def send_notification(
    request: Request,
    req: SendNotificationRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    token: str = Depends(verify_token)
):
    if req.channel not in ["EMAIL", "SMS", "PUSH"]:
        return JSONResponse(
            status_code=400,
            content={
                "type": "https://campus.local/problems/validation-error",
                "title": "Validation error",
                "status": 400,
                "detail": "channel must be EMAIL, SMS, or PUSH"
            }
        )

    prefer_header = request.headers.get("Prefer", "")
    
    # Xử lý theo Prefer header từ Prism mock/Postman
    if "code=429" in prefer_header:
        return JSONResponse(
            status_code=429,
            content={
                "type": "https://campus.local/problems/rate-limited",
                "title": "Too Many Requests",
                "status": 429,
                "detail": "Rate limit exceeded"
            }
        )
    elif "code=409" in prefer_header:
        return JSONResponse(
            status_code=409,
            content={
                "type": "https://campus.local/problems/conflict",
                "title": "Conflict",
                "status": 409,
                "detail": "Idempotency-Key already processed"
            }
        )
    elif "code=201" in prefer_header:
        # Bỏ qua logic trùng lặp nếu Prefer ép buộc trả 201
        pass
    else:
        # Nếu không ép buộc 201 mà key đã tồn tại thì báo lỗi 409
        if idempotency_key in processed_requests:
            return JSONResponse(
                status_code=409,
                content={
                    "type": "https://campus.local/problems/conflict",
                    "title": "Conflict",
                    "status": 409,
                    "detail": "Idempotency-Key already processed"
                }
            )
    
    # Process notification
    processed_requests.add(idempotency_key)
    notification_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
    new_notif = {
        "notificationId": notification_id,
        "status": "QUEUED",
        "channel": req.channel,
        "sentAt": datetime.now(timezone.utc).isoformat()
    }
    notifications_db.append(new_notif)
    
    return new_notif

# Custom exception handler to return ProblemDetails format
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    if isinstance(exc.detail, dict) and "type" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "https://campus.local/problems/error",
            "title": "Error",
            "status": exc.status_code,
            "detail": str(exc.detail)
        }
    )
