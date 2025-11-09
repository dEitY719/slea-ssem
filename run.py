"""Entry point for SLEA-SSEM CLI application."""

import os
import signal
import sys
from types import FrameType

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from cli.main import main


def signal_handler(sig: int, frame: FrameType | None) -> None:
    """Handle signals gracefully."""
    print("\n[CLI] Received signal. Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    try:
        main()
    except Exception as e:
        print(f"[ERROR] Unhandled exception: {e}", file=sys.stderr)
        sys.exit(1)
