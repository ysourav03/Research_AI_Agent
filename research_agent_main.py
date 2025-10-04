import os
from dotenv import load_dotenv

# LangChain components
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.format_scratchpad.log import format_log_to_str # Used by ReAct

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
    temperature=0.2 # Use low temperature for research tasks
)

# 4. Define the Agent Prompt (FIXED for create_react_agent)
# create_react_agent expects the agent_scratchpad to be a STRING variable in the prompt
# which contains the Thought/Action/Observation log.
# The .partial() call now pre-fills the tool descriptions and tool names correctly

# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system", 
#             # The system prompt contains the instructions and the ReAct format definition
#             "You are an expert research assistant. Your task is to accurately answer user questions. "
#             "You MUST use the 'tavily_search_results_json' tool for any question requiring up-to-date or external information. "
#             "Provide a detailed, well-structured answer with sources. "
            
#             # Tool information is inserted here
#             "The available tools are: {tools}\n"
#             "The available tool names are: {tool_names}\n\n"
            
#             # The ReAct Format Definition
#             "To answer, you must follow this exact format:\n"
#             "Thought: <Your internal reasoning>\n"
#             "Action: <Tool Name, e.g., tavily_search_results_json, or Final Answer>\n"
#             "Action Input: <Input for the tool or the Final Answer>\n"
#             "Observation: <The tool's result>\n"
#             "... (repeat Thought/Action/Action Input/Observation cycle if necessary) ...\n"
#             "Thought: I now know the final answer\n"
#             "Final Answer: <The final, detailed answer to the user>\n\n"
            
#             # The agent_scratchpad is the string placeholder for the ReAct log (intermediate steps)
#             "{agent_scratchpad}"
#         ),
        
#         # The user message with the query
#         ("user", "{input}"),
#     ]
# ).partial(
#     # Pre-fill tool_names (string of names) and tools (string of name: description)
#     tool_names=", ".join([t.name for t in tools]),
#     tools="\n".join([f"{t.name}: {t.description}" for t in tools]) 
# ) 

# M-2 step - 4
# research_agent.py (Section 4: Define the Agent Prompt)

# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",  
#             # 1. Be assertive about the format
#             "You are an expert research assistant. Your task is to accurately answer user questions. "
#             "You **MUST** adhere to the specific ReAct format provided below for *every* step. "
#             "You **MUST** use the 'tavily_search_results_json' tool for any question requiring up-to-date or external information. "
#             "Provide a detailed, well-structured answer in **MARKDOWN** format with sources included.\n\n" # <-- Added MARKDOWN instruction
            
#             # Tool information remains here
#             "The available tools are: {tools}\n"
#             "The available tool names are: {tool_names}\n\n"
            
#             # 2. Add extra delimiters for clarity (LLMs often respect these)
#             "--- START ReAct FORMAT INSTRUCTIONS ---\n"
#             "To answer, you must follow this exact sequence:\n"
#             "Thought: <Your internal reasoning>\n"
#             "Action: <Tool Name, e.g., tavily_search_results_json, or Final Answer>\n"
#             "Action Input: <Input for the tool or the Final Answer>\n"
#             "Observation: <The tool's result>\n"
#             "... (repeat Thought/Action/Action Input/Observation cycle if necessary) ...\n"
#             "Thought: I now know the final answer\n"
#             "Final Answer: <The final, detailed answer to the user in clean Markdown>\n" # <-- Reiterated "clean"
#             "--- END ReAct FORMAT INSTRUCTIONS ---\n\n"
            
#             "{agent_scratchpad}"
#         ),
        
#         ("user", "{input}"),
#     ]
# ).partial(
#     # Pre-fill tool_names (string of names) and tools (string of name: description)
#     tool_names=", ".join([t.name for t in tools]),
#     tools="\n".join([f"{t.name}: {t.description}" for t in tools]) 
# )
# m-3 step 4
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",  
            "You are an expert research assistant. Your task is to accurately answer user questions. "
            "You **MUST** adhere to the specific ReAct format provided below for *every* step. "
            "You **MUST** use the 'tavily_search_results_json' tool for any question requiring up-to-date or external information. "
            "Provide a detailed, well-structured answer in **MARKDOWN** format with sources included.\n\n"
            
            # --- NEW CRITICAL INSTRUCTION ---
            "**STOPPING CRITERION:** Once you have sufficient information to fully answer the user's request, you **MUST** immediately stop the action/observation loop and proceed to the Final Answer. Do NOT search again if the answer is complete.\n\n"
            # --------------------------------
            
            "The available tools are: {tools}\n"
            "The available tool names are: {tool_names}\n\n"
            
            "--- START ReAct FORMAT INSTRUCTIONS ---\n"
            "To answer, you must follow this exact sequence:\n"
            "Thought: <Your internal reasoning>\n"
            "Action: <Tool Name, e.g., tavily_search_results_json, or Final Answer>\n"
            "Action Input: <Input for the tool or the Final Answer>\n"
            "Observation: <The tool's result>\n"
            "... (repeat Thought/Action/Action Input/Observation cycle if necessary) ...\n"
            "Thought: I now know the final answer\n"
            "Final Answer: <The final, detailed answer to the user in clean Markdown>\n"
            "--- END ReAct FORMAT INSTRUCTIONS ---\n\n"
            
            "{agent_scratchpad}"
        ),
        
        ("user", "{input}"),
    ]
).partial(
    tool_names=", ".join([t.name for t in tools]),
    tools="\n".join([f"{t.name}: {t.description}" for t in tools]) 
)

# 5. Create the Agent
# The create_react_agent function assembles the LLM, the tools, and the prompt into a full agent.
agent = create_react_agent(llm, tools, prompt)

# 6. Create the Agent Executor
# The executor is the runtime that handles the agent's full cycle.
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=30, early_stopping_method='generate')

# 7. Run the Agent
# def run_research_agent(query: str):
#     """Invokes the agent to answer a research query."""
#     print(f"\n--- Running Agent for Query: '{query}' ---")
#     try:
#         # The AgentExecutor handles the formatting of intermediate steps 
#         # into the string required by {agent_scratchpad}
#         result = agent_executor.invoke({"input": query})
        
#         # The final answer is typically in the 'output' key
#         final_answer = result.get('output', 'Agent did not return a structured output.')
#         print("\n--- FINAL RESEARCH REPORT ---")
#         print(final_answer)

#     except Exception as e:
#         print(f"\nAn error occurred during agent execution: {e}")

# if __name__ == "__main__":
#     # Example Query
#     research_query = "What is the latest news regarding the stock price of Tesla (TSLA) today?"
#     run_research_agent(research_query)

#     print("\n----------------------------------------------------")
