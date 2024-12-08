from anthropic import Anthropic
from typing import List, Optional
from pydantic import BaseModel, Field
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class CodeIssue(BaseModel):
    type: str = Field(description="Type of issue (style, bug, performance, security, best_practice)")
    line: int = Field(description="Line number where the issue was found")
    description: str = Field(description="Description of the issue")
    suggestion: str = Field(description="Suggested fix for the issue")


class FileAnalysis(BaseModel):
    file_path: str = Field(description="Path to the analyzed file")
    issues: List[CodeIssue] = Field(description="List of issues found in the file")


class CodeReviewAgent:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        self.review_template = """
        You are an experienced code reviewer. Review the following code and provide detailed feedback.
        Focus on:
        1. Code style and formatting issues
        2. Potential bugs or errors
        3. Performance improvements
        4. Security concerns
        5. Best practices

        Code to review:
        ```{language}
        {code_content}
        ```

        Provide your analysis in JSON format with the following structure:
        {{
            "issues": [
                {{
                    "type": "style|bug|performance|security|best_practice",
                    "line": <line_number>,
                    "description": "description of the issue",
                    "suggestion": "how to fix it"
                }}
            ]
        }}

        Respond ONLY with the JSON. Be specific about line numbers and provide clear, actionable suggestions.
        """

    async def review_file(self, file_path: str, content: str, language: str) -> FileAnalysis:
        try:
            prompt = self.review_template.format(
                language=language,
                code_content=content
            )

            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            try:
                # Parse the JSON response
                analysis_dict = json.loads(response.content[0].text)
                return FileAnalysis(
                    file_path=file_path,
                    issues=[CodeIssue(**issue) for issue in analysis_dict.get('issues', [])]
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from response: {response.content}")
                return FileAnalysis(
                    file_path=file_path,
                    issues=[
                        CodeIssue(
                            type="error",
                            line=0,
                            description="Failed to parse analysis results",
                            suggestion="Please try again"
                        )
                    ]
                )

        except Exception as e:
            logger.error(f"Error in review_file: {str(e)}")
            return FileAnalysis(
                file_path=file_path,
                issues=[
                    CodeIssue(
                        type="error",
                        line=0,
                        description=f"Error analyzing file: {str(e)}",
                        suggestion="Please try again or contact support if the issue persists"
                    )
                ]
            )

    def generate_summary(self, analyses: List[FileAnalysis]) -> dict:
        total_files = len(analyses)
        total_issues = sum(len(analysis.issues) for analysis in analyses)
        critical_issues = sum(
            1 for analysis in analyses
            for issue in analysis.issues
            if issue.type in ['bug', 'security']
        )

        return {
            "total_files": total_files,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "issues_by_type": self._count_issues_by_type(analyses)
        }

    def _count_issues_by_type(self, analyses: List[FileAnalysis]) -> dict:
        counts = {}
        for analysis in analyses:
            for issue in analysis.issues:
                counts[issue.type] = counts.get(issue.type, 0) + 1
        return counts