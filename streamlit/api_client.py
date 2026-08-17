import os
import requests

BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
UPLOAD_ENDPOINT = f"{BASE_URL}/upload_pdf/"
CHAT_ENDPOINT = f"{BASE_URL}/chat/"


def upload_pdf_to_backend(uploaded_file) -> dict:
    try:
        response = requests.post(
            UPLOAD_ENDPOINT,
            files={"file": (uploaded_file.name, uploaded_file, "application/pdf")},
            timeout=120,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ask_backend(doc_id: str, session_id: str, question: str) -> dict:
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={"doc_id": doc_id, "session_id": session_id, "question": question},
            timeout=120,
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
