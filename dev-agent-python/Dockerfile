FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# git: for git_tools and pulling repos
# build-essential: for compiling some python deps (like tree-sitter if enabled)
# curl: for healthcheck and poetry install
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock* /app/
RUN --mount=type=cache,target=/root/.cache/pypoetry poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy Application Code (not needed if mounting volume in dev, but good for build)
COPY . /app

# Expose API
EXPOSE 8000

# Default Command (API)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
