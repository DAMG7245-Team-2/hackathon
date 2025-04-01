import base64
import os

from dotenv import load_dotenv
import requests
import streamlit as st

load_dotenv()
FASTAPI_URL = os.getenv("FASTAPI_URL")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "research_document" not in st.session_state:
    st.session_state.research_document = None

st.set_page_config(page_title="Job Interview Preparation Assistant", layout="wide")

# Sidebar
with st.sidebar:
    st.title("Job Interview Preparation Assistant")
    st.markdown("This assistant helps you prepare for job interviews by generating comprehensive research documents based on job descriptions.")
    
    # Clear conversation button
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.research_document = None
        st.rerun()

# Main chat interface
st.title("Job Interview Preparation Assistant")

# Function to create a download link for the markdown file
def get_download_link(file_content, file_name):
    """
    Generates a link allowing the user to download a file from the app.
    :param file_content: The content of the file to download.
    :param file_name: The name of the file to download.
    :return: A link to download the file.
    """
    b64 = base64.b64encode(file_content.encode()).decode()
    href = f'<a href="data:file/markdown;base64,{b64}" download="{file_name}">Download {file_name}</a>'
    return href

# Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "is_markdown" in message and message["is_markdown"]:
            st.markdown(message["content"])
        else:
            st.write(message["content"])

if prompt := st.chat_input("Enter a job description to get started..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner(f"Deep research in progress..."):
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/chat",
                        json={
                            "user_message": prompt
                        }
                    )
                    
                    if response.status_code == 200:
                        research_document = response.text
                        
                        st.session_state.research_document = research_document
                        
                        st.markdown(research_document)
                        
                        st.markdown(get_download_link(research_document, "Interview_Preparation_Guide.md"), unsafe_allow_html=True)
                        
                        message_data = {
                            "role": "assistant", 
                            "content": research_document,
                            "is_markdown": True
                        }
                        
                        st.session_state.messages.append(message_data)
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"Error: Unable to generate research document. Status code: {response.status_code}",
                            "is_markdown": False
                        })
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"Error: Unable to connect to the research API. {str(e)}",
                        "is_markdown": False
                    })


# Download button for the latest interveiew preparation guide
if st.session_state.research_document:
    st.sidebar.markdown("### Download Interview Preparation Guide")
    st.sidebar.markdown(get_download_link(st.session_state.research_document, "Interview_Preparation_Guide.md"), unsafe_allow_html=True)