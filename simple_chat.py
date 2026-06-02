import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types


MODEL_NAME = "gemini-2.5-flash"
MAX_TURNS = 20


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

    # Keep explicit history so each request always includes prior turns.
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
            )

            response_text_parts: list[str] = []
            async for chunk in stream:
                if chunk.text:
                    response_text_parts.append(chunk.text)
                    print(chunk.text, end="", flush=True)

            assistant_text = "".join(response_text_parts).strip()
            if assistant_text:
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
