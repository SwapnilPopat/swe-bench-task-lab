FROM python:3.11-slim

LABEL maintainer="Benchmark Engineering Lab"
LABEL description="Hermetic sandbox for evaluating autonomous coding agents on HTTP resilience tasks."

# Install basic toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    patch \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged runner
RUN useradd -m -s /bin/bash evaluator
WORKDIR /workspace

# Copy task files
COPY . /workspace

# Set environment
ENV PYTHONPATH="/workspace/src:$PYTHONPATH"

# Install test dependencies
RUN pip install --no-cache-dir pytest==7.4.3

# Initialize git repository state inside container
RUN git config --global user.email "evaluator@benchmark.local" \
    && git config --global user.name "Harness Evaluator" \
    && git init . \
    && git add . \
    && git commit -m "base commit: initial reproducible snapshot"

RUN chown -R evaluator:evaluator /workspace
USER evaluator

ENTRYPOINT ["python3", "verify.py"]
