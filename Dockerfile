# Use the official Python base image
FROM python:3.12-slim
# Set the working directory in the container
WORKDIR /app
# Copy the requirements file to the working directory
# Copy the requirements file to the working directory
COPY requirements.txt ./
# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project into the container
COPY . /app

# Make the entrypoint executable
RUN chmod +x /app/entrypoint.sh || true

# Default entrypoint will run migrations (if needed) and start the server
ENTRYPOINT ["/app/entrypoint.sh"]







# Set the entrypoint command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--debug"]
