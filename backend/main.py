from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.config import settings
from backend.database import init_db
from backend.routes import conversations, chat, models, tools, config, generation, auth, admin, suggestions, bots


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="MIDAS API",
    description="AI Agentic Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(tools.router)
app.include_router(config.router)
app.include_router(generation.router)
app.include_router(suggestions.router)
app.include_router(bots.router)


@app.get("/")
async def root():
    return {
        "name": "MIDAS API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
