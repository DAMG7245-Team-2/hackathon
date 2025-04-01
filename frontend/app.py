import streamlit as st
import requests
import os

def main():
    st.title("Chat with the Agent")
    
    user_input = st.text_input("You: ", "")
    if st.button("Send"):
        fastapi_url = os.getenv("FASTAPI_URL")
        response = requests.post(f"{fastapi_url}/chat", json={"user_message": user_input})
        st.write(f"Agent: {response.json()['response']}")

if __name__ == "__main__":
    main()
