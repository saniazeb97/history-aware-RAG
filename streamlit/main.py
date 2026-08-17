import uuid
import streamlit as st
from api_client import upload_pdf_to_backend, ask_backend
from ui_helpers import display_chat_history

st.set_page_config(page_title="Chat with PDF", page_icon="📄")
st.title("Chat with PDF")
st.caption("Upload a PDF and query about it")

if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.sidebar.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file and st.session_state.doc_id is None:
    with st.spinner("Processing PDF..."):
        response = upload_pdf_to_backend(uploaded_file)

    if response.get("status") == "success":
        st.session_state.doc_id = response.get("doc_id")
        st.sidebar.success("Document processed! Ask away.")
    else:
        st.sidebar.error(response.get("message", "Failed to process PDF."))

if st.session_state.doc_id:
    display_chat_history()

    user_input = st.text_input("Ask a question about the document:", key="user_input")

    if st.button("Ask") and user_input:
        with st.spinner("Thinking..."):
            response = ask_backend(st.session_state.doc_id, st.session_state.session_id, user_input)

        if response.get("status") == "success":
            st.session_state.chat_history.append((user_input, response["answer"]))
            st.rerun()
        else:
            st.error(response.get("message", "Something went wrong."))
else:
    st.write("### Please upload a PDF to start the conversation.")
