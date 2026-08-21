from openai import OpenAI

client = OpenAI()

with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="sage",
    input="Hello, this is a voice quality test. The quick brown fox jumps over the lazy dog. One two three four five six seven eight nine zero. Thank you."
) as response:
    response.stream_to_file("quick_brown_fox.wav")

print("Done")
