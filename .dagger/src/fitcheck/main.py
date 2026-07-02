"""FitCheck CI pipeline as a Dagger module.

Functions (run with `dagger call <name>`):
  env    — backend container with all deps synced (uv, incl. dev group)
  test   — run pytest
  lint   — run ruff check
  build  — build the backend image from backend/Dockerfile
  ci     — lint + test + build in one shot
"""

from typing import Annotated

import dagger
from dagger import DefaultPath, Ignore, dag, function, object_type

# backend/ is the Python project. Default so `dagger call test` needs no args;
# ignore local venv/cache so they never bust the layer cache.
Backend = Annotated[
    dagger.Directory,
    DefaultPath("backend"),
    Ignore([".venv", "**/__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache"]),
]


@object_type
class Fitcheck:
    @function
    def env(self, source: Backend) -> dagger.Container:
        """Backend container with all (incl. dev) deps synced via uv."""
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_exec(["pip", "install", "--no-cache-dir", "uv"])
            .with_workdir("/app")
            # dummy values so pydantic Settings validates; tests mock all real calls
            .with_env_variable("DATABASE_URL", "postgresql+asyncpg://ci:ci@localhost/ci")
            .with_env_variable("GEMINI_API_KEY", "ci-dummy-key")
            # deps layer first — cached until pyproject/lock change
            .with_file("/app/pyproject.toml", source.file("pyproject.toml"))
            .with_file("/app/uv.lock", source.file("uv.lock"))
            .with_exec(["uv", "sync"])
            # then the actual code
            .with_directory("/app", source)
        )

    @function
    async def test(self, source: Backend) -> str:
        """Run the pytest suite."""
        return await self.env(source).with_exec(["uv", "run", "pytest", "-q"]).stdout()

    @function
    async def lint(self, source: Backend) -> str:
        """Run ruff check over the backend."""
        return await self.env(source).with_exec(["uv", "run", "ruff", "check", "."]).stdout()

    @function
    def build(self, source: Backend) -> dagger.Container:
        """Build the backend image from backend/Dockerfile."""
        return source.docker_build()

    @function
    async def ci(self, source: Backend) -> str:
        """Full pipeline: lint, test, then confirm the image builds."""
        lint = await self.lint(source)
        test = await self.test(source)
        await self.build(source).sync()
        return f"=== lint ===\n{lint}\n=== test ===\n{test}\n=== build ===\nOK\n"
