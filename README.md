# Conversational Agent with Tool Use and Reasoning Techniques

This project implements a conversational agent capable of retrieving weather data, performing calculations, and simulating web searches. The agent supports three reasoning strategies:
- **Basic Weather Assistant:** Provides weather information using external APIs.
- **Chain-of-Thought (CoT) Assistant:** Breaks down complex queries step-by-step and uses a calculator when needed.
- **ReAct Assistant:** Alternates between reasoning and taking actions (tool use) to solve problems iteratively.

## Overview

The conversational agent is built on top of the OpenAI API and integrates various tools:
- **Weather Tools:** Retrieve current weather conditions and forecasts using WeatherAPI.
- **Calculator Tool:** Evaluates mathematical expressions for computations.
- **Search Tool:** Simulates web search functionality to provide additional information.
- **Comparative Evaluation:** (Bonus) Allows users to compare responses from all three agents, rate them, and save the results for later analysis.

This implementation explores different reasoning paradigms such as Chain of Thought and ReAct to improve problem-solving and clarity in responses.

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Install Dependencies:**
   Create a virtual environment and install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the repository root with your variables

4. **Run the Agent:**
   Execute the Python script:
   ```bash
   python conversational_agent.py
   ```

## Usage

When you run the script, you will be prompted to choose an agent type:
- **1:** Basic Weather Assistant
- **2:** Chain-of-Thought Assistant
- **3:** ReAct Assistant
- **4:** Comparative Evaluation (Bonus)

For options 1–3, simply follow the on-screen prompts to ask about weather conditions, forecasts, or perform calculations. The agent will handle tool calls automatically and provide responses accordingly.

For option 4, you can enter a single query that will be processed by all three agent types. You will then be asked to rate each response on a scale of 1–5, and the results will be saved in a CSV file (`comparative_evaluation_results.csv`) for further analysis.

## Features & Implementation Details

- **Tool Integration:**  
  The agent defines and registers multiple tools (weather retrieval, calculator, search) using JSON schemas. These tools allow the agent to gather real-time data and perform calculations as needed.
  
- **Reasoning Paradigms:**  
  - **Chain-of-Thought (CoT):** Encourages the agent to think through complex queries step-by-step.  
  - **ReAct:** Enables the agent to alternate between reasoning (thoughts) and actions (tool usage), improving the clarity and accuracy of its final answer.

- **Comparative Evaluation:**  
  This bonus feature allows you to compare the responses of all three agents side by side. It provides a simple mechanism to rate and log the performance of each agent type, facilitating further analysis of their effectiveness.

## Examples

- **Basic Query:**  
  *User:* "What's the current weather in San Francisco?"  
  *Assistant:* Retrieves and displays current weather data from WeatherAPI.

- **Complex Query (Chain-of-Thought):**  
  *User:* "What is the temperature difference between New York and London today?"  
  *Assistant:* Breaks down the query, retrieves weather data for both cities, uses the calculator tool to compute the difference, and explains the reasoning.

- **ReAct Query:**  
  *User:* "Can you tell me about severe weather conditions and calculate the probability of rain in Paris for the next 3 days?"  
  *Assistant:* Alternates between fetching weather data, simulating a search for additional information on severe weather, and performing any necessary calculations.


