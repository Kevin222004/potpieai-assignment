from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.github import PRAnalysisRequest
from app.tasks.review import analyze_pr_task

router = APIRouter()


@router.post("/analyze-pr")
async def analyze_pr(
        request: PRAnalysisRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    try:
        # Create a new task
        task_id = analyze_pr_task.delay(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            github_token=request.github_token
        )

        return {"task_id": str(task_id), "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    # Get task status from Celery
    task = analyze_pr_task.AsyncResult(task_id)
    return {"task_id": task_id, "status": task.status}


@router.get("/results/{task_id}")
async def get_results(task_id: str):
    # Get task results from Celery
    task = analyze_pr_task.AsyncResult(task_id)

    if task.status == 'PENDING':
        return {"status": "pending"}
    elif task.status == 'SUCCESS':
        return {"status": "completed", "results": task.get()}
    else:
        return {"status": "failed", "error": str(task.result)}
