# AI-Powered Code Review System

An autonomous code review agent system that uses AI (Claude) to analyze GitHub pull requests. The system processes code reviews asynchronously using Celery, provides structured feedback through an API, and includes features like caching, rate limiting, and comprehensive error handling.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Implementation Details](#implementation-details)
- [Setup & Installation](#setup--installation)
- [API Documentation](#api-documentation)
- [Design Patterns & Best Practices](#design-patterns--best-practices)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

### Core Components
1. **FastAPI Server**
   - Handles HTTP requests
   - Provides RESTful API endpoints
   - Implements rate limiting and request validation

2. **Celery Worker**
   - Processes asynchronous code review tasks
   - Manages task queues and retries
   - Handles long-running AI analysis

3. **Redis**
   - Acts as message broker for Celery
   - Provides caching layer
   - Stores rate limiting data

4. **PostgreSQL**
   - Stores task results (optional)
   - Maintains system state
   - Handles persistent data

5. **Claude AI**
   - Performs code analysis
   - Generates review feedback
   - Identifies code issues

### System Flow
1. Client submits PR for review via API
2. Request is validated and rate-limited
3. Task is created and queued in Redis
4. Celery worker picks up task
5. AI performs code analysis
6. Results are stored and returned

## Features

### Core Features
- Asynchronous task processing
- AI-powered code analysis
- Structured API responses
- Multiple programming language support
- GitHub integration

### Advanced Features
1. **Rate Limiting**
   - Per-client request tracking
   - Configurable limits
   - Redis-based implementation

2. **Caching**
   - PR analysis results caching
   - Configurable TTL
   - Redis backend

3. **Error Handling**
   - Comprehensive error types
   - Detailed error messages
   - Automatic retries

4. **Monitoring & Logging**
   - Structured JSON logging
   - Request timing metrics
   - Task status tracking


## Implementation Details

### Rate Limiting Implementation
```python
class RateLimiter:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.rate_limit = 10  # requests
        self.per_seconds = 60  # per minute

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
```
- Uses Redis to track request counts
- Implements sliding window rate limiting
- Handles concurrent requests safely

### Caching Mechanism
```python
class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.default_ttl = 3600  # 1 hour

    async def get_pr_cache_key(self, repo_url: str, pr_number: int):
        return f"pr_analysis:{repo_url}:{pr_number}"
```
- Caches PR analysis results
- Implements TTL-based expiration
- Handles cache invalidation

### AI Integration
```python
class CodeReviewAgent:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
    async def review_file(self, file_path: str, content: str, language: str):
        # AI analysis implementation
```
- Uses Claude for code analysis
- Handles different programming languages
- Provides structured feedback

### Task Processing
```python
@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url: str, pr_number: int):
    """
    Analyzes a GitHub PR asynchronously
    """
    try:
        # Task implementation
```
- Asynchronous task processing
- Error handling and retries
- Status tracking

## Setup & Installation

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd code-review-agent
```

2. Set up virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/code_review_db
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=your_api_key
GITHUB_TOKEN=your_github_token
```

5. Run services:
```bash
# Terminal 1: FastAPI server
uvicorn app.main:app --reload

# Terminal 2: Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```

### Docker Setup

1. Build and run with Docker Compose:
```bash
docker compose up --build
```

This will start:
- FastAPI application on port 8000
- Celery worker
- PostgreSQL database
- Redis instance

## API Documentation

### Endpoints

#### 1. Analyze PR
```http
POST /api/v1/analyze-pr
```
Request:
```json
{
    "repo_url": "https://github.com/user/repo",
    "pr_number": 123,
    "github_token": "optional_token"
}
```
Response:
```json
{
    "task_id": "abc123",
    "status": "pending"
}
```

#### 2. Check Status
```http
GET /api/v1/status/<task_id>
```
Response:
```json
{
    "task_id": "abc123",
    "status": "processing|completed|failed"
}
```

#### 3. Get Results
```http
GET /api/v1/results/<task_id>
```
Response:
```json
{
    "status": "completed",
    "results": {
        "files": [
            {
                "file_path": "main.py",
                "issues": [
                    {
                        "type": "style",
                        "line": 15,
                        "description": "Line too long",
                        "suggestion": "Break line into multiple lines"
                    }
                ]
            }
        ],
        "summary": {
            "total_files": 1,
            "total_issues": 1,
            "critical_issues": 0
        }
    }
}
```

## Design Patterns & Best Practices

1. **Repository Pattern**
   - Separation of data access logic
   - Clean interface for database operations
   - Easy to switch implementations

2. **Factory Pattern**
   - Used for creating service instances
   - Centralizes object creation
   - Simplifies dependency injection

3. **Strategy Pattern**
   - Used in AI analysis for different languages
   - Allows swapping analysis strategies
   - Maintains clean separation of concerns

4. **Best Practices**
   - Comprehensive error handling
   - Input validation
   - Secure configuration management
   - Structured logging
   - Rate limiting
   - Caching strategies

## Advanced Features

### Monitoring & Logging
- Structured JSON logs
- Request timing metrics
- Task status tracking
- Error monitoring

### Security
- Rate limiting
- Input validation
- Secure token handling
- Error message sanitization

### Performance
- Redis caching
- Async processing
- Connection pooling
- Resource limiting

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```
   Error: could not connect to database
   ```
   Solution: Check DATABASE_URL and ensure PostgreSQL is running

2. **Redis Connection Issues**
   ```
   Error: could not connect to Redis
   ```
   Solution: Verify REDIS_URL and Redis server status

3. **Celery Worker Issues**
   ```
   Error: cannot connect to broker
   ```
   Solution: Ensure Redis is running and REDIS_URL is correct

### Docker Issues

1. **Container Startup Failures**
   - Check logs: `docker compose logs`
   - Verify environment variables
   - Check network connectivity

2. **Performance Issues**
   - Monitor resource usage
   - Check container logs
   - Adjust resource limits

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Create pull request

## License
MIT License
