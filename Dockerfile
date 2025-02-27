# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the function code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for local testing (Cloud Functions use 8080 by default)
EXPOSE 8080

# Command to start the function framework
CMD ["functions-framework", "--target=gcs_trigger", "--port=8080"]
