import json
import httpx


BASE_URL = "http://127.0.0.1:8000"


def main():

    with httpx.Client(timeout=180.0) as client:

        response = client.get(
            f"{BASE_URL}/api/chat/conversations"
        )

        response.raise_for_status()

        conversations = response.json()

        if not conversations:

            print("Create a conversation first.")
            return

        conversation_id = conversations[0]["id"]

        question = input(
            "Enter a document-related question: "
        ).strip()

        if not question:
            return

        print("\n" + "=" * 60)
        print("DOCUMIND AI STREAMING TEST")
        print("=" * 60)

        answer_parts = []
        completed = False

        with client.stream(
            "POST",
            (
                f"{BASE_URL}/api/chat/conversations/"
                f"{conversation_id}/stream"
            ),
            json={
                "question": question
            }
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines():

                if not line.startswith("data:"):
                    continue

                event = json.loads(
                    line[5:].strip()
                )

                event_type = event.get("type")

                if event_type == "sources":

                    print("\nRETRIEVED SOURCES:")

                    for source in event["sources"]:

                        print(
                            source["filename"],
                            source["relevance_score"]
                        )

                    print("\nAI RESPONSE:\n")

                elif event_type == "token":

                    token = event["content"]

                    answer_parts.append(token)

                    print(
                        token,
                        end="",
                        flush=True
                    )

                elif event_type == "done":

                    completed = True

                    complete_answer = "".join(
                        answer_parts
                    )

                    saved_answer = event["message"]["content"]

                    print("\n\nSTREAMING COMPLETED")

                    print(
                        "Response characters:",
                        len(complete_answer)
                    )

                    print(
                        "Saved response matches:",
                        complete_answer == saved_answer
                    )

                elif event_type == "error":

                    print(
                        "\nERROR:",
                        event["message"]
                    )

        print("\nCompleted:", completed)

        print("\n" + "=" * 60)

        print("COMPLETE RECONSTRUCTED RESPONSE")

        print("=" * 60)

        print("".join(answer_parts))


if __name__ == "__main__":
    main()