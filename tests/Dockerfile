FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

# Verifier dependencies, baked in (no network at trial time). Grading uses the
# stdlib only (json/hashlib/ast/subprocess) plus pytest.
# The verifier image's one network step. An unguarded index fetch here fails the
# build just as surely as a failed apt fetch does, so it gets the same treatment.
RUN set -eu; \
    delay=5; \
    for attempt in 1 2 3 4 5; do \
        if pip install --no-cache-dir --timeout 60 --retries 5 \
                pytest==8.4.1 \
                pytest-json-ctrf==0.3.5; then \
            exit 0; \
        fi; \
        echo "pip attempt ${attempt} failed, retrying in ${delay}s" >&2; \
        sleep "${delay}"; \
        delay=$((delay * 2)); \
    done; \
    exit 1

# Landing directory for the declared artifact (/app) collected from the agent's
# environment. Its parent must exist in the verifier image before the copy.
RUN mkdir -p /app

# Verifier-execution isolation: the submitted program is run under the unprivileged uid 65534
# (nobody) via setpriv, which the pinned base image already provides. A world-writable scratch
# area lets the candidate write only there; /tests (held-out fixtures) and the reward path stay
# root-owned and unreadable/unwritable to the candidate.
RUN mkdir -p /candidate-work \
    && chmod 1777 /candidate-work

WORKDIR /tests
COPY test_outputs.py /tests/test_outputs.py
COPY test.sh /tests/test.sh
COPY fixtures/ /tests/fixtures/

# Keep the held-out fixtures readable only by root, so the unprivileged candidate cannot read
# expected outputs even though it can be handed staged inputs.
# Closing the two directories is enough: without search permission on them
# nothing below can be reached by another uid, so no recursive mode change
# is needed.
RUN chmod 700 /tests /tests/fixtures
