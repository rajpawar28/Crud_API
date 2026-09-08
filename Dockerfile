# Use official lightweight Python image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables for clean Python execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose container port (Assignment A3 uses port 3000)
EXPOSE 3000

# Start FastAPI app on 0.0.0.0:3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
