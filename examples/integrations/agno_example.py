#!/usr/bin/env python3
"""
AGNO Framework Integration Example for Memoriai v1.0
Demonstrates integration with AGNO (Adaptive Goal-oriented Navigational Optimization) framework
"""

import os
from memoriai import Memori, create_memory_search_tool
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

def main():
    print("🎯 Memoriai v1.0 + AGNO Framework Integration Example")
    print("=" * 55)
    
    # Initialize Memoriai for AGNO integration
    agno_memory = Memori(
        database_connect="sqlite:///agno_memory.db",
        template="basic",
        mem_prompt="Focus on goal-oriented conversations, adaptive strategies, and navigation decisions",
        conscious_ingest=True,
        namespace="agno_framework",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        user_id="agno_agent_001"
    )
    
    print("✅ Memoriai initialized for AGNO framework integration")
    
    # Enable memory processing
    agno_memory.enable()
    print("✅ Memory processing enabled for AGNO!")
    print(f"📊 Session ID: {agno_memory.session_id}")
    
    # Example 1: Goal-oriented memory storage
    print("\n🎯 Example 1: Goal-oriented conversation recording...")
    
    # Simulate AGNO goal definition
    goal_conversations = [
        {
            "user": "I want to build an AI agent that can adapt its behavior based on user feedback",
            "ai": "For adaptive AI agents, implement a feedback loop system with reinforcement learning. Use reward signals from user interactions, maintain a preference model, and employ techniques like RLHF (Reinforcement Learning from Human Feedback). Consider implementing exploration vs exploitation strategies.",
            "context": "goal_definition",
            "agno_phase": "goal_setting"
        },
        {
            "user": "The agent should be able to navigate complex decision trees efficiently",
            "ai": "For efficient decision tree navigation, implement Monte Carlo Tree Search (MCTS) or hierarchical planning. Use heuristics for pruning, maintain state abstraction for similar situations, and implement dynamic programming for optimal subproblems. Consider A* search for goal-directed navigation.",
            "context": "navigation_strategy",
            "agno_phase": "strategy_planning"
        },
        {
            "user": "I prefer agents that can explain their reasoning process transparently",
            "ai": "Explainable AI is crucial for trust. Implement attention visualization, decision path tracking, and natural language explanations. Use techniques like LIME or SHAP for model interpretability, maintain reasoning traces, and provide confidence scores for decisions.",
            "context": "user_preference",
            "agno_phase": "adaptation"
        }
    ]
    
    agno_chat_ids = []
    for conv in goal_conversations:
        chat_id = agno_memory.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model="agno-gpt-4o",
            metadata={
                "agno_context": conv["context"],
                "agno_phase": conv["agno_phase"],
                "framework": "agno",
                "goal_oriented": True
            }
        )
        agno_chat_ids.append(chat_id)
        print(f"   📝 Recorded {conv['agno_phase']} conversation: {chat_id[:8]}...")
    
    # Example 2: Adaptive memory retrieval
    print("\n🧠 Example 2: Adaptive memory retrieval for AGNO...")
    
    # Wait for memory processing
    time.sleep(2)
    
    # Search for goal-related memories
    goal_memories = agno_memory.retrieve_context("adaptive AI agent", limit=3)
    print(f"📊 Found {len(goal_memories)} goal-related memories:")
    
    for i, memory in enumerate(goal_memories, 1):
        summary = memory.get('summary', 'No summary available')
        category = memory.get('category_primary', 'unknown')
        importance = memory.get('importance_score', 0)
        print(f"  {i}. [{category.upper()}] {summary[:70]}... (importance: {importance:.2f})")
    
    # Example 3: Navigation strategy memories
    print("\n🗺️  Example 3: Navigation strategy memory analysis...")
    
    navigation_memories = agno_memory.retrieve_context("decision tree navigation", limit=2)
    print(f"📊 Found {len(navigation_memories)} navigation-related memories:")
    
    for i, memory in enumerate(navigation_memories, 1):
        summary = memory.get('summary', 'No summary available')
        print(f"  {i}. {summary[:80]}...")
    
    # Example 4: AGNO-specific memory search tool
    print("\n🔧 Example 4: AGNO-specific memory search...")
    
    search_tool = create_memory_search_tool(agno_memory)
    
    # Search for AGNO-related concepts
    agno_searches = [
        "reinforcement learning feedback",
        "explainable AI reasoning",
        "adaptive behavior strategies"
    ]
    
    for search_query in agno_searches:
        search_result = search_tool(search_query, max_results=2)
        try:
            search_data = json.loads(search_result)
            found = search_data.get('found', 0)
            print(f"   🔍 '{search_query}': {found} results")
            
            if found > 0:
                for memory in search_data['memories'][:1]:  # Show first result
                    summary = memory.get('summary', 'No summary')
                    category = memory.get('category', 'unknown')
                    print(f"     └─ [{category}] {summary[:60]}...")
        
        except json.JSONDecodeError:
            print(f"   🔍 '{search_query}': Search completed")
    
    # Example 5: Goal optimization memory pattern
    print("\n⚡ Example 5: Goal optimization memory patterns...")
    
    # Record optimization strategies
    optimization_conversations = [
        {
            "user": "How can I optimize the agent's learning speed while maintaining accuracy?",
            "ai": "Balance exploration vs exploitation using epsilon-greedy strategies or Upper Confidence Bound (UCB). Implement curriculum learning to start with simpler tasks. Use transfer learning from similar domains and implement early stopping to prevent overfitting.",
            "optimization_type": "learning_speed"
        },
        {
            "user": "What's the best way to handle conflicting objectives in multi-goal scenarios?",
            "ai": "Use Pareto optimization for multi-objective scenarios. Implement weighted scoring functions, priority queues for goal ranking, and negotiation algorithms for conflict resolution. Consider lexicographic ordering for strict priorities.",
            "optimization_type": "multi_objective"
        }
    ]
    
    optimization_ids = []
    for conv in optimization_conversations:
        chat_id = agno_memory.record_conversation(
            user_input=conv["user"],
            ai_output=conv["ai"],
            model="agno-optimizer-gpt-4o",
            metadata={
                "optimization_type": conv["optimization_type"],
                "framework": "agno",
                "phase": "optimization"
            }
        )
        optimization_ids.append(chat_id)
        print(f"   ⚡ Recorded optimization strategy: {chat_id[:8]}...")
    
    # Example 6: AGNO framework statistics
    print("\n📈 Example 6: AGNO framework statistics...")
    
    stats = agno_memory.get_memory_stats()
    
    print("AGNO Memory Statistics:")
    print(f"  🎯 Total Goal-oriented Conversations: {stats.get('chat_history_count', 0)}")
    print(f"  🧠 Stored Memories: {stats.get('short_term_count', 0) + stats.get('long_term_count', 0)}")
    print(f"  🏷️  Extracted Entities: {stats.get('total_entities', 0)}")
    print(f"  ⭐ Average Importance: {stats.get('average_importance', 0):.2f}")
    
    categories = stats.get('memories_by_category', {})
    if categories:
        print(f"  📊 Memory Categories:")
        for category, count in categories.items():
            print(f"     - {category}: {count}")
    
    # Example 7: AGNO decision support system
    print("\n🤖 Example 7: AGNO decision support system...")
    
    # Simulate decision point
    decision_context = "The agent needs to choose between exploring new strategies vs exploiting known successful patterns"
    
    # Get relevant memories for decision support
    decision_memories = agno_memory.retrieve_context("exploration exploitation strategies", limit=3)
    
    if decision_memories:
        print(f"📋 Decision support memories ({len(decision_memories)} found):")
        for i, memory in enumerate(decision_memories, 1):
            summary = memory.get('summary', 'No summary')
            importance = memory.get('importance_score', 0)
            print(f"  {i}. {summary[:70]}... (weight: {importance:.2f})")
    else:
        print("📭 No relevant decision support memories found")
    
    # Record the decision process
    decision_chat_id = agno_memory.record_conversation(
        user_input=decision_context,
        ai_output="Based on current performance metrics and exploration history, recommend balanced approach: 70% exploitation of proven strategies, 30% exploration of new patterns. Implement adaptive threshold based on recent success rates.",
        model="agno-decision-support",
        metadata={
            "decision_type": "exploration_exploitation",
            "context": "adaptive_strategy",
            "framework": "agno",
            "decision_weight": 0.85
        }
    )
    print(f"✅ Decision process recorded: {decision_chat_id[:8]}...")
    
    # Example 8: AGNO memory insights
    print("\n💡 Example 8: AGNO framework insights...")
    
    # Get conversation history for analysis
    recent_conversations = agno_memory.get_conversation_history(limit=10)
    
    agno_insights = {
        "total_conversations": len(recent_conversations),
        "goal_oriented_sessions": len([c for c in recent_conversations if "agno" in str(c.get('metadata', {}))]),
        "optimization_strategies": len([c for c in recent_conversations if "optimization" in str(c.get('metadata', {}))]),
        "decision_points": len([c for c in recent_conversations if "decision" in str(c.get('metadata', {}))]),
        "framework_usage": "AGNO integration active"
    }
    
    print("AGNO Framework Insights:")
    for key, value in agno_insights.items():
        print(f"  📊 {key.replace('_', ' ').title()}: {value}")
    
    # Clean up
    agno_memory.disable()
    print("\n🔒 AGNO framework integration disabled")
    
    print("\n💡 AGNO Integration Benefits:")
    print("   ✅ Goal-oriented memory storage")
    print("   ✅ Adaptive strategy retrieval")
    print("   ✅ Navigation decision support")
    print("   ✅ Optimization pattern recognition")
    print("   ✅ Multi-objective conflict resolution")
    print("   ✅ Exploration vs exploitation balance")
    
    print("\n🎉 AGNO framework integration example completed!")
    print("💾 Check 'agno_memory.db' for framework-specific memories")
    print("🚀 Ready for production AGNO agent deployment!")

if __name__ == "__main__":
    main()
