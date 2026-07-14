import pytest
from pydantic import ValidationError

from schemas import ChatRequest, ChatResponse


def test_chat_request_requires_question():
    with pytest.raises(ValidationError):
        ChatRequest()


def test_chat_request_accepts_question():
    request = ChatRequest(question="What are the symptoms of flu?")
    assert request.question == "What are the symptoms of flu?"


def test_chat_response_shape():
    response = ChatResponse(
        response="Fever, cough, fatigue.",
        confidence=0.87,
        sources=["Influenza - Overview"],
    )
    assert response.confidence == 0.87
    assert response.sources == ["Influenza - Overview"]


def test_chat_response_requires_all_fields():
    with pytest.raises(ValidationError):
        ChatResponse(response="incomplete")
