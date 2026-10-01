from groq import Groq

client = Groq(api_key="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")
model = "openai/gpt-oss-20b"

print(f"Testing {model}...")
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": 'Respond strictly in JSON with: {"status": "ok"}'}],
    response_format={"type": "json_object"}
)
print("SUCCESS! Output:", response.choices[0].message.content)
