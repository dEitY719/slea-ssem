"""CLI autosave command test."""
from unittest.mock import MagicMock, patch
from src.cli.actions.questions import autosave_answer
from src.cli.context import CLIContext, SessionState
from rich.console import Console


def test_autosave_success():
    """Test CLI autosave command with mocked HTTP client."""
    # Create mock context
    mock_console = MagicMock(spec=Console)
    mock_client = MagicMock()

    # Mock responses for different requests
    # First call: GET question type
    question_response = (200, {"type": "short_answer"}, None)
    # Second call: POST autosave
    autosave_response = {
        "saved": True,
        "session_id": "test-session-123",
        "question_id": "test-question-456",
        "saved_at": "2025-11-12T10:00:00"
    }
    autosave_full_response = (200, autosave_response, None)

    # Setup side_effect to return different responses for different calls
    mock_client.make_request.side_effect = [question_response, autosave_full_response]

    # Create a mock for SessionState
    mock_session = MagicMock(spec=SessionState)
    mock_session.token = "fake-token"
    mock_session.current_session_id = "test-session-123"

    # Create CLIContext with mocked components
    context = MagicMock(spec=CLIContext)
    context.console = mock_console
    context.client = mock_client
    context.session = mock_session
    context.logger = MagicMock()

    # Call autosave
    autosave_answer(context, "--session-id", "test-session-123", "--question-id", "test-question-456", "--answer", "test answer")

    # Verify two HTTP requests were made
    assert mock_client.make_request.call_count == 2

    # First call: GET question type
    first_call = mock_client.make_request.call_args_list[0]
    assert first_call[0][0] == "GET"
    assert first_call[0][1] == "/questions/test-question-456"

    # Second call: POST autosave
    second_call = mock_client.make_request.call_args_list[1]
    assert second_call[0][0] == "POST"
    assert second_call[0][1] == "/questions/autosave"

    # Verify JSON data
    json_data = second_call[1]["json_data"]
    assert json_data["session_id"] == "test-session-123"
    assert json_data["question_id"] == "test-question-456"
    assert json_data["user_answer"] == {"text": "test answer"}
    assert json_data["response_time_ms"] == 0

    print("✅ CLI autosave test passed!")
    print(f"   Session: {json_data['session_id']}")
    print(f"   Question: {json_data['question_id']}")
    print(f"   Answer: {json_data['user_answer']}")


def test_autosave_no_active_session():
    """Test autosave fails when no active session."""
    # Create mock context without session
    mock_console = MagicMock(spec=Console)
    context = MagicMock()
    context.console = mock_console
    context.session.token = "fake-token"
    context.session.current_session_id = None  # No active session
    
    # Call autosave - should print error
    autosave_answer(context, "test-question", "test answer")
    
    # Verify error message was printed
    assert mock_console.print.called
    print_call = mock_console.print.call_args[0][0]
    assert "No active session" in print_call or "questions generate" in print_call
    print("✅ No active session test passed!")


def test_autosave_not_authenticated():
    """Test autosave fails when not authenticated."""
    # Create mock context without token
    mock_console = MagicMock(spec=Console)
    context = MagicMock()
    context.console = mock_console
    context.session.token = None  # Not authenticated
    
    # Call autosave - should print error
    autosave_answer(context, "test-question", "test answer")
    
    # Verify error message was printed
    assert mock_console.print.called
    print_call = mock_console.print.call_args[0][0]
    assert "Not authenticated" in print_call
    print("✅ Not authenticated test passed!")


if __name__ == "__main__":
    test_autosave_not_authenticated()
    test_autosave_no_active_session()
    test_autosave_success()
    print("\n✅ All CLI autosave tests passed!")
