from livekit.agents.voice import Agent
import inspect

print("Agent dir:", dir(Agent))
print("Has start:", hasattr(Agent, 'start'))

if hasattr(Agent, 'start'):
    print("Agent.start signature:", inspect.signature(Agent.start))
else:
    print("Agent methods:")
    for name, member in inspect.getmembers(Agent):
        if inspect.isfunction(member) or inspect.ismethod(member):
            print(f"- {name}")
