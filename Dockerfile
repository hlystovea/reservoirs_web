FROM hlystovea/pytorch-forecasting:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /reservoirs_web

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=auto \
    PATH="/reservoirs_web/.venv/bin:$PATH"

COPY pyproject.toml uv.lock .python-version ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

COPY ./web .
