"""
Level 2 - Example 2: Function Calling

This example demonstrates function calling (tool use), allowing LLMs to
interact with external tools and APIs.

Learning Goals:
- Define functions/tools for LLMs to use
- Implement function calling workflow
- Handle function results
- Build practical applications with tools
"""

import json
from datetime import datetime
from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.core.base import Message


# Define example functions
def get_current_weather(location: str, unit: str = "fahrenheit") -> dict:
    """
    Get the current weather in a given location.

    Args:
        location: City and state, e.g., "San Francisco, CA"
        unit: Temperature unit (celsius or fahrenheit)

    Returns:
        Weather information
    """
    # Simulated weather data
    weather_data = {
        "San Francisco, CA": {"temperature": 72, "condition": "sunny"},
        "New York, NY": {"temperature": 65, "condition": "cloudy"},
        "London, UK": {"temperature": 55, "condition": "rainy"},
    }

    data = weather_data.get(location, {"temperature": 70, "condition": "partly cloudy"})

    return {
        "location": location,
        "temperature": data["temperature"],
        "unit": unit,
        "condition": data["condition"],
        "timestamp": datetime.now().isoformat()
    }


def calculate_mortgage(principal: float, annual_rate: float, years: int) -> dict:
    """
    Calculate monthly mortgage payment.

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (as percentage, e.g., 5.5)
        years: Loan term in years

    Returns:
        Mortgage calculation results
    """
    monthly_rate = (annual_rate / 100) / 12
    num_payments = years * 12

    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                         ((1 + monthly_rate)**num_payments - 1)

    total_payment = monthly_payment * num_payments
    total_interest = total_payment - principal

    return {
        "principal": principal,
        "annual_rate": annual_rate,
        "years": years,
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2)
    }


def search_database(query: str, category: str = "all") -> list:
    """
    Search a simulated database.

    Args:
        query: Search query
        category: Category to search in

    Returns:
        Search results
    """
    # Simulated database
    database = {
        "products": [
            {"id": 1, "name": "Laptop", "price": 999, "category": "electronics"},
            {"id": 2, "name": "Phone", "price": 699, "category": "electronics"},
            {"id": 3, "name": "Desk", "price": 299, "category": "furniture"},
        ],
        "articles": [
            {"id": 1, "title": "AI in 2025", "category": "tech"},
            {"id": 2, "title": "Python Best Practices", "category": "programming"},
        ]
    }

    results = []
    for cat, items in database.items():
        if category == "all" or category == cat:
            for item in items:
                item_str = json.dumps(item).lower()
                if query.lower() in item_str:
                    results.append({"category": cat, **item})

    return results


# Define tool schemas for OpenAI
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_mortgage",
            "description": "Calculate monthly mortgage payment",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {
                        "type": "number",
                        "description": "Loan amount in dollars"
                    },
                    "annual_rate": {
                        "type": "number",
                        "description": "Annual interest rate as percentage (e.g., 5.5)"
                    },
                    "years": {
                        "type": "integer",
                        "description": "Loan term in years"
                    }
                },
                "required": ["principal", "annual_rate", "years"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "Search a database for products or articles",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["all", "products", "articles"],
                        "description": "Category to search in"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# Function registry
FUNCTION_MAP = {
    "get_current_weather": get_current_weather,
    "calculate_mortgage": calculate_mortgage,
    "search_database": search_database,
}


def execute_function_call(function_name: str, arguments: dict) -> str:
    """Execute a function call and return the result."""
    function = FUNCTION_MAP.get(function_name)
    if not function:
        return json.dumps({"error": f"Function {function_name} not found"})

    try:
        result = function(**arguments)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def chat_with_tools(user_message: str) -> str:
    """
    Chat with function calling enabled.

    Args:
        user_message: User's message

    Returns:
        Assistant's response
    """
    client = OpenAIClient()
    messages = [Message(role="user", content=user_message)]

    # Initial request with tools
    response = client.chat(messages, tools=TOOLS, tool_choice="auto")

    # Check if function calling is needed
    if hasattr(response, 'tool_calls') and response.tool_calls:
        # Function calling loop
        for tool_call in response.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"\n🔧 Calling function: {function_name}")
            print(f"   Arguments: {arguments}")

            # Execute function
            function_result = execute_function_call(function_name, arguments)
            print(f"   Result: {function_result}")

            # Add function result to messages
            messages.append(Message(
                role="assistant",
                content=response.content or "",
                tool_calls=[tool_call]
            ))
            messages.append(Message(
                role="tool",
                content=function_result,
                tool_call_id=tool_call.id
            ))

        # Get final response
        final_response = client.chat(messages)
        return final_response.content

    return response.content


def example_weather_tool():
    """Example using weather tool."""
    print("\n" + "=" * 50)
    print("1. Weather Tool Example")
    print("=" * 50)

    query = "What's the weather like in San Francisco?"
    print(f"\n❓ User: {query}")
    print("\n🤖 Assistant:")
    print("-" * 50)

    response = chat_with_tools(query)
    print(f"\n{response}")


def example_calculator_tool():
    """Example using calculator tool."""
    print("\n" + "=" * 50)
    print("2. Mortgage Calculator Tool")
    print("=" * 50)

    query = "Calculate monthly payment for a $300,000 loan at 6.5% interest for 30 years"
    print(f"\n❓ User: {query}")
    print("\n🤖 Assistant:")
    print("-" * 50)

    response = chat_with_tools(query)
    print(f"\n{response}")


def example_search_tool():
    """Example using search tool."""
    print("\n" + "=" * 50)
    print("3. Database Search Tool")
    print("=" * 50)

    query = "Find me electronics products"
    print(f"\n❓ User: {query}")
    print("\n🤖 Assistant:")
    print("-" * 50)

    response = chat_with_tools(query)
    print(f"\n{response}")


def example_multi_step():
    """Example with multiple function calls."""
    print("\n" + "=" * 50)
    print("4. Multi-Step Function Calling")
    print("=" * 50)

    query = "What's the weather in New York and also search for laptop products"
    print(f"\n❓ User: {query}")
    print("\n🤖 Assistant:")
    print("-" * 50)

    response = chat_with_tools(query)
    print(f"\n{response}")


def main():
    """Main function demonstrating function calling."""
    print("=" * 50)
    print("Level 2 - Example 2: Function Calling")
    print("=" * 50)

    example_weather_tool()
    example_calculator_tool()
    example_search_tool()
    example_multi_step()

    print("\n" + "=" * 50)
    print("✓ All examples completed!")
    print("\nKey Takeaways:")
    print("- Function calling allows LLMs to use external tools")
    print("- Define clear function schemas for better results")
    print("- Handle function execution and return results")
    print("- Can chain multiple function calls together")


if __name__ == "__main__":
    main()
