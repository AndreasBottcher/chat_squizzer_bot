FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md /app/

RUN uv sync --locked --no-install-project --no-dev &&\
    rm -rf /var/lib/apt/lists/*\
    && apt-get autoremove -y \
    && apt-get clean autoclean \
    && rm -fr /tmp/* \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

CMD ["uv", "run", "bot.py"]
