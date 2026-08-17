import os

UPLOAD_DIR = "temp_documents"
EMBEDDINGS_DIR = "embeddings_store"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
