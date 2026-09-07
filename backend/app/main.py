from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import os

from .db import init_db

app = FastAPI(title="Cafe Management API", version="0.1.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("--- VALIDATION ERROR ---")
    print(f"Method: {request.method} | URL: {request.url}")
    try:
        body = await request.body()
        print(f"Raw Body: {body.decode('utf-8')}")
    except Exception:
        print("Could not decode body")
    print(f"Errors: {exc.errors()}")
    print("------------------------")
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())}
    )

# Explicit origins are required when allow_credentials is enabled: a "*" wildcard
# is rejected by browsers for credentialed requests.
# Vercel generates a new *.vercel.app alias per deployment, so in addition to the
# explicit CORS_ORIGINS list we allow any https://*.vercel.app origin.
_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins_raw.split(",") if o.strip()],
    allow_origin_regex=r"^https://[a-z0-9.-]*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    os.makedirs('uploads', exist_ok=True)
    await init_db()


# Import routers after app initialization to avoid circular imports
from .api import auth, menu, orders, websocket as ws_module, staff, inventory, profile, dashboard, tables, shifts

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(menu.router, prefix="/api/menu", tags=["menu"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(staff.router, prefix="/api/staff", tags=["staff"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(tables.router, prefix="/api/tables", tags=["tables"])
app.include_router(shifts.router, prefix="/api/shifts", tags=["shifts"])

# WebSocket route registered directly
app.add_api_websocket_route("/ws/orders", ws_module.websocket_endpoint)


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/healthz")
async def health():
    return {"status": "ok"}
