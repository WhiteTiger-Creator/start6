FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

ENV DEBIAN_FRONTEND=noninteractive

# Least-volatile layers first: fix the working directory before the apt and
# dependency layers so a change to those never invalidates the WORKDIR layer.
WORKDIR /app

# The only step in this build that reaches the network, and a single transient
# mirror failure was enough to fail an image build and void a grading trial, so
# the fetch is retried rather than attempted once.
RUN set -eu; \
    delay=5; \
    for attempt in 1 2 3 4 5; do \
        if apt-get update \
            && apt-get install -y --no-install-recommends tmux asciinema; then \
            rm -rf /var/lib/apt/lists/*; \
            exit 0; \
        fi; \
        echo "apt attempt ${attempt} failed, retrying in ${delay}s" >&2; \
        rm -rf /var/lib/apt/lists/*; \
        sleep "${delay}"; \
        delay=$((delay * 2)); \
    done; \
    exit 1

# /app/data/snapshots.json ships TRUNCATED exactly as the failed rollout left
# it; the pre-incident catalogue and the replay journal beside it are the
# recovery sources the responder has to merge back into the authoritative
# snapshot inventory.
COPY app/ /app/
RUN cp /app/workflow/reconcile_retention.py /app/workflow/.reconcile_retention.original \
    && chmod a-w /app/workflow/.reconcile_retention.original
