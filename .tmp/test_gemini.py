import os
import requests
from dotenv import load_dotenv

load_dotenv("burguersync.analisadorFeedback/.env")
key = os.getenv("GEMINI_API_KEY")

for model in ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    body = {"contents": [{"parts": [{"text": "Diga oi em formato JSON: {\"msg\": \"oi\"}"}]}]}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=10)
        print(f"Model {model} -> Status: {r.status_code}")
        if r.status_code == 200:
            print("Output:", r.json()["candidates"][0]["content"]["parts"][0]["text"])
            break
        else:
            print(r.text[:150])
    except Exception as e:
        print(f"Model {model} -> Exception: {e}")
