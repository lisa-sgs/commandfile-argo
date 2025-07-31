ARG PYTHON_VERSION=3.11
ARG PYTHON_FLAVOUR=slim
ARG PYTHON_IMAGE=python:${PYTHON_VERSION}-${PYTHON_FLAVOUR}

# Install uv
FROM ${PYTHON_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies
# Git is required for setuptools_scm to figure out the project version
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.git,target=.git \
    uv sync --locked --no-editable

FROM ${PYTHON_IMAGE} AS runtime

# Copy the environment, but not the source code
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Run the application
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["generate-commandfile"]
