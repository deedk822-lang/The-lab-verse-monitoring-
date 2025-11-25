# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code from the host to the container at /app
COPY . .

# Make port 8086 available to the world outside this container
EXPOSE 8086

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8086"]
