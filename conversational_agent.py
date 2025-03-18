import os
import json
import time
import csv
import requests
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use GROQ model server (only GROQ is supported)
API_KEY = os.getenv('GROQ_API_KEY')
BASE_URL = os.getenv('GROQ_BASE_URL')
LLM_MODEL = os.getenv('GROQ_MODEL')

# Initialize the OpenAI client with the selected API key and base URL
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Weather API key remains separate
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

def get_current_weather(location):
    """Get the current weather for a location."""
    api_key = WEATHER_API_KEY
    url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}&aqi=no"
    response = requests.get(url)
    data = response.json()
    if "error" in data:
        return f"Error: {data['error']['message']}"
    weather_info = data["current"]
    result = {
        "location": data["location"]["name"],
        "temperature_c": weather_info["temp_c"],
        "temperature_f": weather_info["temp_f"],
        "condition": weather_info["condition"]["text"],
        "humidity": weather_info["humidity"],
        "wind_kph": weather_info["wind_kph"]
    }
    return json.dumps(result)

def get_weather_forecast(location, days=3):
    """Get a weather forecast for a location for a specified number of days."""
    api_key = WEATHER_API_KEY
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days={days}&aqi=no"
    response = requests.get(url)
    data = response.json()
    if "error" in data:
        return f"Error: {data['error']['message']}"
    forecast_days = data["forecast"]["forecastday"]
    forecast_data = []
    for day in forecast_days:
        forecast_data.append({
            "date": day["date"],
            "max_temp_c": day["day"]["maxtemp_c"],
            "min_temp_c": day["day"]["mintemp_c"],
            "condition": day["day"]["condition"]["text"],
            "chance_of_rain": day["day"]["daily_chance_of_rain"]
        })
    result = {
        "location": data["location"]["name"],
        "forecast": forecast_data
    }
    return json.dumps(result)

weather_tools = [
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
                        "description": "The city and state (e.g., San Francisco, CA) or country (e.g., France)"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get the weather forecast for a location for a specific number of days",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state (e.g., San Francisco, CA) or country (e.g., France)"
                    },
                    "days": {
                        "type": "integer",
                        "description": "The number of days to forecast (1-10)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["location", "days"]
            }
        }
    }
]

available_functions = {
    "get_current_weather": get_current_weather,
    "get_weather_forecast": get_weather_forecast
}

def process_messages(client, messages, tools=None, available_functions=None):
    tools = tools or []
    available_functions = available_functions or {}
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=tools,
    )
    # Convert the response message to a dictionary using model_dump()
    response_message = response.choices[0].message.model_dump()
    messages.append(response_message)
    
    # Check if the API returned structured tool_calls.
    if response_message.get("tool_calls"):
        for tool_call in response_message["tool_calls"]:
            function_name = tool_call["function"]["name"]
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call["function"]["arguments"])
            function_response = function_to_call(**function_args)
            messages.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
    else:
        # If no "tool_calls" field, check if the content is a function call in XML-like format.
        content = response_message.get("content", "")
        pattern = r'<request><function name="(.*?)" arguments=\'(.*?)\' /></request>'
        match = re.search(pattern, content)
        if match:
            function_name = match.group(1)
            arguments_str = match.group(2)
            function_to_call = available_functions.get(function_name)
            if function_to_call:
                function_args = json.loads(arguments_str)
                function_response = function_to_call(**function_args)
                messages.append({
                    "tool_call_id": "manual",
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
    return messages

def run_conversation(client, system_message="You are a helpful weather assistant.", tools=None):
    messages = [{"role": "system", "content": system_message}]
    print("Weather Assistant: Hello! I can help you with weather information. Ask me about the weather anywhere!")
    print("(Type 'exit' to end the conversation)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nWeather Assistant: Goodbye! Have a great day!")
            break
        messages.append({"role": "user", "content": user_input})
        messages = process_messages(client, messages, tools=tools, available_functions=available_functions)
        # Look for the last tool response or assistant message
        last_message = messages[-1]
        if last_message.get("role") == "assistant" and last_message.get("content"):
            print(f"\nWeather Assistant: {last_message.get('content')}\n")
        elif last_message.get("role") == "tool" and last_message.get("content"):
            print(f"\nWeather Assistant (Tool Response): {last_message.get('content')}\n")
    return messages

def calculator(expression):
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a mathematical expression",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2+2' or '5*(3+2)')"
                }
            },
            "required": ["expression"]
        }
    }
}

cot_system_message = (
    "You are a helpful assistant that can answer questions about weather and perform calculations. "
    "When responding to complex questions, follow these steps:\n"
    "1. Think step-by-step about what information you need.\n"
    "2. Break down the problem into smaller parts.\n"
    "3. Use the appropriate tools to gather information (weather data, calculator).\n"
    "4. Explain your reasoning clearly.\n"
    "5. Provide a clear final answer."
)

cot_tools = weather_tools + [calculator_tool]
available_functions["calculator"] = calculator

def web_search(query):
    search_results = {
        "weather forecast": "Weather forecasts predict atmospheric conditions, including temperature, precipitation, and wind, for a given location and time.",
        "temperature conversion": "To convert Celsius to Fahrenheit: multiply by 9/5 and add 32. Reverse for Fahrenheit to Celsius.",
        "climate change": "Climate change refers to significant, long-term changes in global temperatures and weather patterns.",
        "severe weather": "Severe weather includes phenomena like tornadoes, hurricanes, and heavy snowfall that can cause damage."
    }
    best_match = None
    best_match_score = 0
    words_in_query = set(query.lower().split())
    for key in search_results:
        words_in_key = set(key.lower().split())
        match_score = len(words_in_query.intersection(words_in_key))
        if match_score > best_match_score:
            best_match = key
            best_match_score = match_score
    if best_match_score > 0:
        result = {"query": query, "result": search_results[best_match]}
    else:
        result = {"query": query, "result": "No relevant information found."}
    return json.dumps(result)

search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search for information on the web",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
}

react_tools = cot_tools + [search_tool]
available_functions["web_search"] = web_search

react_system_message = (
    "You are a helpful weather and information assistant that uses the ReAct approach to solve problems. "
    "When responding to questions, follow this pattern:\n"
    "1. Thought: Think about what you need to know and the steps to take.\n"
    "2. Action: Use a tool to gather information (weather data, search, calculator).\n"
    "3. Observation: Review the information obtained.\n"
    "4. Repeat as needed until you have enough information.\n"
    "5. Final Answer: Provide your clear final response based on all observations."
)

def comparative_evaluation(query):
    agents = {
        "Basic": {
            "system_message": "You are a helpful weather assistant.",
            "tools": weather_tools
        },
        "Chain of Thought": {
            "system_message": cot_system_message,
            "tools": cot_tools
        },
        "ReAct": {
            "system_message": react_system_message,
            "tools": react_tools
        }
    }
    responses = {}
    print("\n--- Comparative Evaluation ---")
    for agent_type, config in agents.items():
        print(f"\nRunning {agent_type} agent...")
        messages = [{"role": "system", "content": config["system_message"]}]
        messages.append({"role": "user", "content": query})
        messages = process_messages(client, messages, tools=config["tools"], available_functions=available_functions)
        last_message = messages[-1]
        responses[agent_type] = last_message.get("content", "[No response]")
    
    print("\n--- Agent Responses ---")
    for agent_type, resp in responses.items():
        print(f"{agent_type} Agent Response: {resp}\n")
    
    ratings = {}
    for agent_type in agents.keys():
        while True:
            try:
                rating = int(input(f"Please rate the {agent_type} agent's response (1-5): "))
                if 1 <= rating <= 5:
                    ratings[agent_type] = rating
                    break
                else:
                    print("Rating must be between 1 and 5.")
            except ValueError:
                print("Please enter a valid integer.")
    
    filename = "comparative_evaluation_results.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as csvfile:
        fieldnames = ["query", "Basic_response", "CoT_response", "ReAct_response", "Basic_rating", "CoT_rating", "ReAct_rating"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "query": query,
            "Basic_response": responses["Basic"],
            "CoT_response": responses["Chain of Thought"],
            "ReAct_response": responses["ReAct"],
            "Basic_rating": ratings["Basic"],
            "CoT_rating": ratings["Chain of Thought"],
            "ReAct_rating": ratings["ReAct"]
        })
    print(f"\nEvaluation results saved to {filename}.")

if __name__ == "__main__":
    print("Choose an agent type:")
    print("1: Basic Weather Assistant")
    print("2: Chain-of-Thought Assistant")
    print("3: ReAct Assistant")
    print("4: Comparative Evaluation (Bonus)")
    choice = input("Enter 1, 2, 3 or 4: ").strip()

    if choice == "1":
        system_message = "You are a helpful weather assistant."
        tools = weather_tools
        run_conversation(client, system_message=system_message, tools=tools)
    elif choice == "2":
        system_message = cot_system_message
        tools = cot_tools
        run_conversation(client, system_message=system_message, tools=tools)
    elif choice == "3":
        system_message = react_system_message
        tools = react_tools
        run_conversation(client, system_message=system_message, tools=tools)
    elif choice == "4":
        query = input("Enter a single query for evaluation: ")
        comparative_evaluation(query)
    else:
        print("Invalid choice. Defaulting to Basic Weather Assistant.")
        system_message = "You are a helpful weather assistant."
        tools = weather_tools
        run_conversation(client, system_message=system_message, tools=tools)
