from app.tasks.celery_app import celery_app
from celery import Task
from app.core.agent import CodeReviewAgent
from app.services.github import GitHubService
import asyncio
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeReviewTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        return {
            "exc_type": type(exc).__name__,
            "exc_message": str(exc),
            "task_id": task_id
        }


@celery_app.task(bind=True, base=CodeReviewTask)
def analyze_pr_task(self, repo_url: str, pr_number: int, github_token: Optional[str] = None):
    """
    Analyze a GitHub pull request and return the results
    """
    try:
        logger.info(f"Starting analysis for PR #{pr_number} in {repo_url}")
        if github_token:
            logger.info("GitHub token provided")
        else:
            logger.warning("No GitHub token provided")

        # Create services
        github_service = GitHubService(github_token)
        agent = CodeReviewAgent()

        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_analyze_pr(github_service, agent, repo_url, pr_number))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Error in analyze_pr_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                'task_id': self.request.id
            }
        )
        raise


async def _analyze_pr(github_service, agent, repo_url: str, pr_number: int):
    repo = github_service.get_repo_from_url(repo_url)
    logger.info(f"Analyzing repository: {repo}")

    try:
        # Get PR details first
        pr_details = await github_service.get_pr_details(repo, pr_number)
        logger.info(f"Analyzing PR from {pr_details['user']} - {pr_details['title']}")

        # Get files changed in PR
        files = await github_service.get_pr_files(repo, pr_number)
        logger.info(f"Found {len(files)} files in PR")

        # Analyze each file
        analyses = []
        for file in files:
            if file.get('status') == 'removed':
                logger.info(f"Skipping removed file: {file['filename']}")
                continue

            if int(file.get('changes', 0)) > 1000:
                logger.info(f"Skipping large file: {file['filename']} ({file.get('changes')} changes)")
                continue

            logger.info(f"Fetching content for {file['filename']}")
            content = await github_service.get_file_content(repo, file['filename'], pr_details['head_sha'])

            if content is None:
                logger.warning(f"Could not fetch content for {file['filename']}")
                continue

            # Determine language from file extension
            extension = file['filename'].split('.')[-1].lower()
            language_map = {
                'py': 'python',
                'js': 'javascript',
                'java': 'java',
                'cpp': 'cpp',
                'ts': 'typescript',
                'xml': 'xml',
                'md': 'markdown',
                'yml': 'yaml',
                'yaml': 'yaml',
                'json': 'json'
            }
            language = language_map.get(extension, 'text')
            logger.info(f"Analyzing {file['filename']} as {language}")

            analysis = await agent.review_file(file['filename'], content, language)
            analyses.append(analysis)
            logger.info(f"Completed analysis for {file['filename']}")

        if not analyses:
            logger.warning("No files were successfully analyzed")
            return {
                "files": [],
                "summary": {
                    "total_files": 0,
                    "total_issues": 0,
                    "critical_issues": 0,
                    "message": "No files were analyzed. This could be due to file access restrictions or unsupported file types."
                }
            }

        # Generate summary
        summary = agent.generate_summary(analyses)
        logger.info(f"Analysis complete. Found {summary['total_issues']} issues in {summary['total_files']} files")

        return {
            "files": [analysis.dict() for analysis in analyses],
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error in _analyze_pr: {str(e)}")
        raise ValueError(f"Error analyzing PR: {str(e)}")


# Make sure to export the task
__all__ = ['analyze_pr_task']