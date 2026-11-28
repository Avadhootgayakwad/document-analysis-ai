import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import (
    StreamingResponse,
    Response
)

from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal

from app.schemas.chat import (
    ConversationCreate,
    ConversationRename,
    ConversationResponse,
    ConversationDetail,
    ChatRequest,
    ChatResponse,
    MessageResponse
)

from app.services import chat_service

from app.services.llm_service import (
    llm_service,
    LLMServiceError
)


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Chat"]
)


def sse_event(event_type: str, data: dict):

    payload = {
        "type": event_type,
        **data
    }

    return (
        "data: "
        + json.dumps(
            payload,
            ensure_ascii=False
        )
        + "\n\n"
    )


@router.get("/health")
async def ai_health():

    return await llm_service.health()


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201
)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db)
):

    return chat_service.create_conversation(
        title=payload.title,
        document_ids=payload.document_ids,
        db=db
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse]
)
def list_conversations(
    db: Session = Depends(get_db)
):

    return chat_service.list_conversations(db)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail
)
def conversation_details(
    conversation_id: str,
    db: Session = Depends(get_db)
):

    return chat_service.get_conversation(
        conversation_id,
        db
    )


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse
)
def rename_conversation(
    conversation_id: str,
    payload: ConversationRename,
    db: Session = Depends(get_db)
):

    return chat_service.rename_conversation(
        conversation_id,
        payload.title,
        db
    )


@router.delete(
    "/conversations/{conversation_id}"
)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):

    return chat_service.delete_conversation(
        conversation_id,
        db
    )


@router.post(
    "/conversations/{conversation_id}/ask",
    response_model=ChatResponse
)
async def ask_question(
    conversation_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db)
):

    try:

        return await chat_service.ask_question(
            conversation_id,
            payload.question,
            db
        )

    except LLMServiceError as error:

        raise HTTPException(
            status_code=503,
            detail=str(error)
        ) from error


@router.post(
    "/conversations/{conversation_id}/stream"
)
async def stream_question(
    conversation_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db)
):

    prepared = chat_service.prepare_chat(
        conversation_id,
        payload.question,
        db
    )

    async def event_generator():

        yield sse_event(
            "sources",
            {
                "sources": prepared["sources"]
            }
        )

        answer_parts = []

        try:

            if prepared["has_context"]:

                async for token in llm_service.stream(
                    prepared["messages"],
                    temperature=0.1,
                    max_tokens=512
                ):

                    answer_parts.append(token)

                    yield sse_event(
                        "token",
                        {"content": token}
                    )

            else:

                answer_parts.append(
                    chat_service.NO_CONTEXT_ANSWER
                )

                yield sse_event(
                    "token",
                    {
                        "content":
                        chat_service.NO_CONTEXT_ANSWER
                    }
                )

            answer = "".join(answer_parts)

            if not answer.strip():

                yield sse_event(
                    "error",
                    {
                        "message":
                        "AI returned an empty response."
                    }
                )

                return

            with SessionLocal() as stream_db:

                chat_service.save_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=prepared["question"],
                    db=stream_db
                )

                message = chat_service.save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                    sources=prepared["sources"],
                    db=stream_db
                )

                result = MessageResponse.model_validate(
                    message
                ).model_dump(mode="json")

            yield sse_event(
                "done",
                {"message": result}
            )

        except LLMServiceError as error:

            yield sse_event(
                "error",
                {"message": str(error)}
            )

        except Exception:

            yield sse_event(
                "error",
                {
                    "message":
                    "Unable to complete the conversation."
                }
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get(
    "/conversations/{conversation_id}/export"
)
def export_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):

    conversation = chat_service.get_conversation(
        conversation_id,
        db
    )

    data = ConversationDetail.model_validate(
        conversation
    ).model_dump(mode="json")

    return Response(
        content=json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="conversation-{conversation_id}.json"'
            )
        }
    )