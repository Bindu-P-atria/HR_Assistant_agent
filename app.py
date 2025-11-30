import streamlit as st
from hr_assistant_leave import ask_hr
from hr_assistant_leave import listen, speak
import pyttsx3

# Streamlit page config
st.set_page_config(page_title="HR Assistant", page_icon="🧑‍💼", layout="centered")
st.title("🧑‍💼 Smart HR Assistant - Voice & Text Chatbot")
st.write("Ask any HR related question using **text** or **voice mode**.")

# --- Session state for chat ---
if "chat" not in st.session_state:
    st.session_state.chat = []

# --- Choose mode ---
mode = st.radio("Choose interaction mode:", ["Text Chat", "Voice Chat"])

# --- TEXT MODE ---
if mode == "Text Chat":
    emp_id = st.number_input("Enter your Employee ID:", min_value=1, step=1)
    user_input = st.text_input("Enter your HR question:")

    if st.button("Ask") and user_input.strip():
        answer = ask_hr(emp_id, user_input)
        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("Assistant", answer))

# --- VOICE MODE ---
elif mode == "Voice Chat":
    st.write("Press the button and speak your question.")
    emp_id = st.number_input("Enter your Employee ID:", min_value=1, step=1)

    if st.button("Record & Ask"):
        question = listen()
        if question:
            answer = ask_hr(emp_id, question)
            st.session_state.chat.append(("You (Voice)", question))
            st.session_state.chat.append(("Assistant", answer))
            speak(answer)

# --- Display chat history ---
st.subheader("Chat History")
for role, message in st.session_state.chat:
    st.write(f"**{role}:** {message}")
