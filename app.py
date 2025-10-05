import streamlit as st
import os
import time


# We will import the function that runs the agent.
# NOTE: To run this successfully, ensure you have a .env file with GOOGLE_API_KEY and TAVILY_API_KEY in the same directory as both files.
try:
    # Attempt to import the function from your agent file
    # You MUST change the agent file to ONLY define the function and remove the 'if __name__ == "__main__":' block, or modify this import.
    # The safest way is to wrap the agent function and the full setup.
    
    # --- Modifying Agent Logic for Safe Import ---
    # For a Streamlit app, we should encapsulate the agent setup and running in a function that *returns* the final answer.
    # The original file's `run_research_agent` currently prints, not returns, and re-initializes everything on every run.
    # To make it robust, let's assume we can import the core executor and a new simplified runner function.
    from research_agent_main import agent_executor 
    
    # A simple runner function for Streamlit, designed to work with the imported executor
    def run_agent_streamlit(query: str):
        """Invokes the agent executor and returns the final answer."""
        # Note: 'verbose=True' in AgentExecutor prints the Thought/Action logs, 
        # which is useful for debugging but we'll only display the final output.
        try:
            result = agent_executor.invoke({"input": query})
            final_answer = result.get('output', 'Agent did not return a structured output.')
            return final_answer
        except Exception as e:
            # Handle potential API key errors, network issues, etc.
            return f"An error occurred during agent execution: {e}"

except ImportError:
    st.error("Could not find 'research_agent.py' or the required components. Please ensure your agent file is correctly named and accessible.")
    # Define a placeholder function to prevent the app from crashing
    def run_agent_streamlit(query: str):
        return f"AGENT ERROR: Cannot run agent. Check your 'research_agent.py' file."


# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="Expert Research Agent Frontend",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Expert Research Agent")
st.caption("Powered by LangChain, Gemini 2.5 Flash, and Tavily Search")

st.sidebar.header("Agent Status")
# Check for API keys as a health check
google_key = os.getenv("GOOGLE_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

if not google_key or not tavily_key:
    st.sidebar.error("⚠️ API Keys Missing!")
    st.sidebar.write("Please ensure you have a `.env` file with `GOOGLE_API_KEY` and `TAVILY_API_KEY` set.")
else:
    st.sidebar.success("✅ Agent Dependencies Loaded.")

# 1. Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial greeting from the AI
    st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm your expert research assistant. What topic should I research for you today?"})

# 2. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Use st.markdown for rich text output (the agent's output is often in markdown)
        st.markdown(message["content"])

# 3. Handle User Input
if prompt := st.chat_input("Ask your research question here..."):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add an empty assistant message to stream the response into
    with st.chat_message("assistant"):
        # Show a loading spinner while the agent is running
        with st.spinner(f"🔍 Running expert agent for: **{prompt}**..."):
            
            # --- AGENT EXECUTION ---
            # Call the modified function to get the research report
            final_report = run_agent_streamlit(prompt)
            # --- END AGENT EXECUTION ---
            
            # Display the final report
            st.markdown(final_report)
            
        # Add the final report to the session state after the loading spinner is done
        st.session_state.messages.append({"role": "assistant", "content": final_report})


st.sidebar.markdown("---")
# st.sidebar.info("Developed by a 5+ YOE Agentic AI Professional.")