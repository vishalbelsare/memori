#!/usr/bin/env python3
"""
Multi-Agent Memory Example for Memoriai v1.0
Demonstrates multiple agents sharing and using memory systems
"""

import os
from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv
import time

load_dotenv()


def main():
    print("🤖🤖 Multi-Agent Memory Example - Memoriai v1.0")
    print("=" * 55)

    # Initialize multiple agent memory systems

    # Agent 1: Research Assistant
    research_agent = Memori(
        database_connect="sqlite:///research_agent.db",
        template="basic",
        mem_prompt="Research agent focused on gathering and organizing information, facts, and research findings",
        conscious_ingest=True,
        namespace="research_agent",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="research_001",
    )

    # Agent 2: Planning Assistant
    planning_agent = Memori(
        database_connect="sqlite:///planning_agent.db",
        template="basic",
        mem_prompt="Planning agent focused on strategies, schedules, and task organization",
        conscious_ingest=True,
        namespace="planning_agent",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="planning_001",
    )

    # Agent 3: Communication Assistant
    communication_agent = Memori(
        database_connect="sqlite:///communication_agent.db",
        template="basic",
        mem_prompt="Communication agent focused on user preferences, messaging styles, and interpersonal interactions",
        conscious_ingest=True,
        namespace="communication_agent",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="communication_001",
    )

    print("✅ Multi-agent memory systems initialized")

    # Enable all agents
    agents = {
        "Research": research_agent,
        "Planning": planning_agent,
        "Communication": communication_agent,
    }

    for name, agent in agents.items():
        agent.enable()
        print(f"✅ {name} agent enabled: {agent.session_id[:8]}...")

    # Example 1: Agent-specific memory recording
    print("\n🎯 Example 1: Agent-specific memory recording...")

    # Research Agent conversations
    research_conversations = [
        {
            "user": "What are the latest developments in quantum computing?",
            "ai": "Recent quantum computing developments include IBM's 1000+ qubit processors, Google's quantum error correction breakthroughs, and advancements in quantum algorithms for optimization problems. Key players are IBM, Google, IonQ, and Rigetti.",
            "focus": "research_findings",
        },
        {
            "user": "Find information about sustainable energy solutions",
            "ai": "Sustainable energy solutions include solar photovoltaic efficiency improvements (now 26%+ in commercial panels), wind turbine blade optimization, battery storage advancement with lithium-iron-phosphate technology, and emerging fusion energy research at companies like Commonwealth Fusion.",
            "focus": "research_data",
        },
    ]

    research_ids = []
    for conv in research_conversations:
        chat_id = research_agent.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model="research-specialist-gpt-4o",
            metadata={"agent_role": "research", "focus": conv["focus"]},
        )
        research_ids.append(chat_id)
        print(f"  🔬 Research recorded: {chat_id[:8]}...")

    # Planning Agent conversations
    planning_conversations = [
        {
            "user": "Help me plan a 3-month project timeline for implementing a new feature",
            "ai": "For a 3-month feature implementation: Month 1 - Requirements gathering, design, and prototyping (weeks 1-4). Month 2 - Core development, initial testing, and iterative improvements (weeks 5-8). Month 3 - Final testing, documentation, deployment preparation, and launch (weeks 9-12). Include buffer time for unexpected issues.",
            "focus": "project_planning",
        },
        {
            "user": "What's the best approach for managing multiple deadlines?",
            "ai": "For managing multiple deadlines: Use priority matrix (urgent/important), create dependency maps, implement time-blocking for focused work, set up milestone tracking, maintain buffer time (20% rule), and use project management tools like Gantt charts. Review and adjust weekly.",
            "focus": "time_management",
        },
    ]

    planning_ids = []
    for conv in planning_conversations:
        chat_id = planning_agent.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model="planning-specialist-gpt-4o",
            metadata={"agent_role": "planning", "focus": conv["focus"]},
        )
        planning_ids.append(chat_id)
        print(f"  📅 Planning recorded: {chat_id[:8]}...")

    # Communication Agent conversations
    communication_conversations = [
        {
            "user": "I prefer direct, concise communication in professional settings",
            "ai": "Noted your preference for direct, concise professional communication. I'll keep messages brief, use clear action items, avoid unnecessary pleasantries, and focus on key information when discussing work matters.",
            "focus": "communication_preference",
        },
        {
            "user": "How should I communicate complex technical information to non-technical stakeholders?",
            "ai": "For technical-to-non-technical communication: Use analogies and real-world examples, avoid jargon, focus on business impact rather than technical details, use visual aids, provide executive summaries, and always ask for questions to ensure understanding.",
            "focus": "communication_strategy",
        },
    ]

    communication_ids = []
    for conv in communication_conversations:
        chat_id = communication_agent.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model="communication-specialist-gpt-4o",
            metadata={"agent_role": "communication", "focus": conv["focus"]},
        )
        communication_ids.append(chat_id)
        print(f"  💬 Communication recorded: {chat_id[:8]}...")

    # Wait for memory processing
    time.sleep(3)

    # Example 2: Cross-agent memory sharing simulation
    print("\n🔄 Example 2: Cross-agent memory sharing...")

    # Create search tools for each agent
    research_search = create_memory_search_tool(research_agent)
    planning_search = create_memory_search_tool(planning_agent)
    communication_search = create_memory_search_tool(communication_agent)

    # Simulate cross-agent information sharing
    print("Research agent sharing quantum computing info...")
    quantum_info = research_search("quantum computing developments", max_results=1)

    print("Planning agent accessing project timeline expertise...")
    timeline_info = planning_search("project timeline implementation", max_results=1)

    print("Communication agent providing style preferences...")
    comm_info = communication_search(
        "professional communication preferences", max_results=1
    )

    # Combine information from multiple agents
    combined_context = f"""
    Research Context: {quantum_info[:100] if quantum_info else 'No research data'}...
    Planning Context: {timeline_info[:100] if timeline_info else 'No planning data'}...
    Communication Context: {comm_info[:100] if comm_info else 'No communication data'}...
    """

    print("✅ Cross-agent information aggregated")

    # Example 3: Multi-agent collaboration simulation
    print("\n🤝 Example 3: Multi-agent collaboration simulation...")

    # Simulate a collaborative task: "Plan a quantum computing research project"
    collaboration_task = (
        "Plan a quantum computing research project with proper communication strategy"
    )

    # Each agent contributes based on their expertise
    research_contribution = research_agent.retrieve_context(
        "quantum computing", limit=1
    )
    planning_contribution = planning_agent.retrieve_context("project planning", limit=1)
    communication_contribution = communication_agent.retrieve_context(
        "communication strategy", limit=1
    )

    # Compile collaborative response
    collaborative_memories = []
    if research_contribution:
        collaborative_memories.extend(research_contribution)
    if planning_contribution:
        collaborative_memories.extend(planning_contribution)
    if communication_contribution:
        collaborative_memories.extend(communication_contribution)

    print(f"🤝 Collaborative context: {len(collaborative_memories)} contributions")
    for i, memory in enumerate(collaborative_memories, 1):
        summary = memory.get("summary", "No summary")
        agent_context = (
            "Research" if i == 1 else "Planning" if i == 2 else "Communication"
        )
        print(f"  {i}. [{agent_context}] {summary[:60]}...")

    # Record the collaborative result
    for agent_name, agent in agents.items():
        collab_chat_id = agent.record_conversation(
            user_input=collaboration_task,
            ai_output=f"As the {agent_name} agent, I contribute my specialized knowledge to this quantum computing research project planning task.",
            model=f"collaborative-{agent_name.lower()}-agent",
            metadata={
                "collaboration": True,
                "multi_agent": True,
                "task": "quantum_research_planning",
            },
        )
        print(f"  🤝 {agent_name} collaboration: {collab_chat_id[:8]}...")

    # Example 4: Agent specialization analysis
    print("\n📊 Example 4: Agent specialization analysis...")

    for agent_name, agent in agents.items():
        stats = agent.get_memory_stats()
        print(f"{agent_name} Agent Statistics:")
        print(f"  💬 Conversations: {stats.get('chat_history_count', 0)}")
        print(
            f"  🧠 Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}"
        )
        print(f"  🏷️  Entities: {stats.get('total_entities', 0)}")

        categories = stats.get("memories_by_category", {})
        if categories:
            print(
                f"  📊 Top category: {max(categories.items(), key=lambda x: x[1])[0] if categories else 'None'}"
            )
        print()

    # Example 5: Memory synchronization patterns
    print("\n🔄 Example 5: Memory synchronization patterns...")

    # Simulate memory synchronization between agents
    sync_patterns = {
        "Research → Planning": "Share research findings for project planning",
        "Planning → Communication": "Share timeline info for stakeholder updates",
        "Communication → Research": "Share user preferences for research presentation",
    }

    for pattern, description in sync_patterns.items():
        print(f"  🔄 {pattern}: {description}")

    # Simulate actual sync by having agents access each other's relevant memories
    # (In a real system, this would be done through shared memory spaces or APIs)

    # Example 6: Multi-agent decision making
    print("\n🎯 Example 6: Multi-agent decision making...")

    decision_scenario = "Should we prioritize quantum computing research or sustainable energy research for the next quarter?"

    # Each agent provides input based on their expertise
    decision_inputs = {}

    # Research agent input
    research_context = research_agent.retrieve_context(
        "quantum computing sustainable energy", limit=2
    )
    decision_inputs["research"] = (
        f"Based on research data: {len(research_context)} relevant findings available"
    )

    # Planning agent input
    planning_context = planning_agent.retrieve_context(
        "project planning timeline", limit=1
    )
    decision_inputs["planning"] = (
        f"Based on planning expertise: {len(planning_context)} planning considerations"
    )

    # Communication agent input
    communication_context = communication_agent.retrieve_context(
        "communication preferences", limit=1
    )
    decision_inputs["communication"] = (
        f"Based on communication needs: {len(communication_context)} stakeholder factors"
    )

    print("Multi-agent decision inputs:")
    for agent_role, input_summary in decision_inputs.items():
        print(f"  🤖 {agent_role.title()}: {input_summary}")

    # Record the collaborative decision process
    decision_id = research_agent.record_conversation(
        user_input=decision_scenario,
        ai_output="Based on multi-agent analysis: Quantum computing shows higher research momentum and clearer 3-month deliverables, while sustainable energy requires longer-term commitment. Recommend quantum computing for Q1 focus.",
        model="multi-agent-decision-system",
        metadata={"decision_type": "research_prioritization", "agents_involved": 3},
    )
    print(f"✅ Multi-agent decision recorded: {decision_id[:8]}...")

    # Example 7: Agent performance metrics
    print("\n📈 Example 7: Agent performance metrics...")

    total_conversations = sum(
        agent.get_memory_stats().get("chat_history_count", 0)
        for agent in agents.values()
    )
    total_memories = sum(
        agent.get_memory_stats().get("short_term_count", 0)
        + agent.get_memory_stats().get("long_term_count", 0)
        for agent in agents.values()
    )
    total_entities = sum(
        agent.get_memory_stats().get("total_entities", 0) for agent in agents.values()
    )

    print("Multi-Agent System Metrics:")
    print(f"  🤖 Active Agents: {len(agents)}")
    print(f"  💬 Total Conversations: {total_conversations}")
    print(f"  🧠 Total Memories: {total_memories}")
    print(f"  🏷️  Total Entities: {total_entities}")
    print("  🔄 Collaboration Events: 4")  # Based on examples above

    # Clean up all agents
    print("\n🔒 Shutting down multi-agent system...")
    for agent_name, agent in agents.items():
        agent.disable()
        print(f"  🔒 {agent_name} agent disabled")

    print("\n💡 Multi-Agent Memory Benefits:")
    print("   ✅ Specialized knowledge domains")
    print("   ✅ Cross-agent information sharing")
    print("   ✅ Collaborative decision making")
    print("   ✅ Memory synchronization patterns")
    print("   ✅ Distributed expertise utilization")
    print("   ✅ Scalable agent coordination")

    print("\n🎉 Multi-agent memory example completed!")
    print(
        "💾 Check agent databases: research_agent.db, planning_agent.db, communication_agent.db"
    )


if __name__ == "__main__":
    main()
