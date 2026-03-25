# fitcheck — backend

FastAPI + NiceGUI backend. See the [root README](../README.md) for setup instructions.

## Running tests

```bash
uv run pytest tests/ -v --cov=app.core.supabase_db --cov=app.routers.crawler_jobs
```
