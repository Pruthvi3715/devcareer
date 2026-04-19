from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import audit, report, auth, user_router, chat
from models.db import engine, Base
import models.user # To register the models
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DevCareer API",
    description="Developer Career Intelligence System — Backend Pipeline & AI Layer",
    version="1.0.0",
)

# CORS — allow frontend integration (PRD Part 2)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(report.router, prefix="/report", tags=["report"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user_router.router, prefix="/user", tags=["user"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


# --- Seed demo user on startup ---
def _seed_demo_user():
    from models.db import SessionLocal
    from services.auth import get_password_hash
    try:
        db = SessionLocal()
        existing = db.query(models.user.User).filter(models.user.User.email == "demo@devcareer.com").first()
        if not existing:
            demo = models.user.User(
                email="demo@devcareer.com",
                hashed_password=get_password_hash("demo123"),
                skills="Python, JavaScript, TypeScript, Go",
                job_level="Mid-Level",
                company="Demo Corp",
                primary_language="Python",
                coding_style="VS Code + Dark Theme",
                schooling="CS Degree",
            )
            db.add(demo)
            db.commit()
            print("[startup] Demo user seeded: demo@devcareer.com / demo123")
        else:
            print("[startup] Demo user already exists")
        db.close()
    except Exception as e:
        print(f"[startup] Demo user seed failed (non-fatal): {e}")

_seed_demo_user()


@app.get("/")
def root():
    return {"service": "DevCareer API", "version": "1.0.0", "status": "running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
