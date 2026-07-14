FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    URDB_API_HOST=0.0.0.0 \
    URDB_API_PORT=8080

WORKDIR /app

RUN groupadd --system urdb \
    && useradd --system --gid urdb --home-dir /app --no-create-home urdb

COPY --chown=urdb:urdb orchestrator/ ./orchestrator/
COPY --chown=urdb:urdb homeassistant/ ./homeassistant/

USER urdb

EXPOSE 8080

CMD ["python", "-m", "homeassistant.server"]
