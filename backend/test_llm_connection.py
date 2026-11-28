import asyncio

from app.services.llm_service import llm_service


async def main():

    print("=" * 60)
    print("DOCUMIND AI - LLM INTEGRATION TEST")
    print("=" * 60)

    health = await llm_service.health()

    print("\nAI SERVER STATUS:")
    print(health)

    if not health["connected"]:
        return

    messages = [
        {
            "role": "system",
            "content": "You are DocuMind AI."
        },
        {
            "role": "user",
            "content": "Explain document analysis in two sentences."
        }
    ]

    print("\nNORMAL RESPONSE:")

    answer = await llm_service.generate(
        messages,
        max_tokens=150
    )

    print(answer)

    print("\nSTREAMING RESPONSE:")

    async for token in llm_service.stream(
        messages,
        max_tokens=150
    ):

        print(token, end="", flush=True)

    print("\n")
    print("=" * 60)
    print("LLM INTEGRATION TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())