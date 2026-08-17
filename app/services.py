import os
import shutil
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

UPLOAD_DIR = "temp_documents"
EMBEDDINGS_DIR = "embeddings_store"

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")

_embeddings = OllamaEmbeddings()
_llm = Ollama(model=OLLAMA_MODEL)

_session_store: dict[str, BaseChatMessageHistory] = {}


def _get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in _session_store:
        _session_store[session_id] = ChatMessageHistory()
    return _session_store[session_id]


async def process_pdf(file) -> dict:
    """
    Save an uploaded PDF, chunk it, embed it, and persist a FAISS index.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    doc_id = uuid.uuid4().hex
    temp_file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")

    try:
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()

        if not documents:
            return {"status": "error", "message": "No extractable text found in this PDF."}

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)

        db = FAISS.from_documents(splits, _embeddings)

        index_dir = os.path.join(EMBEDDINGS_DIR, doc_id)
        db.save_local(index_dir)

        return {
            "status": "success",
            "message": "PDF processed successfully!",
            "doc_id": doc_id,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def _build_conversational_rag_chain(doc_id: str) -> RunnableWithMessageHistory:
    index_dir = os.path.join(EMBEDDINGS_DIR, doc_id)
    if not os.path.isdir(index_dir):
        raise FileNotFoundError(f"No processed document found for doc_id='{doc_id}'.")

    db = FAISS.load_local(index_dir, _embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()

    # Step 1: reformulate the latest question into a standalone question,
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Given a chat history and the latest user question which might "
         "reference context in the chat history, formulate a standalone "
         "question which can be understood without the chat history. Do "
         "NOT answer the question, just reformulate it if needed and "
         "otherwise return it as is."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(
        _llm, retriever, contextualize_q_prompt
    )

    # Step 2: answer the question using retrieved context.
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an assistant for question-answering tasks. Use the "
         "following pieces of retrieved context to answer the question. "
         "If you don't know the answer, say that you don't know. Use "
         "three sentences maximum and keep the answer concise.\n\n{context}"),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(_llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return RunnableWithMessageHistory(
        rag_chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )


async def ask_question(doc_id: str, session_id: str, question: str) -> dict:
    """
    Answer a question about a previously-processed document, using
    session-scoped chat history for follow-up-question awareness.
    """
    try:
        chain = _build_conversational_rag_chain(doc_id)
        result = chain.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        )
        return {"status": "success", "answer": result["answer"]}
    except FileNotFoundError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
