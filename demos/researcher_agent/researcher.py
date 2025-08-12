import os
from datetime import datetime
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

# Load environment variables
load_dotenv()

# Create tmp directory for saving reports
cwd = Path(__file__).parent.resolve()
tmp = cwd.joinpath("tmp")
if not tmp.exists():
    tmp.mkdir(exist_ok=True, parents=True)

today = datetime.now().strftime("%Y-%m-%d")

class Researcher:
    """A researcher class that manages Memori initialization and agent creation"""
    
    def __init__(self):
        # Initialize memori directly
        self.memori = Memori(
            database_connect="sqlite:///research_memori.db",
            conscious_ingest=True,  # Working memory
            auto_ingest=True,  # Dynamic search
            verbose=False,
        )
        self.memori.enable()
        self.memory_tool = create_memory_tool(self.memori)
        
        # Create custom memory search function
        self.memory_search_function = self._create_memory_search_function()
        
        self.research_agent = None
        self.memory_agent = None
    
    def _create_memory_search_function(self):
        """Create memory search function as per Agno documentation"""
        def memory_search(query: str) -> str:
            """Search user's memory for research information, past studies, and findings.

            Use this tool to find information about the user's previous research sessions,
            findings, topics studied, reports generated, and any other research-related 
            information that has been stored in their memory.

            Args:
                query: A descriptive search query about what research information you're looking for.
                      Examples: "past AI research", "findings on quantum computing", "biotech studies",
                      "machine learning reports", "recent research on climate change"
            """
            try:
                if not query or not query.strip():
                    return "Please provide a specific search query for memory search"

                if self.memory_tool is None:
                    return "Memory tool not initialized"

                clean_query = query.strip()
                result = self.memory_tool.execute(query=clean_query)
                return str(result) if result else "No relevant research memories found."
            except Exception as e:
                return f"Memory search error: {str(e)}"
        
        return memory_search
    
    def save_to_memory(self, user_query: str, agent_response: str) -> bool:
        """Directly save conversation to Memori memory"""
        try:
            from litellm import completion
            
            # Since Memori is enabled with conscious_ingest=True, any completion() call
            # will be automatically captured and stored. We just need to simulate a conversation
            messages = [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": agent_response}
            ]
            
            # This completion call will be automatically monitored by Memori
            completion(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1  # Minimal response since we just want memory storage
            )
            return True
            
        except Exception as e:
            print(f"Memory save error: {str(e)}")
            return False
    
    def define_agents(self):
        """Define and create research and memory agents"""
        # Create research agent
        self.research_agent = self._create_research_agent()
        
        # Create memory agent
        self.memory_agent = self._create_memory_agent()
        
        return self.research_agent, self.memory_agent
    
    def get_research_agent(self):
        """Get the research agent, creating it if necessary"""
        if self.research_agent is None:
            self.define_agents()
        return self.research_agent
    
    def get_memory_agent(self):
        """Get the memory agent, creating it if necessary"""
        if self.memory_agent is None:
            self.define_agents()
        return self.memory_agent
    
    def _create_research_agent(self):
        """Create a research agent with Memori memory capabilities and Exa search"""
        agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            tools=[
                ExaTools(start_published_date=today, type="keyword"),
                self.memory_search_function,
            ],
            description=dedent(
                """\
                You are Professor X-1000, a distinguished AI research scientist with MEMORY CAPABILITIES!

                🧠 Your enhanced abilities:
                - Advanced research using real-time web search via Exa
                - Persistent memory of all research sessions
                - Ability to reference and build upon previous research
                - Creating comprehensive, fact-based research reports

                Your writing style is:
                - Clear and authoritative
                - Engaging but professional  
                - Fact-focused with proper citations
                - Accessible to educated non-specialists
                - Builds upon previous research when relevant
            """
            ),
            instructions=dedent(
                """\
                RESEARCH WORKFLOW:
                1. FIRST: Search your memory for any related previous research on this topic
                2. Run 3 distinct Exa searches to gather comprehensive current information
                3. Analyze and cross-reference sources for accuracy and relevance
                4. If you find relevant previous research, mention how this builds upon it
                5. Structure your report following academic standards but maintain readability
                6. Include only verifiable facts with proper citations
                7. Create an engaging narrative that guides the reader through complex topics
                8. End with actionable takeaways and future implications

                Always mention if you're building upon previous research sessions!
            """
            ),
            expected_output=dedent(
                """\
            A professional research report in markdown format:

            # {Compelling Title That Captures the Topic's Essence}

            ## Executive Summary
            {Brief overview of key findings and significance}
            {Note any connections to previous research if found}

            ## Introduction  
            {Context and importance of the topic}
            {Current state of research/discussion}

            ## Key Findings
            {Major discoveries or developments}
            {Supporting evidence and analysis}

            ## Implications
            {Impact on field/society}
            {Future directions}

            ## Key Takeaways
            - {Bullet point 1}
            - {Bullet point 2} 
            - {Bullet point 3}

            ## References
            - [Source 1](link) - Key finding/quote
            - [Source 2](link) - Key finding/quote
            - [Source 3](link) - Key finding/quote

            ---
            Report generated by Professor X-1000 with Memory Enhancement
            Advanced Research Systems Division
            Date: {current_date}
            """
            ),
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True,
            save_response_to_file=str(tmp.joinpath("{message}.md")),
        )
        return agent

    def _create_memory_agent(self):
        """Create an agent specialized in retrieving research memories"""
        agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            tools=[self.memory_search_function],
            description=dedent(
                """\
                You are the Research Memory Assistant, specialized in helping users recall their research history!

                🧠 Your capabilities:
                - Search through all past research sessions
                - Summarize previous research topics and findings
                - Help users find specific research they've done before
                - Connect related research across different sessions

                Your style:
                - Friendly and helpful
                - Organized and clear in presenting research history
                - Good at summarizing complex research into digestible insights
            """
            ),
            instructions=dedent(
                """\
                When users ask about their research history:
                1. Use memory_search to find relevant past research
                2. Organize the results chronologically or by topic
                3. Provide clear summaries of each research session
                4. Highlight key findings and connections between research
                5. If they ask for specific research, provide detailed information

                Always search memory first, then provide organized, helpful summaries!
            """
            ),
            markdown=True,
            show_tool_calls=True,
        )
        return agent


