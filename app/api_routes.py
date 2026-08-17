from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from .services import process_pdf, ask_question

router = APIRouter()


class ChatRequest(BaseModel):
    doc_id: str
    session_id: str
    question: str


@router.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    return await process_pdf(file)


@router.post("/chat/")
async def chat(request: ChatRequest):
    return await ask_question(request.doc_id, request.session_id, request.question)
