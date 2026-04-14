"""
FastAPI Server for Teacher Model API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from ffr.teacher import TeacherModel
import os
from contextlib import asynccontextmanager
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required")
API_BASE = os.getenv("API_BASE", "https://api.siliconflow.cn/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "zai-org/GLM-4.5V")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "45"))
RESULTS_FILE = os.getenv("RESULTS_FILE", "api_results.json")

# Global teacher model instance
teacher_model = None

def load_results():
    """Load existing results from file"""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_results(results):
    """Save results to file"""
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global teacher_model
    teacher_model = TeacherModel(
        api_key=API_KEY,
        api_base=API_BASE,
        model_name=MODEL_NAME,
        temperature=0.1
    )
    logger.info(f"Server started with model: {MODEL_NAME}")
    yield
    # Shutdown
    teacher_model = None
    logger.info("Server shutdown")

app = FastAPI(title="Teacher Model API", lifespan=lifespan)

class AnalysisRequest(BaseModel):
    problem_id: str
    question: str
    video_path: str
    student_response: str
    student_score: float
    ground_truth: str
    reference_reasoning: Optional[str] = None
    incorrect_only: bool = False
    nframes: int = 16

class AnalysisResponse(BaseModel):
    success: bool
    problem_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_response(request: AnalysisRequest):
    """
    Analyze student response with timeout
    """
    start_time = datetime.now()
    logger.info(f"[{start_time}] Processing request for problem_id: {request.problem_id}")
    
    try:
        # Run analysis with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(
                teacher_model.analyze_student_response,
                question=request.question,
                video_path=request.video_path,
                student_response=request.student_response,
                student_score=request.student_score,
                ground_truth=request.ground_truth,
                reference_reasoning=request.reference_reasoning,
                incorrect_only=request.incorrect_only,
                nframes=request.nframes
            ),
            timeout=TIMEOUT_SECONDS
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log success
        logger.info(f"[{end_time}] SUCCESS - problem_id: {request.problem_id}")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info(f"  Error Classification: {result.get('error_classification', 'N/A')}")
        if result.get('raw_response'):
            logger.info(f"  Response preview: {result['raw_response'][:200]}...")
        
        # Save to results file
        record = {
            "problem_id": request.problem_id,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "success": True,
            "request": {
                "question": request.question,
                "video_path": request.video_path,
                "student_response": request.student_response,
                "student_score": request.student_score,
                "ground_truth": request.ground_truth,
                "incorrect_only": request.incorrect_only,
                "nframes": request.nframes
            },
            "response": result
        }
        
        results = load_results()
        results.append(record)
        save_results(results)
        
        return AnalysisResponse(
            success=True,
            problem_id=request.problem_id,
            data=result
        )
        
    except asyncio.TimeoutError:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        error_msg = f"Analysis timeout after {TIMEOUT_SECONDS} seconds"
        
        logger.error(f"[{end_time}] TIMEOUT - problem_id: {request.problem_id}")
        logger.error(f"  Duration: {duration:.2f}s")
        
        # Save timeout record
        record = {
            "problem_id": request.problem_id,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "success": False,
            "error": error_msg
        }
        
        results = load_results()
        results.append(record)
        save_results(results)
        
        return AnalysisResponse(
            success=False,
            problem_id=request.problem_id,
            error=error_msg
        )
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        error_msg = str(e)
        
        logger.error(f"[{end_time}] ERROR - problem_id: {request.problem_id}")
        logger.error(f"  Duration: {duration:.2f}s")
        logger.error(f"  Error: {error_msg}")
        
        # Save error record
        record = {
            "problem_id": request.problem_id,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "success": False,
            "error": error_msg
        }
        
        results = load_results()
        results.append(record)
        save_results(results)
        
        return AnalysisResponse(
            success=False,
            problem_id=request.problem_id,
            error=error_msg
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "timeout": TIMEOUT_SECONDS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
