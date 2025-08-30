FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Streamlit and dashboard dependencies
RUN pip install --no-cache-dir streamlit==1.28.1 \
    plotly==5.17.0 \
    pandas==2.1.3 \
    numpy==1.24.3 \
    requests==2.31.0 \
    pyvis==0.3.2 \
    networkx==3.2.1

# Copy frontend code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start Streamlit
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]