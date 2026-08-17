import streamlit as st


def display_chat_history():
    for question, answer in st.session_state.chat_history:
        st.write(f"**You:** {question}")
        st.write(f"**Answer:** {answer}")
        st.write("---")
