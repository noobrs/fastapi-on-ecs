from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import logging
from supabase_client import supabase
from app.schemas import ProcessResumeRequest
from app.security import verify_signature
from services.resume_pipeline import resume_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# # Context Manager
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield
#     # Clean up
#     await resume_pipeline.aclose()

# app = FastAPI(lifespan=lifespan, docs_url="/api/py/docs")

app = FastAPI(docs_url="/api/py/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "fastapi", "message": "AI FastAPI is running"}

@app.get("/api/py/health")
def health():
    return {"ok": True, "service": "fastapi"}


@app.get("/api/py/test-supabase")
async def test_supabase():
    """Test Supabase connection by listing tables"""
    try:
        # This will fail if no tables exist, but shows connection works
        # Replace 'your_table_name' with an actual table name from your database
        response = supabase.table('users').select("*").limit(1).execute()
        return {
            "status": "connected",
            "message": "Supabase connection successful",
            "data": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "hint": "Make sure you have created a table in Supabase or update the table name"
        }


@app.post("/api/py/process-resume")
async def process_resume(request: Request, payload: ProcessResumeRequest):
    import traceback
    
    logger.info(f"Received process-resume request for resume_id={payload.resume_id}")
    
    body = await request.body()
    timestamp = request.headers.get("x-resume-timestamp")
    signature = request.headers.get("x-resume-signature")

    if not verify_signature(body, timestamp, signature):
        logger.warning(f"Invalid signature for resume_id={payload.resume_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        result = await resume_pipeline.process(payload)
        logger.info(f"Successfully processed resume_id={payload.resume_id}")
    except Exception as exc:
        # Log the full traceback for debugging
        logger.error(f"ERROR: Resume processing failed for resume_id={payload.resume_id}")
        logger.error(f"Exception type: {type(exc).__name__}")
        logger.error(f"Exception message: {str(exc)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {exc}") from exc

    return {
        "status": "processed",
        "resume_id": result.resume_id,
        "job_seeker_id": result.job_seeker_id,
        "redacted_file_path": result.redacted_file_path,
    }