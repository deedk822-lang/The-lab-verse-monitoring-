# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
# This command copies all files in the build context (the repository root)
# into the container's /app directory. This includes the rainmaker_orchestrator.py
# script (and all other Python modules), making them available for import.
COPY . .

# Run the API server when the container launches
# The api/server.py script correctly modifies its sys.path to find modules
# in the /app directory, so this command will work as intended.
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]
