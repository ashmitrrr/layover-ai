FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the downloader script
COPY download_model.py .

# Run the script to download the model into the image
RUN python download_model.py

# Tell Hugging Face to NEVER try to download online (Use Offline Mode)
ENV HF_HUB_OFFLINE=1
# --- NEW SECTION ENDS HERE ---

# Copy the rest of the app code
COPY . .

# Expose port
EXPOSE 8080

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]