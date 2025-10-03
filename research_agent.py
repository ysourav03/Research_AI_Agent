import os
from dotenv import load_dotenv

# LangChain components
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# 1. Load Environment Variables
# The .env file must be in the same directory as this script.
load_dotenv()

# Check for API Keys
if not os.getenv("GOOGLE_API_KEY") or not os.getenv("TAVILY_API_KEY"):
    raise ValueError("API keys for GOOGLE_API_KEY and TAVILY_API_KEY must be set in the .env file.")

# 2. Define the Tools
# The TavilySearch tool allows the agent to look up current information on the web.
search_tool = TavilySearch(max_results=3) 
tools = [search_tool]

# 3. Initialize the Language Model (LLM)
# Using gemini-2.5-flash which is a fast, capable, and free-tier model.
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0 # Use low temperature for research tasks
)

# 4. Define the Agent Prompt
# The prompt template guides the LLM on its role, the tools it has, and the format for thought/action.
# LangChain's create_react_agent handles the standard ReAct instructions.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert research assistant. Your task is to accurately answer user questions. You MUST use the 'tavily_search_results_json' tool for any question requiring up-to-date or external information. Provide a detailed, well-structured answer with sources."),
        ("user", "{input}"),
        # The agent logic (tool calls, thoughts, observations) will be inserted here.
    ]
)

# 5. Create the Agent
# The create_react_agent function assembles the LLM, the tools, and the prompt into a full agent.
agent = create_react_agent(llm, tools, prompt)

# 6. Create the Agent Executor
# The executor is the runtime that handles the agent's full cycle:
# LLM prompt -> LLM output (thought/action) -> Tool execution -> LLM prompt (with observation) -> Final answer.
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 7. Run the Agent
def run_research_agent(query: str):
    """Invokes the agent to answer a research query."""
    print(f"\n--- Running Agent for Query: '{query}' ---")
    try:
        result = agent_executor.invoke({"input": query})
        
        # The final answer is typically in the 'output' or a similar key in the result dictionary
        final_answer = result.get('output', 'Agent did not return a structured output.')
        print("\n--- FINAL RESEARCH REPORT ---")
        print(final_answer)

    except Exception as e:
        print(f"\nAn error occurred during agent execution: {e}")

if __name__ == "__main__":
    # Example Query
    research_query = "What is the latest news regarding the stock price of Tesla (TSLA) today?"
    run_research_agent(research_query)

    print("\n----------------------------------------------------")
    
    # Another example query that requires web search
    second_query = "Explain the concept of 'Retrieval-Augmented Generation' (RAG) and why it's used in modern LLM applications."
    run_research_agent(second_query)