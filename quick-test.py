#!/usr/bin/env python3

# Quick test of the fixed Gemini API implementation
import requests
import json


def test_gemini_api():
    api_key = "AIzaSyD2IOD95V-uZ7t13g19KUTjlcqZS1hXWno"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": "Write a short scientific paper title about plastic pollution."
            }]
        }],
        "generationConfig": {
            "maxOutputTokens": 100,
            "temperature": 0.7
        }
    }

    try:
        print("Testing Gemini API...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ API is working!")
            if 'candidates' in result:
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"Generated text: {text}")
                return True
            else:
                print(f"Unexpected response: {result}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

    return False


if __name__ == "__main__":
    test_gemini_api()