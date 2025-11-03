# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY src/anomaly_detection/requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application's source code from the host to the container at /app
COPY . .

# Set the PYTHONPATH to include the root of the src directory
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Make port 8085 available to the world outside this container
EXPOSE 8085

# Run the application
CMD ["uvicorn", "src.anomaly_detection.main:app", "--host", "0.0.0.0", "--port", "8085"]