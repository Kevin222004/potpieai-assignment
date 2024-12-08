from pydantic import BaseModel
from typing import Optional

class PRAnalysisRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: Optional[str] = None

class CodeIssue(BaseModel):
    type: str
    line: int
    description: str
    suggestion: str

class FileAnalysis(BaseModel):
    name: str
    issues: list[CodeIssue]

class AnalysisSummary(BaseModel):
    total_files: int
    total_issues: int
    critical_issues: int

class AnalysisResult(BaseModel):
    task_id: str
    status: str
    results: dict
