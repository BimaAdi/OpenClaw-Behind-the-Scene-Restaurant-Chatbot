import asyncio
import os
from typing import TypedDict
from dotenv import load_dotenv
from google import genai


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

    # Create a chat session
    chat = client.aio.chats.create(model="gemini-3.5-flash")

    # Add personality and menu command to the system prompt
    system_prompt = """
        You are a helpful and friendly restaurant assistant.
        if you want to get list of menu just call ```list_menu()``` on prompt
        if you want to search menu just call ```search_menu(keyword)``` on prompt with keyword as parameter
    """
    stream = await chat.send_message_stream(system_prompt)
    async for chunk in stream:
        pass  # Consume the system prompt response to set the context

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
            stream = await chat.send_message_stream(user_input)
            # extra_prompt = ""
            async for chunk in stream:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    # check is chunk.text contains list_menu() call and respond with menu if it does
                    if "list_menu()" in chunk.text:
                        menu_response = "\n".join(
                            [f"{item['menu']}: {item['price']}" for item in list_menu()]
                        )
                        print(f"\n{menu_response}", end="", flush=True)
                    if "search_menu(" in chunk.text:
                        # extract keyword from search_menu() call
                        start_index = chunk.text.find("search_menu(") + len(
                            "search_menu("
                        )
                        end_index = chunk.text.find(")", start_index)
                        keyword = (
                            chunk.text[start_index:end_index].strip('"').strip("'")
                        )
                        search_response = "\n".join(
                            [
                                f"{item['menu']}: {item['price']}"
                                for item in search_menu(keyword)
                            ]
                        )
                        print(f"\n{search_response}", end="", flush=True)
            print("\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

    await client.aio.aclose()


if __name__ == "__main__":
    asyncio.run(main())
