import aiohttp
from typing import List, Dict, Any, Optional
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeReviewBot"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
            logger.info("GitHub token provided")
        else:
            logger.warning("No GitHub token provided")

    async def get_pr_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get list of files changed in a PR"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
                logger.info(f"Fetching PR files from: {url}")

                async with session.get(url) as response:
                    if response.status == 404:
                        logger.error(f"Pull request {pr_number} not found in repository {repo}")
                        raise ValueError(f"Pull request {pr_number} not found in repository {repo}")

                    response.raise_for_status()
                    files = await response.json()
                    logger.info(f"Found {len(files)} files in PR")
                    return files

        except aiohttp.ClientError as e:
            logger.error(f"Error fetching PR files: {str(e)}")
            raise ValueError(f"Error fetching PR files: {str(e)}")

    async def get_file_content(self, repo: str, file_path: str, sha: str) -> Optional[str]:
        """Get content of a specific file from a PR"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # First try to get the raw content using the raw URL
                url = f"https://raw.githubusercontent.com/{repo}/{sha}/{file_path}"
                logger.info(f"Fetching file content from: {url}")

                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Successfully fetched content for: {file_path}")
                        return content

                    # If raw content fails, try the blob API
                    blob_url = f"{self.base_url}/repos/{repo}/git/blobs/{sha}"
                    logger.info(f"Trying blob API: {blob_url}")

                    async with session.get(blob_url) as blob_response:
                        if blob_response.status == 200:
                            data = await blob_response.json()
                            if data.get("encoding") == "base64":
                                content = base64.b64decode(data["content"]).decode()
                                logger.info(f"Successfully fetched content from blob for: {file_path}")
                                return content

                logger.warning(f"Could not fetch content for: {file_path}")
                return None

        except Exception as e:
            logger.error(f"Error fetching file content for {file_path}: {str(e)}")
            return None

    def get_repo_from_url(self, repo_url: str) -> str:
        """Convert GitHub URL to owner/repo format"""
        parts = repo_url.rstrip("/").split("/")
        repo = f"{parts[-2]}/{parts[-1]}"
        logger.info(f"Converted {repo_url} to {repo}")
        return repo

    async def get_pr_details(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get PR details including base and head SHAs"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
                logger.info(f"Fetching PR details from: {url}")

                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return {
                        "base_sha": data["base"]["sha"],
                        "head_sha": data["head"]["sha"],
                        "title": data["title"],
                        "user": data["user"]["login"]
                    }
        except Exception as e:
            logger.error(f"Error fetching PR details: {str(e)}")
            raise ValueError(f"Error fetching PR details: {str(e)}")