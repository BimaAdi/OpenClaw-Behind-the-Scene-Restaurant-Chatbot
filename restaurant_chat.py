import asyncio
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from restaurant_tools import format_menu, list_menu, search_menu


MODEL_NAME = "gemini-2.5-flash"
MAX_TURNS = 20


def extract_tool_call(text: str) -> str | None:
    strict_match = re.search(
        r"TOOL_CALL:\s*(list_menu\(\)|search_menu\(([^)]*)\))",
        text,
    )
    if strict_match:
        return strict_match.group(1).strip()

    loose_match = re.search(r"\b(list_menu\(\)|search_menu\(([^)]*)\))", text)
    if loose_match:
        return loose_match.group(1).strip()

    return None


def execute_tool_call(tool_call: str) -> str:
    if tool_call == "list_menu()":
        return format_menu(list_menu())

    search_match = re.fullmatch(r"search_menu\((.*)\)", tool_call)
    if search_match:
        keyword = search_match.group(1).strip().strip('"').strip("'")
        return format_menu(search_menu(keyword))

    return f"Unsupported tool call: {tool_call}"


def trim_history(history: list[types.Content], max_turns: int) -> list[types.Content]:
    """Keep only the latest N user/model turn pairs."""
    max_messages = max_turns * 2
    if len(history) <= max_messages:
        return history
    return history[-max_messages:]


async def main():
    """Simple CLI chat app using Gemini."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set your API key: export GEMINI_API_KEY='your-api-key'")
        return

    # Create a client
    client = genai.Client(api_key=api_key)

    # Add personality and strict tool-call format to the system prompt
    system_prompt = """
        You are a helpful and friendly restaurant assistant.

        You can ask for tools using these exact strings:
        - TOOL_CALL: list_menu()
        - TOOL_CALL: search_menu("keyword")

        Rules:
        - If you need menu data, only output one TOOL_CALL line.
        - If you already have enough data, answer normally and do not output TOOL_CALL.
        - After receiving a TOOL_RESULT message, use it to answer the user.
    """

    # Keep explicit history so each request includes prior turns.
    history: list[types.Content] = []

    print("🤖 Gemini Chat CLI")
    print("Type 'exit' or 'quit' to end the chat\n")

    pending_user_prompt: str | None = None

    while True:
        try:
            if pending_user_prompt:
                user_input = pending_user_prompt
                pending_user_prompt = None
                print(f"Tools: {user_input}")
            else:
                user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            llm_input = user_input
            if extract_tool_call(user_input):
                tool_result = execute_tool_call(user_input)
                print(f"Tool Result:\n{tool_result}\n")
                llm_input = f"TOOL_RESULT\ntool_call={user_input}\n{tool_result}"

            # Stream message chunks from Gemini as they arrive.
            print("\nGemini: ", end="", flush=True)
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=llm_input)],
            )
            request_contents = [*history, user_content]

            stream = await client.aio.models.generate_content_stream(
                model=MODEL_NAME,
                contents=request_contents,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )

            response_text_parts: list[str] = []
            async for chunk in stream:
                if chunk.text:
                    response_text_parts.append(chunk.text)
                    print(chunk.text, end="", flush=True)

            # Check whether the model requested a tool call.
            assistant_text = "".join(response_text_parts).strip()
            if assistant_text:
                tool_call = extract_tool_call(assistant_text)
                if tool_call:
                    pending_user_prompt = tool_call
                    print(f"\n[Detected tool request: {tool_call}]", end="", flush=True)

                model_content = types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=assistant_text)],
                )
                history.extend([user_content, model_content])
                history = trim_history(history, MAX_TURNS)
            print("\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

    await client.aio.aclose()


if __name__ == "__main__":
    asyncio.run(main())
