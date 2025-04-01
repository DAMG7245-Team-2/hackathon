import streamlit as st
from agent.graph import graph

def main():
    st.title("Chat with the Agent")
    
    user_input = st.text_input("You: ", "")
    if st.button("Send"):
        response = graph.ainvoke({"changeme": user_input})
        st.write(f"Agent: {response}")

if __name__ == "__main__":
    main()
