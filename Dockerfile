# 1. Base Image: Start from an official image that includes Python and Playwright.
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the dependencies file to the container
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install -r requirements.txt

# 5. Copy the rest of the project's source code into the container
COPY . .

# 6. Expose the port that Django will use
EXPOSE 8000

# 7. Command to start the application when the container runs
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]