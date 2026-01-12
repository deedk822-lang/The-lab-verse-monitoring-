# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the new orchestrator and its requirements
COPY rainmaker_orchestrator/ /app/rainmaker_orchestrator/
COPY rainmaker_cli.py /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/rainmaker_orchestrator/requirements.txt

# Set the default command to run the CLI
# This allows passing arguments to the container to run the tool
ENTRYPOINT ["python", "rainmaker_cli.py"]
