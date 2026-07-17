FROM mcr.microsoft.com/devcontainers/python:3.10

# Set working directory
WORKDIR /workspace

# ── System packages ────────────────────────────────────────────────────────
# asciidoctor:           render the AsciiDoc user guide to HTML / PDF
# ruby-asciidoctor-pdf:  PDF back-end for asciidoctor
# default-jre-headless:  required by asciidoctor-diagram (PlantUML)
# sh / bash:             POSIX shell needed by the ip-config.sh syntax checker
RUN apt-get update && apt-get install -y --no-install-recommends \
        asciidoctor \
        ruby-asciidoctor-pdf \
        ruby-rouge \
        default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────
# Copy only the dependency files first so Docker layer caching works
# even when source code changes.
COPY requirements.txt pyproject.toml setup.cfg /workspace/

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ── Install the package itself (editable) ─────────────────────────────────
# The full source tree is copied here; in a Dev Container the workspace
# folder is mounted over /workspace at run-time, so postCreateCommand
# re-runs "pip install -e ." to pick up any local changes.
COPY . /workspace
RUN pip install -e .

# Default command
CMD ["bash"]
