# 1. Use a lightweight, official Python base image
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements first (for better caching)
COPY requirements.txt .

# 4. Install dependencies (no-cache to keep image small)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your app code (including layover.db)
COPY . .

# 6. Expose the port (Streamlit default)
EXPOSE 8080

# 7. Run Streamlit on Google's expected port (8080)
CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0