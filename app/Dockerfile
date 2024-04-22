# https://hub.docker.com/_/python
FROM python:3.11-slim as builder

WORKDIR /app

# Install deps
COPY requirements.txt requirements.txt
RUN python -m venv --without-pip .venv && \
    pip install --target .venv/lib/*/site-packages --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir shiv

# Copy code
COPY pyproject.toml .
COPY src src
RUN pip install --target .venv/lib/*/site-packages --no-cache-dir .

RUN shiv \
    --site-packages .venv/lib/*/site-packages \
    --console-script badapp \
    --compile-pyc \
    --reproducible \
    --python /usr/bin/python \
    --output-file badapp.pyz

# debian12 contains python 3.11
FROM gcr.io/distroless/python3-debian12

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY --from=builder /app/badapp.pyz /app/badapp.pyz

CMD ["/app/badapp.pyz"]
