#!/usr/bin/env python3
"""
Smart Shopping Experience Demo - Azure AI Foundry + Memori Integration

A real-world demonstration of an AI-powered shopping assistant that remembers
customer preferences, purchase history, and provides personalized recommendations.

This demo showcases:
- Customer preference learning
- Purchase history tracking
- Personalized product recommendations
- Budget-aware suggestions
- Seasonal shopping assistance
- Gift recommendation based on relationships

Requirements:
- pip install memorisdk openai azure-ai-projects azure-identity python-dotenv
- Set PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME in environment or .env file
- Configure Azure authentication (Azure CLI login or managed identity)

Usage:
    python smart_shopping_demo.py
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from azure.ai.agents.models import FunctionTool
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from memori import Memori, create_memory_tool

# Constants
DATABASE_PATH = "sqlite:///smart_shopping_memory.db"
NAMESPACE = "smart_shopping_assistant"

# Mock product database
PRODUCT_CATALOG = {
    "electronics": [
        {
            "id": "iphone15",
            "name": "iPhone 15 Pro",
            "price": 999,
            "rating": 4.8,
            "category": "smartphone",
        },
        {
            "id": "macbook",
            "name": "MacBook Air M2",
            "price": 1199,
            "rating": 4.9,
            "category": "laptop",
        },
        {
            "id": "airpods",
            "name": "AirPods Pro",
            "price": 249,
            "rating": 4.7,
            "category": "audio",
        },
        {
            "id": "ipad",
            "name": "iPad Air",
            "price": 599,
            "rating": 4.6,
            "category": "tablet",
        },
    ],
    "clothing": [
        {
            "id": "nike_shoes",
            "name": "Nike Air Max",
            "price": 120,
            "rating": 4.5,
            "category": "footwear",
        },
        {
            "id": "levi_jeans",
            "name": "Levi's 501 Jeans",
            "price": 80,
            "rating": 4.4,
            "category": "pants",
        },
        {
            "id": "sweater",
            "name": "Cashmere Sweater",
            "price": 150,
            "rating": 4.6,
            "category": "tops",
        },
    ],
    "home": [
        {
            "id": "coffee_maker",
            "name": "Breville Coffee Maker",
            "price": 300,
            "rating": 4.7,
            "category": "kitchen",
        },
        {
            "id": "vacuum",
            "name": "Dyson V15",
            "price": 450,
            "rating": 4.8,
            "category": "cleaning",
        },
        {
            "id": "mattress",
            "name": "Memory Foam Mattress",
            "price": 800,
            "rating": 4.5,
            "category": "bedroom",
        },
    ],
    "books": [
        {
            "id": "ai_book",
            "name": "AI for Everyone",
            "price": 25,
            "rating": 4.3,
            "category": "technology",
        },
        {
            "id": "cookbook",
            "name": "Mediterranean Cookbook",
            "price": 30,
            "rating": 4.6,
            "category": "cooking",
        },
    ],
}


@dataclass
class Config:
    """Configuration for Azure AI Foundry integration"""

    project_endpoint: str
    model_name: str

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        load_dotenv()

        project_endpoint = os.getenv("PROJECT_ENDPOINT")
        model_name = os.getenv("MODEL_DEPLOYMENT_NAME")

        if not project_endpoint:
            print("❌ Error: PROJECT_ENDPOINT not found in environment variables")
            print("Please set: export PROJECT_ENDPOINT='your-project-endpoint-here'")
            sys.exit(1)

        if not model_name:
            print("❌ Error: MODEL_DEPLOYMENT_NAME not found in environment variables")
            print(
                "Please set: export MODEL_DEPLOYMENT_NAME='your-model-deployment-name'"
            )
            sys.exit(1)

        return cls(project_endpoint=project_endpoint, model_name=model_name)


class SmartShoppingAssistant:
    """AI Shopping Assistant with memory capabilities"""

    def __init__(self, config: Config):
        self.config = config
        self.memory_system = self._setup_memory()
        self.memory_tool = create_memory_tool(self.memory_system)
        self.client = AIProjectClient(
            endpoint=config.project_endpoint, credential=DefaultAzureCredential()
        )
        self.functions = FunctionTool(
            functions={
                self.search_memory,
                self.search_products,
                self.get_product_details,
            }
        )
        self.agent = None
        self.thread = None

    def _setup_memory(self) -> Memori:
        """Initialize and enable memory system"""
        print("🧠 Initializing Smart Shopping Memory System...")
        memory = Memori(
            database_connect=DATABASE_PATH,
            conscious_ingest=True,
            verbose=False,
            namespace=NAMESPACE,
        )
        memory.enable()
        return memory

    def search_memory(self, query: str) -> str:
        """Search customer's shopping history and preferences"""
        try:
            if not query.strip():
                return json.dumps({"error": "Please provide a search query"})

            result = self.memory_tool.execute(query=query.strip())
            memory_result = (
                str(result) if result else "No relevant shopping history found"
            )

            return json.dumps(
                {
                    "shopping_history": memory_result,
                    "search_query": query,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            return json.dumps({"error": f"Memory search error: {str(e)}"})

    def search_products(
        self,
        category: str,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
    ) -> str:
        """Search products by category with optional filters"""
        try:
            products = []

            if category.lower() in PRODUCT_CATALOG:
                category_products = PRODUCT_CATALOG[category.lower()]

                for product in category_products:
                    # Apply price filter
                    if max_price and product["price"] > max_price:
                        continue

                    # Apply rating filter
                    if min_rating and product["rating"] < min_rating:
                        continue

                    products.append(product)
            else:
                # Search across all categories
                for cat_products in PRODUCT_CATALOG.values():
                    for product in cat_products:
                        if (
                            category.lower() in product["name"].lower()
                            or category.lower() in product["category"].lower()
                        ):
                            # Apply filters
                            if max_price and product["price"] > max_price:
                                continue
                            if min_rating and product["rating"] < min_rating:
                                continue

                            products.append(product)

            return json.dumps(
                {
                    "products": products,
                    "total_found": len(products),
                    "filters_applied": {
                        "category": category,
                        "max_price": max_price,
                        "min_rating": min_rating,
                    },
                }
            )

        except Exception as e:
            return json.dumps({"error": f"Product search error: {str(e)}"})

    def get_product_details(self, product_id: str) -> str:
        """Get detailed information about a specific product"""
        try:
            for category_products in PRODUCT_CATALOG.values():
                for product in category_products:
                    if product["id"] == product_id:
                        return json.dumps(
                            {
                                "product": product,
                                "availability": "In Stock",
                                "shipping": "Free 2-day shipping",
                                "return_policy": "30-day return policy",
                            }
                        )

            return json.dumps({"error": f"Product {product_id} not found"})

        except Exception as e:
            return json.dumps({"error": f"Product details error: {str(e)}"})

    def _handle_function_calls(self, tool_calls) -> List[Dict]:
        """Handle function calls from the agent"""
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            try:
                if function_name == "search_memory":
                    output = self.search_memory(function_args.get("query", ""))
                elif function_name == "search_products":
                    output = self.search_products(
                        category=function_args.get("category", ""),
                        max_price=function_args.get("max_price"),
                        min_rating=function_args.get("min_rating"),
                    )
                elif function_name == "get_product_details":
                    output = self.get_product_details(
                        function_args.get("product_id", "")
                    )
                else:
                    output = json.dumps({"error": f"Unknown function: {function_name}"})

                tool_outputs.append({"tool_call_id": tool_call.id, "output": output})

            except Exception as e:
                error_output = json.dumps(
                    {"error": f"Function execution error: {str(e)}"}
                )
                tool_outputs.append(
                    {"tool_call_id": tool_call.id, "output": error_output}
                )

        return tool_outputs

    def _extract_response_content(self, messages) -> str:
        """Extract assistant response from messages"""
        for message in messages:
            if message["role"] == "assistant":
                content = message["content"]
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if hasattr(block, "text") and hasattr(block.text, "value"):
                            text_parts.append(block.text.value)
                        elif isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"].get("value", ""))
                    return " ".join(text_parts)
                else:
                    return str(content)
        return ""

    def setup(self):
        """Create agent and thread"""
        print("🛍️ Creating Smart Shopping Assistant...")

        instructions = """You are an advanced AI shopping assistant with memory capabilities. You help customers find products, remember their preferences, track purchase history, and provide personalized recommendations.

Your capabilities:
1. **Memory Search**: Use search_memory to recall customer preferences, past purchases, and shopping history
2. **Product Search**: Use search_products to find products by category with price and rating filters
3. **Product Details**: Use get_product_details to get specific information about products

Guidelines:
1. Always search memory first to understand the customer's preferences and history
2. Provide personalized recommendations based on past interactions
3. Consider budget constraints mentioned by customers
4. Suggest complementary products when appropriate
5. Be helpful, friendly, and knowledgeable about products
6. Remember seasonal preferences and gift occasions
7. Track customer satisfaction and preferences for future interactions

Your goal is to create a personalized shopping experience that feels natural and helpful."""

        self.agent = self.client.agents.create_agent(
            model=self.config.model_name,
            name="smart-shopping-assistant",
            instructions=instructions,
            tools=self.functions.definitions,
        )

        self.thread = self.client.agents.threads.create()

        print(f"✅ Created shopping assistant with ID: {self.agent.id}")
        print(f"✅ Created thread with ID: {self.thread.id}")

    def chat(self, user_input: str) -> str:
        """Process user input and return AI response"""
        try:
            # Send message to thread
            self.client.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_input,
            )

            # Create and process run
            run = self.client.agents.runs.create(
                thread_id=self.thread.id, agent_id=self.agent.id
            )

            # Poll run status
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(1)
                run = self.client.agents.runs.get(
                    thread_id=self.thread.id, run_id=run.id
                )

                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = self._handle_function_calls(tool_calls)

                    self.client.agents.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs,
                    )

            # Get response
            messages = self.client.agents.messages.list(thread_id=self.thread.id)
            assistant_response = self._extract_response_content(messages)

            # Store in memory
            if assistant_response:
                self.memory_system.record_conversation(
                    user_input=user_input, ai_output=assistant_response
                )

            return assistant_response or "I apologize, I couldn't generate a response."

        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

    def cleanup(self):
        """Clean up agent resources"""
        if self.agent:
            try:
                self.client.agents.delete_agent(self.agent.id)
                print(f"🗑️ Deleted shopping assistant {self.agent.id}")
            except Exception as e:
                print(f"Warning: Could not delete agent: {str(e)}")


def run_smart_shopping_demo(assistant: SmartShoppingAssistant):
    """Run predefined smart shopping scenarios"""

    print("\n🛍️ Welcome to Smart Shopping Experience Demo!")
    print("=" * 60)
    print("This demo showcases an AI shopping assistant that learns and remembers")
    print("customer preferences to provide personalized shopping experiences.\n")

    # Predefined shopping scenarios
    scenarios = [
        {
            "title": "🎯 First-time Customer - Electronics Shopping",
            "inputs": [
                "Hi! I'm looking for a new smartphone. I prefer Apple products and my budget is around $1000.",
                "What about accessories for the iPhone? I like high-quality audio products.",
            ],
        },
        {
            "title": "👔 Returning Customer - Work Setup",
            "inputs": [
                "I need to upgrade my work setup. Last time you helped me with a phone, now I need a laptop for development work.",
                "I also need something for video calls and presentations. What do you recommend?",
            ],
        },
        {
            "title": "🎁 Gift Shopping",
            "inputs": [
                "I want to buy a gift for my tech-savvy friend. Based on what I've bought before, what would you suggest?",
                "Actually, let me check what's available for home office setup under $500.",
            ],
        },
        {
            "title": "🏠 Home Improvement Shopping",
            "inputs": [
                "I'm setting up a new apartment. I need kitchen and cleaning appliances. What are the best-rated options?",
                "What about something for the bedroom? I want good quality within reasonable price.",
            ],
        },
        {
            "title": "📚 Personal Interest - Learning",
            "inputs": [
                "I've been buying tech products, but now I want to learn more about AI and cooking. Any book recommendations?",
                "Based on my shopping history, what would be a good next purchase to complement what I already have?",
            ],
        },
    ]

    conversation_count = 0

    for scenario_num, scenario in enumerate(scenarios, 1):
        print(f"\n{'=' * 60}")
        print(f"SCENARIO {scenario_num}: {scenario['title']}")
        print(f"{'=' * 60}")

        for _, user_input in enumerate(scenario["inputs"], 1):
            conversation_count += 1

            print(f"\n👤 Customer: {user_input}")
            print(f"\n🤖 Assistant (Processing... #{conversation_count})")

            response = assistant.chat(user_input)
            print(f"🤖 Assistant: {response}")

            # Add a small delay between conversations for realism
            time.sleep(2)

        # Pause between scenarios
        if scenario_num < len(scenarios):
            print("\n⏱️  Moving to next scenario in 3 seconds...")
            time.sleep(3)

    print(f"\n{'=' * 60}")
    print("📊 DEMO SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Completed {len(scenarios)} shopping scenarios")
    print(f"✅ Processed {conversation_count} customer interactions")
    print(f"✅ Memory database: {DATABASE_PATH}")
    print(f"✅ Namespace: {NAMESPACE}")
    print("\n🎯 Demo Features Showcased:")
    print("- Customer preference learning and memory")
    print("- Personalized product recommendations")
    print("- Budget-aware suggestions")
    print("- Cross-category shopping assistance")
    print("- Gift recommendation based on purchase history")
    print("- Contextual shopping conversations")
    print("\n💾 All interactions are saved in memory for future shopping sessions!")


def main():
    """Main function to run the Smart Shopping Experience demo"""
    print("🚀 Initializing Smart Shopping Experience Demo...")

    try:
        config = Config.from_env()
        assistant = SmartShoppingAssistant(config)

        with assistant.client:
            assistant.setup()
            run_smart_shopping_demo(assistant)

    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
    finally:
        if "assistant" in locals():
            assistant.cleanup()
        print("\n👋 Smart Shopping Demo completed!")


if __name__ == "__main__":
    main()
