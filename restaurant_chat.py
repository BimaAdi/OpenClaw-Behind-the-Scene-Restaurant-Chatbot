import asyncio
import os
import re
from typing import TypedDict
from dotenv import load_dotenv
from google import genai
from google.genai import types


MODEL_NAME = "gemini-2.5-flash"
MAX_TURNS = 20


class MenuItem(TypedDict):
    menu: str
    price: int


MENU: list[MenuItem] = [
    {
        "menu": "Hamburger",
        "price": 5000,
    },
    {
        "menu": "Fries",
        "price": 2000,
    },
    {
        "menu": "Cheese Pizza",
        "price": 12000,
    },
    {
        "menu": "Chicken Wings",
        "price": 9000,
    },
    {
        "menu": "Spaghetti Bolognese",
        "price": 11000,
    },
    {
        "menu": "Caesar Salad",
        "price": 7000,
    },
    {
        "menu": "Grilled Salmon",
        "price": 15000,
    },
    {
        "menu": "Steak",
        "price": 18000,
    },
    {
        "menu": "Iced Tea",
        "price": 3000,
    },
    {
        "menu": "Chocolate Milkshake",
        "price": 4500,
    },
]


def list_menu() -> list[MenuItem]:
    return MENU


def search_menu(keyword: str) -> list[MenuItem]:
    normalized_keyword = keyword.casefold().strip()
    if not normalized_keyword:
        return MENU

    return [item for item in MENU if normalized_keyword in item["menu"].casefold()]


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

    # Add personality and menu command to the system prompt
    system_prompt = """
        You are a helpful and friendly restaurant assistant.
        if you want to get list of menu just call ```list_menu()``` on prompt
        if you want to search menu just call ```search_menu(keyword)``` on prompt with keyword as parameter
    """

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

            # Stream message chunks from Gemini as they arrive.
            print("\nGemini: ", end="", flush=True)
            user_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)],
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

            assistant_text = "".join(response_text_parts).strip()
            if assistant_text:
                rendered_parts = [assistant_text]

                if "list_menu()" in assistant_text:
                    menu_response = "\n".join(
                        [f"{item['menu']}: {item['price']}" for item in list_menu()]
                    )
                    rendered_parts.append(menu_response)
                    print(f"\n{menu_response}", end="", flush=True)

                search_matches = re.findall(r"search_menu\(([^)]*)\)", assistant_text)
                for raw_keyword in search_matches:
                    keyword = raw_keyword.strip().strip('"').strip("'")
                    search_response = "\n".join(
                        [
                            f"{item['menu']}: {item['price']}"
                            for item in search_menu(keyword)
                        ]
                    )
                    rendered_parts.append(search_response)
                    print(f"\n{search_response}", end="", flush=True)

                model_content = types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="\n".join(rendered_parts))],
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
