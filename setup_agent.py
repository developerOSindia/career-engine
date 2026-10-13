#!/usr/bin/env python3
"""
CareerOS - Setup & Onboarding CLI Entrypoint.
Usage:
    python3 setup_agent.py              # Interactive wizard
    python3 setup_agent.py --defaults   # Quick template generation
"""
import sys
from core.setup_agent import SetupAgent

if __name__ == "__main__":
    agent = SetupAgent()
    defaults = "--defaults" in sys.argv or "--non-interactive" in sys.argv
    agent.run(defaults_only=defaults)
