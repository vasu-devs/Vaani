try:
    from livekit.agents.voice import VoicePipelineAgent
    print("Found VoicePipelineAgent")
except ImportError as e:
    print(f"VoicePipelineAgent NOT found: {e}")

try:
    from livekit.agents.pipeline import VoicePipelineAgent
    print("Found pipeline.VoicePipelineAgent")
except ImportError as e:
    print(f"pipeline.VoicePipelineAgent NOT found: {e}")
