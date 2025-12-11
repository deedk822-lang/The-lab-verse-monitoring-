Groq SDK package can be installed using the following command:

shell

pip install groq
The following is an example of a request using playai-tts. To use the Arabic model, use the playai-tts-arabic model ID and an Arabic prompt:

Python

import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

speech_file_path = "speech.wav" 
model = "playai-tts"
voice = "Fritz-PlayAI"
text = "I love building and shipping new features for our users!"
response_format = "wav"

response = client.audio.speech.create(
    model=model,
    voice=voice,
    input=text,
    response_format=response_format
)

response.write_to_file(speech_file_path)
Parameters
