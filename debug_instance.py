from livekit.agents.voice import Agent
from unittest.mock import MagicMock
import logging

try:
    logging.basicConfig(level=logging.ERROR)
    # Instantiate Agent with mocks to bypass required args
    agent = Agent(
        vad=MagicMock(),
        stt=MagicMock(),
        llm=MagicMock(),
        tts=MagicMock(),
        instructions="debug"
    )
    print("Instance created.")
    print("Start method exists?", hasattr(agent, 'start'))
    print("Run method exists?", hasattr(agent, 'run'))
    print("Methods:", [x for x in dir(agent) if not x.startswith('_')])
except Exception as e:
    print(f"Error: {e}")
