from livekit.agents import llm
try:
    ctx = llm.ChatContext()
    print("Ctx created.")
    print(dir(ctx))
except Exception as e:
    print("Error:", e)
