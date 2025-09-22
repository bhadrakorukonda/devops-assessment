FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (cache-friendly) and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend source
COPY . .

# Flask listens on 5000
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
