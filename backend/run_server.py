from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router

app = FastAPI(title="Vaani Debt Collector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Use reloader for dev
    uvicorn.run("run_server:app", host="0.0.0.0", port=8001, reload=True)
