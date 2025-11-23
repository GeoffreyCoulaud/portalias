FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS build-app

# Set environment for building the app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Install the app
COPY ./src ./pyproject.toml ./uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.14-alpine AS runtime

# Install iptables
RUN apk add --no-cache iptables

# Copy the application from app-builder
COPY --from=build-app /app /app

# Set up environment to run the app
ENV PATH="/app/.venv/bin:$PATH"
ENV LOG_LEVEL=DEBUG
ENV INTERVAL=60
ENV DRY_RUN=false

# Volumes
VOLUME /var/run/docker.sock
VOLUME /zones

# Run
WORKDIR /app
CMD ["python", "-m", "portalias.main.main"]