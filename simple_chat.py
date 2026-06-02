import os
import asyncio
from dotenv import load_dotenv
from google import genai


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
            async for chunk in stream:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

    await client.aio.aclose()


if __name__ == "__main__":
    asyncio.run(main())
