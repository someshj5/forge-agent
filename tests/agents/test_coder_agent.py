import json
from unittest.mock import Mock

from app.agent.edit_operations import EditOperationType
from app.agent.state import AgentState
from app.agents.coder_agent import CoderAgent

def prompt_text(messages):
    return "\n".join(
        message["content"]
        for message in messages
    )

class FakeState:
    def __init__(
        self,
        relevant_files=None,
        target_symbol="urlpatterns",
        task=(
            "Add the comment '# Django URL routes' "
            "immediately above urlpatterns."
        ),
    ):
        self.task = task
        self.repository = "demo-django"
        self.relevant_files = relevant_files or []
        self.target_symbol = target_symbol
        self.edits = []
        self.current_agent = None

    def record_edit(
        self,
        path,
        old_text,
        new_text,
        success,
    ):
        edit_id = f"edit-{len(self.edits) + 1}"

        self.edits.append(
            {
                "id": edit_id,
                "path": path,
                "old_text": old_text,
                "new_text": new_text,
                "success": success,
                "error": None,
            }
        )

        return edit_id


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return self.response


class FakeEditEngine:
    def __init__(self, result=None):
        self.result = result or {"success": True}
        self.operation = None
        self.target_text = None

    def apply(self, operation, target_text):
        self.operation = operation
        self.target_text = target_text

        return self.result


def make_state():
    return FakeState(
        relevant_files=[
            "demo-django/demo_django/urls.py"
        ],
        target_symbol="urlpatterns",
    )


def make_file_content():
    return (
        '"""\n'
        "URL configuration for demo_django project.\n"
        "\n"
        "The `urlpatterns` list routes URLs to views.\n"
        '"""\n'
        "from django.contrib import admin\n"
        "from django.urls import path\n"
        "\n"
        "urlpatterns = [\n"
        "    path('admin/', admin.site.urls),\n"
        "]\n"
    )


def make_success_response():
    return json.dumps(
        {
            "operation": "insert_before",
            "text": "# Django URL routes\n",
        }
    )


# ------------------------------------------------------------------
# Basic validation
# ------------------------------------------------------------------


def test_coder_fails_when_no_relevant_files():
    state = FakeState(relevant_files=[])

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
    )

    result = agent.run(state)

    assert result.success is False
    assert "No relevant files" in result.error


def test_coder_fails_when_no_target_symbol():
    state = FakeState(
        relevant_files=[
            "demo-django/demo_django/urls.py"
        ],
        target_symbol=None,
    )

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
    )

    result = agent.run(state)

    assert result.success is False
    assert "target symbol" in result.error.lower()


def test_coder_fails_when_no_llm():
    state = make_state()

    agent = CoderAgent(llm=None)

    result = agent.run(state)

    assert result.success is False
    assert "No LLM" in result.error


# ------------------------------------------------------------------
# File reading
# ------------------------------------------------------------------


def test_coder_reads_relevant_file_before_generating_edit(monkeypatch):
    state = make_state()

    read_calls = []

    def fake_read_file(path):
        read_calls.append(path)

        return {
            "success": True,
            "content": make_file_content(),
        }

    monkeypatch.setattr(
        "app.agents.coder_agent.read_file",
        fake_read_file,
    )

    llm = FakeLLM(make_success_response())

    agent = CoderAgent(llm=llm)

    result = agent.run(state)

    assert result.success is True

    assert read_calls == [
        "demo-django/demo_django/urls.py"
    ]


# ------------------------------------------------------------------
# Target resolution
# ------------------------------------------------------------------


def test_coder_resolves_target_symbol():
    state = make_state()

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
    )

    content = make_file_content()

    target = agent._resolve_target(
        content=content,
        target_symbol="urlpatterns",
    )

    assert target is not None
    assert target["id"] == "A9"
    assert target["text"] == "urlpatterns = ["


def test_coder_does_not_resolve_unrelated_symbol():
    state = make_state()

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
    )

    content = make_file_content()

    target = agent._resolve_target(
        content=content,
        target_symbol="does_not_exist",
    )

    assert target is None


def test_coder_fails_when_target_cannot_be_resolved():
    state = FakeState(
        relevant_files=[
            "demo-django/demo_django/urls.py"
        ],
        target_symbol="does_not_exist",
    )

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
    )

    result = agent.run(state)

    assert result.success is False
    assert "Could not resolve target symbol" in result.error


# ------------------------------------------------------------------
# JSON parsing
# ------------------------------------------------------------------


def test_coder_fails_on_invalid_json():
    state = make_state()

    agent = CoderAgent(
        llm=FakeLLM(
            "this is not valid json"
        )
    )

    result = agent.run(state)

    assert result.success is False
    assert "Invalid JSON" in result.error


def test_coder_accepts_json_code_fence():
    state = make_state()

    response = """```json
{
    "operation": "insert_before",
    "text": "# Django URL routes\\n"
}
```"""

    edit_engine = FakeEditEngine()

    agent = CoderAgent(
        llm=FakeLLM(response),
        edit_engine=edit_engine,
    )

    result = agent.run(state)

    assert result.success is True

    assert edit_engine.operation.operation == (
        EditOperationType.INSERT_BEFORE
    )


# ------------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------------


def test_coder_fails_on_invalid_schema():
    state = make_state()

    response = json.dumps(
        {
            "operation": "insert_before",
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(response),
    )

    result = agent.run(state)

    assert result.success is False
    assert "text" in result.error.lower()


def test_coder_rejects_unexpected_fields():
    state = make_state()

    response = json.dumps(
        {
            "operation": "insert_before",
            "text": "# Django URL routes\n",
            "target_id": "A9",
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(response),
    )

    result = agent.run(state)

    assert result.success is False
    assert "Unexpected fields" in result.error


def test_coder_rejects_invalid_operation():
    state = make_state()

    response = json.dumps(
        {
            "operation": "modify_something",
            "text": "# Django URL routes\n",
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(response),
    )

    result = agent.run(state)

    assert result.success is False
    assert "Invalid edit operation" in result.error


def test_coder_rejects_non_string_text():
    state = make_state()

    response = json.dumps(
        {
            "operation": "insert_before",
            "text": 123,
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(response),
    )

    result = agent.run(state)

    assert result.success is False
    assert "text" in result.error.lower()


def test_coder_rejects_empty_text_for_insert():
    state = make_state()

    response = json.dumps(
        {
            "operation": "insert_before",
            "text": "",
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(response),
    )

    result = agent.run(state)

    assert result.success is False
    assert "cannot be empty" in result.error


# ------------------------------------------------------------------
# EditEngine
# ------------------------------------------------------------------


def test_coder_fails_when_edit_engine_fails():
    state = make_state()

    edit_engine = FakeEditEngine(
        result={
            "success": False,
            "error": "Edit failed",
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
        edit_engine=edit_engine,
    )

    result = agent.run(state)

    assert result.success is False
    assert "Edit failed" in result.error


def test_coder_successfully_applies_insert_before():
    state = make_state()

    edit_engine = FakeEditEngine()

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
        edit_engine=edit_engine,
    )

    result = agent.run(state)

    assert result.success is True

    operation = edit_engine.operation

    assert operation.path == (
        "demo-django/demo_django/urls.py"
    )

    # IMPORTANT:
    # target_id was resolved by CoderAgent,
    # not provided by the LLM.
    assert operation.target_id.startswith("A")

    assert operation.operation == (
        EditOperationType.INSERT_BEFORE
    )

    assert operation.text == (
        "# Django URL routes\n"
    )

    assert edit_engine.target_text == (
        "urlpatterns = ["
    )


# ------------------------------------------------------------------
# State recording
# ------------------------------------------------------------------


def test_coder_records_successful_edit():
    state = make_state()

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
        edit_engine=FakeEditEngine(),
    )

    result = agent.run(state)

    assert result.success is True
    assert len(state.edits) == 1

    edit = state.edits[0]

    assert edit["id"] == "edit-1"

    assert edit["path"] == (
        "demo-django/demo_django/urls.py"
    )

    assert edit["old_text"] == (
        "urlpatterns = ["
    )

    assert edit["new_text"] == (
        "# Django URL routes\n"
        "urlpatterns = ["
    )

    assert edit["success"] is True


# ------------------------------------------------------------------
# Deterministic target behavior
# ------------------------------------------------------------------


def test_coder_ignores_target_id_from_llm():
    state = make_state()

    response = json.dumps(
        {
            "operation": "insert_before",
            "text": "# Django URL routes\n",
            # This should not be accepted as part of the contract.
            "target_id": "A999",
        }
    )

    agent = CoderAgent(
        llm=FakeLLM(response),
        edit_engine=FakeEditEngine(),
    )

    result = agent.run(state)

    assert result.success is False
    assert "Unexpected fields" in result.error


def test_coder_uses_resolved_target_not_llm_target():
    state = make_state()

    # The LLM doesn't get to choose a target.
    response = make_success_response()

    edit_engine = FakeEditEngine()

    agent = CoderAgent(
        llm=FakeLLM(response),
        edit_engine=edit_engine,
    )

    result = agent.run(state)

    assert result.success is True

    assert edit_engine.operation.target_id.startswith("A")

    assert edit_engine.target_text == (
        "urlpatterns = ["
    )


# ------------------------------------------------------------------
# LLM prompt contract
# ------------------------------------------------------------------


def test_coder_prompt_contains_resolved_target():
    state = make_state()

    llm = FakeLLM(make_success_response())

    agent = CoderAgent(llm=llm)

    result = agent.run(state)

    assert result.success is True

    assert llm.messages is not None

    prompt_text = "\n".join(
        message.get("content", "")
        for message in llm.messages
    )

    assert "urlpatterns" in prompt_text
    assert "urlpatterns = [" in prompt_text


def test_coder_prompt_does_not_ask_llm_to_select_target():
    state = make_state()

    llm = FakeLLM(make_success_response())

    agent = CoderAgent(llm=llm)

    result = agent.run(state)

    assert result.success is True

    prompt_text = "\n".join(
        message.get("content", "")
        for message in llm.messages
    )

    assert "target_id" not in prompt_text


# ------------------------------------------------------------------
# Agent state
# ------------------------------------------------------------------


def test_coder_sets_current_agent():
    state = make_state()

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
        edit_engine=FakeEditEngine(),
    )

    result = agent.run(state)

    assert result.success is True
    assert state.current_agent == "coder"


# ------------------------------------------------------------------
# Result metadata
# ------------------------------------------------------------------


def test_coder_result_contains_edit_metadata():
    state = make_state()

    agent = CoderAgent(
        llm=FakeLLM(make_success_response()),
        edit_engine=FakeEditEngine(),
    )

    result = agent.run(state)

    assert result.success is True

    assert result.data["edit_id"] == "edit-1"

    assert result.data["path"] == (
        "demo-django/demo_django/urls.py"
    )

    assert result.data["target_symbol"] == (
        "urlpatterns"
    )

    assert result.data["target_id"].startswith("A")

    assert result.data["target_text"] == (
        "urlpatterns = ["
    )

    assert result.data["operation"] == (
        "insert_before"
    )

    assert result.data["text"] == (
        "# Django URL routes\n"
    )


def test_coder_prompt_includes_selected_skill():
    agent = CoderAgent(
        llm=Mock()
    )

    state = AgentState(
        task="Add a comment above urlpatterns",
        repository="demo-django",
        skill_context=[
            {
                "name": "django-pro",
                "description": (
                    "Django development and ORM optimization"
                ),
                "content": (
                    "Use Django URL configuration conventions."
                ),
            }
        ],
    )

    target = {
        "id": "A1",
        "text": "urlpatterns = [",
    }

    prompt = agent._build_prompt(
        state=state,
        path="demo-django/demo_django/urls.py",
        target=target,
    )

    assert "django-pro" in prompt_text(prompt)
    assert (
        "Use Django URL configuration conventions."
        in prompt_text(prompt)
    )

def test_coder_prompt_without_skill_has_no_skill_section():
    agent = CoderAgent(
        llm=Mock()
    )

    state = AgentState(
        task="Add a comment above urlpatterns",
        repository="demo-django",
    )

    target = {
        "id": "A1",
        "text": "urlpatterns = [",
    }

    prompt = agent._build_prompt(
        state=state,
        path="demo-django/demo_django/urls.py",
        target=target,
    )

    assert "Relevant Engineering Skills" not in prompt

def test_coder_prompt_keeps_resolved_target_with_skill():
    agent = CoderAgent(
        llm=Mock()
    )

    state = AgentState(
        task="Add a comment above urlpatterns",
        repository="demo-django",
        skill_context=[
            {
                "name": "django-pro",
                "description": "Django guidance",
                "content": "Use Django conventions.",
            }
        ],
    )

    target = {
        "id": "A1",
        "text": "urlpatterns = [",
    }

    prompt = agent._build_prompt(
        state=state,
        path="demo-django/demo_django/urls.py",
        target=target,
    )

    assert "urlpatterns = [" in prompt_text(prompt)
    assert (
    "You must NOT choose a target or file."
    in prompt_text(prompt)
)

    