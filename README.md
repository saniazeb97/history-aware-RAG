# History-Aware RAG for PDF Q&A

A history-aware RAG (Retrieval-Augmented Generation) chatbot for PDFs, with a
**FastAPI** backend and a **Streamlit** frontend. Upload a PDF, then ask
questions about it including follow-up questions that reference earlier
turns in the conversation.

## Architecture

```
Streamlit frontend  --(HTTP)-->  FastAPI backend
                                       |
                          /upload_pdf/  --> chunk, embed, save FAISS index
                          /chat/        --> history-aware retrieval + QA
```

Both the document upload **and** the actual chat/question-answering are
served by the FastAPI backend. The frontend is a thin client that just
calls these two endpoints and displays the conversation.

## Setup

### Install

```bash
git clone https://github.com/saniazeb97/history-aware-RAG.git
cd history-aware-RAG
pip install -r requirements.txt
```

### Run

**Start the FastAPI backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Start the Streamlit frontend**:
```bash
cd streamlit
streamlit run main.py
```

## API Reference

### `POST /upload_pdf/`
Uploads a PDF, chunks and embeds it, and saves a FAISS index.

- **Request**: multipart form-data, key `file`
- **Response**:
  ```json
  {"status": "success", "message": "PDF processed successfully!", "doc_id": "..."}
  ```

### `POST /chat/`
Answers a question about a previously-uploaded document, using
session-scoped chat history for follow-up-question awareness.

- **Request body**:
  ```json
  {"doc_id": "...", "session_id": "...", "question": "What is Phase 1?"}
  ```
- **Response**:
  ```json
  {"status": "success", "answer": "..."}
  ```

