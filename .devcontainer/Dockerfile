FROM mcr.microsoft.com/devcontainers/python:3.10

# Set working directory
WORKDIR /workspace

# Copy project files
COPY . /workspace

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install your package
RUN pip install -e .

# Default command
CMD ["bash"]