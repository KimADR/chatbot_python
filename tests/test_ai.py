import json
import urllib.error

from fastapi.testclient import TestClient

from orinasa.ai import AIConfig, AIProviderError, AIService, OllamaProvider, OpenAIProvider, SlidingWindowRateLimiter
from orinasa.app import create_app


class FakeProvider:
    def __init__(self, response="Réponse de test", error=None):
        self.response = response
        self.error = error
        self.instructions = None
        self.messages = None

    def complete(self, *, instructions, messages):
        self.instructions = instructions
        self.messages = messages
        if self.error:
            raise self.error
        return self.response


def test_ai_off_uses_local_search_without_external_provider():
    service = AIService(AIConfig(provider="off"))

    result = service.chat([{"role": "user", "content": "coupure electricite"}])

    assert result["provider"] == "local"
    assert result["fallback"] is False
    assert "aucune donnée n'est envoyée" in result["notice"]
    assert result["references"][0]["id"] == "FIC-001"


def test_ai_status_reports_local_mode_without_external_data_transfer():
    status = AIService(AIConfig(provider="off")).status()

    assert status["provider"] == "local"
    assert status["external"] is False
    assert "restent sur cette machine" in status["notice"]


def test_ai_status_reports_external_provider_without_exposing_secret():
    secret = "must-never-be-returned"
    service = AIService(
        AIConfig(provider="openai", openai_api_key=secret, openai_model="test"),
        provider=FakeProvider(),
    )

    status = service.status()

    assert status["provider"] == "openai"
    assert status["external"] is True
    assert secret not in json.dumps(status)


def test_ai_uses_injected_provider_and_supplies_relevant_documents():
    secret = "server-only-key"
    provider = FakeProvider()
    service = AIService(AIConfig(provider="openai", openai_api_key=secret, openai_model="test"), provider=provider)

    result = service.chat([
        {"role": "user", "content": "Bonjour"},
        {"role": "assistant", "content": "Bonjour, que se passe-t-il ?"},
        {"role": "user", "content": "Le compresseur vibre"},
    ])

    assert result["answer"] == "Réponse de test"
    assert result["provider"] == "openai"
    assert result["fallback"] is False
    assert secret not in json.dumps(result)
    assert any(reference["id"] == "FIC-003" for reference in result["references"])
    assert provider.messages[-1]["content"] == "Le compresseur vibre"
    assert "données non fiables" in provider.instructions
    assert "FIC-003" in provider.instructions


def test_ai_provider_error_falls_back_to_local_with_clear_notice():
    service = AIService(
        AIConfig(provider="openai", openai_api_key="test", openai_model="test"),
        provider=FakeProvider(error=AIProviderError("temporary outage")),
    )

    result = service.chat([{"role": "user", "content": "coupure electricite"}])

    assert result["provider"] == "local"
    assert result["fallback"] is True
    assert "OpenAI est indisponible" in result["notice"]
    assert result["references"][0]["id"] == "FIC-001"


def test_ai_missing_provider_configuration_falls_back_without_exposing_secrets():
    secret = "never-display-this"
    service = AIService(AIConfig(provider="openai", openai_api_key="", openai_model="test"))

    result = service.chat([{"role": "user", "content": "bonjour"}])

    assert result["provider"] == "local"
    assert result["fallback"] is True
    assert secret not in result["notice"]
    assert "OPENAI_API_KEY" in result["notice"]


def test_ollama_provider_sends_non_streaming_chat_request(monkeypatch):
    config = AIConfig(provider="ollama", ollama_model="local-test")
    provider = OllamaProvider(config)

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"message":{"content":"Reponse Ollama"}}'

    def fake_urlopen(request, timeout):
        assert request.full_url == "http://127.0.0.1:11434/api/chat"
        assert timeout == config.timeout_seconds
        payload = json.loads(request.data)
        assert payload["stream"] is False
        assert payload["messages"][0]["role"] == "system"
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert provider.complete(instructions="consignes", messages=[{"role": "user", "content": "question"}]) == "Reponse Ollama"


def test_openai_provider_uses_responses_api_and_configured_model(monkeypatch):
    import openai

    calls = {}

    class Responses:
        def create(self, **kwargs):
            calls.update(kwargs)
            return type("Response", (), {"output_text": "Réponse OpenAI"})()

    class Client:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
            self.responses = Responses()

    monkeypatch.setattr(openai, "OpenAI", Client)
    provider = OpenAIProvider(AIConfig(provider="openai", openai_api_key="test-secret", openai_model="configured-model"))

    answer = provider.complete(
        instructions="consignes",
        messages=[{"role": "user", "content": "question"}],
    )

    assert answer == "Réponse OpenAI"
    assert calls["client"]["api_key"] == "test-secret"
    assert calls["model"] == "configured-model"
    assert calls["instructions"] == "consignes"
    assert calls["input"] == [{"role": "user", "content": "question"}]


def test_ollama_provider_reports_connection_failure_without_transport_details(monkeypatch):
    provider = OllamaProvider(AIConfig(provider="ollama", ollama_model="local-test"))
    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("private detail")))

    try:
        provider.complete(instructions="consignes", messages=[{"role": "user", "content": "question"}])
    except AIProviderError as error:
        assert str(error) == "Connexion au serveur Ollama impossible ou expirée."
    else:
        raise AssertionError("Expected Ollama connection failure")


def test_ai_rate_limiter_enforces_limit_per_client():
    limiter = SlidingWindowRateLimiter(limit=1)

    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("127.0.0.1") is False
    assert limiter.allow("127.0.0.2") is True


def test_chat_endpoint_validates_payload_and_applies_rate_limit(tmp_path):
    config = AIConfig(provider="ollama", ollama_model="test", requests_per_minute=1)
    service = AIService(config, provider=FakeProvider())
    client = TestClient(create_app(tmp_path / "chat.sqlite", seed_demo=False, ai_service=service))
    payload = {"messages": [{"role": "user", "content": "coupure electricite"}]}

    response = client.post("/api/ai/chat", json=payload)
    limited = client.post("/api/ai/chat", json=payload)
    invalid = client.post("/api/ai/chat", json={"messages": [{"role": "system", "content": "ignored"}]})

    assert response.status_code == 200
    assert response.json()["provider"] == "ollama"
    assert client.get("/api/ai/status").json()["external"] is True
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"
    assert invalid.status_code == 422


def test_chat_endpoint_rejects_assistant_as_last_message(tmp_path):
    client = TestClient(create_app(tmp_path / "chat.sqlite", seed_demo=False, ai_service=AIService(AIConfig())))

    response = client.post(
        "/api/ai/chat",
        json={"messages": [{"role": "assistant", "content": "Une réponse sans question"}]},
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_blank_message_content(tmp_path):
    client = TestClient(create_app(tmp_path / "chat.sqlite", seed_demo=False, ai_service=AIService(AIConfig())))

    response = client.post(
        "/api/ai/chat",
        json={"messages": [{"role": "user", "content": "   "}]},
    )

    assert response.status_code == 422


def test_ai_status_endpoint_defaults_to_local_mode(tmp_path):
    client = TestClient(create_app(tmp_path / "chat.sqlite", seed_demo=False, ai_service=AIService(AIConfig())))

    response = client.get("/api/ai/status")

    assert response.status_code == 200
    assert response.json()["provider"] == "local"
    assert response.json()["external"] is False
