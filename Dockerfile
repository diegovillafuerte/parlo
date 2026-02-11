FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached unless pyproject.toml changes)
COPY pyproject.toml .
RUN pip install --no-cache-dir hatchling \
    && pip install --no-cache-dir $(python -c "import tomllib; f=open('pyproject.toml','rb'); deps=tomllib.load(f)['project']['dependencies']; print(' '.join(deps))")

# Copy full application code
COPY . .

# Install the app package itself (deps already installed, so this is fast)
RUN pip install --no-cache-dir --no-deps .

# Make startup script executable
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
