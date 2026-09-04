FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# git is a runtime dependency, not a build one: the Shipping page shells out to
# `git log` against the checkouts bind-mounted in at runtime.
RUN apt-get update \
	&& apt-get install -y --no-install-recommends git \
	&& rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH=/opt/venv/bin:$PATH

WORKDIR /app

# The template ships no uv.lock, deliberately: a lockfile pinning versions
# resolved on the day the template was written is stale state, not a starting
# point. Generate one in your own copy with `uv lock`, commit it, and change
# this to `uv sync --frozen --no-dev` - which is the form you want from then
# on, so a rebuild can't silently pick up a different dependency tree.
#
# The glob on uv.lock is what makes both of those states buildable from the
# same line: it matches nothing in the template and the lockfile in a
# specialized copy, while pyproject.toml keeps the COPY itself satisfied. A
# bare `COPY pyproject.toml ./` builds here and then fails the moment the
# instruction above is followed, because --frozen has no lockfile to read.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

COPY .streamlit ./.streamlit
COPY dashboard ./dashboard
COPY app_pages ./app_pages
COPY streamlit_app.py ./

# The container runs as a non-root uid with no /etc/passwd entry, so $HOME
# would otherwise resolve to / and Streamlit's own state writes would fail.
ENV HOME=/tmp

# The checkouts the Shipping page runs `git log` against are bind-mounted in as
# a different uid's files; git refuses to read those without this.
ENV GIT_CONFIG_COUNT=1
ENV GIT_CONFIG_KEY_0=safe.directory
ENV GIT_CONFIG_VALUE_0=*

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py"]
