import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from restaurant_tools import MenuItem, list_menu, search_menu


MODEL_NAME = "gemini-2.5-flash"
MAX_TURNS = 20


def list_menu_tool() -> list[MenuItem]:
    """Return all restaurant menu items with prices."""
    return list_menu()


def search_menu_tool(keyword: str) -> list[MenuItem]:
    """Search menu items by keyword (case-insensitive)."""
    return search_menu(keyword)


def trim_history(history: list[types.Content], max_turns: int) -> list[types.Content]:
    """Keep only the latest N turns worth of content messages."""
    # Tool calling may add extra content entries (tool call + tool response).
    max_messages = max_turns * 6
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

    # Add personality and tool usage guidance as system instruction.
    system_prompt = """
        You are a helpful and friendly restaurant assistant.
        Use available tools when menu lookup is needed.
        Keep answers concise and clear.
    """
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[list_menu_tool, search_menu_tool],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=5
        ),
    )

    # Keep explicit history so each request includes prior turns.
    history: list[types.Content] = []

    print("🤖 Gemini Chat CLI")
    print("Type 'exit' or 'quit' to end the chat\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            print("\nGemini: ", end="", flush=True)
            user_content = types.Content(
                role="user", parts=[types.Part.from_text(text=user_input)]
            )
            request_contents = [*history, user_content]

            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=request_contents,
                config=config,
            )

            assistant_text = (response.text or "").strip()
            if assistant_text:
                print(assistant_text, end="", flush=True)

            if response.automatic_function_calling_history:
                history = trim_history(
                    response.automatic_function_calling_history, MAX_TURNS
                )
            elif response.candidates and response.candidates[0].content:
                history.extend([user_content, response.candidates[0].content])
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
