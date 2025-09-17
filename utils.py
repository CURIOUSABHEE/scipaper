# utils.py

import requests
import random
import json
import os
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

# Load .env file automatically
load_dotenv()

# Use environment variable for the API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")


def generate_text_with_gemini(prompt):
    """Generate text using Gemini API and expect a JSON response."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Payload now requests a JSON response for better structure
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",  # Request JSON output
            "maxOutputTokens": 2048,
            "temperature": 0.7
        }
    }

    try:
        print("[DEBUG] Making request to Gemini API...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        # The API returns JSON directly, so we parse the 'text' part which contains the JSON string
        result_json_string = response.json()['candidates'][0]['content']['parts'][0]['text']
        print(f"[DEBUG] Received JSON string from API:\n{result_json_string[:500]}...")

        # Return the parsed dictionary
        return json.loads(result_json_string)

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed: {e}")
        return {"error": f"API request failed: {str(e)}"}
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"[ERROR] Failed to parse API response: {e}")
        return {"error": f"Failed to parse API response: {str(e)}"}
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}


def generate_fake_paper(user_input):
    """
    Generate a full, structured academic paper using a single Gemini API call.
    """

    # Your new, powerful system prompt
    system_prompt = f"""
You are an expert research assistant and academic writer. Your task is to produce a high-quality, well-structured research paper on the topic: "{user_input}".

Guidelines:
- Structure: Generate content in the standard research paper format.
- Content Quality: Use formal academic language with a logical flow.
- References: Generate 3-5 hypothetical references in APA style.
- Output: Provide the output as a single, valid JSON object. Do not include any text or markdown formatting before or after the JSON object.

The JSON object must have the following structure:
{{
  "title": "A concise and academic title for the paper.",
  "authors": "Generated Author 1, Generated Author 2",
  "abstract": "A 150-word summary of the paper.",
  "sections": [
    {{
      "heading": "Introduction",
      "content": "A detailed introduction to the topic."
    }},
    {{
      "heading": "Literature Review",
      "content": "A review of existing literature relevant to the topic."
    }},
    {{
      "heading": "Methodology",
      "content": "A description of the research methodology used."
    }},
    {{
      "heading": "Results",
      "content": "A summary of the findings or results."
    }},
    {{
      "heading": "Discussion",
      "content": "A discussion of the results, their implications, and limitations."
    }},
    {{
      "heading": "Conclusion",
      "content": "A concluding summary of the paper."
    }},
    {{
      "heading": "References",
      "content": "A list of 3-5 hypothetical references in APA format, separated by newlines."
    }}
  ]
}}
"""

    print(f"[DEBUG] Starting paper generation for: {user_input}")

    try:
        paper_data = generate_text_with_gemini(system_prompt)

        if "error" in paper_data:
            # Handle cases where the API call failed
            raise Exception(paper_data["error"])

        print("[DEBUG] Paper generation completed successfully.")
        return paper_data

    except Exception as e:
        print(f"[ERROR] Failed to generate paper: {e}")
        # Return a fallback paper structure so the app doesn't crash
        return {
            "title": f"Error Generating Paper on '{user_input.title()}'",
            "authors": "System",
            "abstract": f"An error occurred while trying to generate the paper. Please check the console logs for details. Error: {str(e)}",
            "sections": [
                {"heading": "Error Details",
                 "content": "The content could not be generated. This might be due to an API key issue, a network problem, or an error in parsing the response from the AI model."}
            ]
        }


# In utils.py

# ... (keep all your existing code and imports) ...

# In utils.py

# ... (keep all your existing code and other functions) ...

# In utils.py

# ... (keep all your existing code and other functions) ...

def analyze_paper_content(paper_text):
    """
    Analyzes text using a more robust "few-shot" prompt that includes examples
    to guide the AI's judgment and improve accuracy.
    """

    # This new prompt includes examples to train the AI on the fly.
    analysis_prompt = f"""
You are an expert linguistic analyst specializing in differentiating between human and AI-generated scholarly articles. Your task is to analyze the provided text and determine the likelihood that it was generated by an AI.

**Core Distinction:** Human academic writing, while formal, typically presents a novel argument, unique synthesis of ideas, or a distinct authorial voice. AI-generated text is often a flawless but generic summary of existing information, lacking a true spark of originality. Your primary goal is to detect this distinction.

**Important Context:** The text was extracted from a file and may contain formatting errors. Ignore these formatting issues and focus on the semantic content.

---
**EXAMPLE 1 (AI-Generated Text):**
"Blockchain technology, a decentralized and distributed ledger system, has emerged as a transformative force across various industries. Its core principles of immutability, transparency, and security offer profound implications for supply chain management, financial services, and digital identity verification. By enabling secure, peer-to-peer transactions without the need for intermediaries, blockchain mitigates risks of fraud and enhances operational efficiency."

**Expected Analysis for Example 1:**
{{
  "score": 90,
  "reasoning": "The text is a perfect, high-level summary of blockchain. It uses standard terminology correctly but offers no novel insight, specific data, or unique perspective. The sentence structure is very consistent and lacks a distinct authorial voice.",
  "confidence": "High"
}}
---
**EXAMPLE 2 (Human-Written Text):**
"While most scholars focus on blockchain's transactional efficiency, they often overlook its profound impact on organizational trust dynamics. My research in rural Indian co-ops revealed a surprising reluctance to adopt the technology. Farmers didn't see it as a trust machine; they saw it as another opaque system imposed by outsiders. This suggests that the cultural context of trust, rather than the technology itself, is the primary barrier to adoption, a point starkly absent from the mainstream techno-optimist discourse."

**Expected Analysis for Example 2:**
{{
  "score": 15,
  "reasoning": "The text presents a specific, novel argument that counters a mainstream view. It references personal research ('My research...'), introduces a unique context (Indian co-ops), and has a clear, critical authorial voice. The phrasing 'starkly absent' and 'techno-optimist discourse' shows a distinct human perspective.",
  "confidence": "High"
}}
---

Now, using the principles and examples above as your guide, analyze the following text. Return your analysis as a single, valid JSON object with the keys: "score", "reasoning", "confidence".

**Text to Analyze:**
---
{paper_text}
---
"""

    print("[DEBUG] Starting paper analysis with few-shot example prompt...")

    try:
        analysis_result = generate_text_with_gemini(analysis_prompt)

        if "error" in analysis_result:
            raise Exception(analysis_result["error"])

        print("[DEBUG] Analysis completed successfully.")
        return analysis_result

    except Exception as e:
        print(f"[ERROR] Failed to analyze paper content: {e}")
        return {
            "score": -1,
            "reasoning": f"An error occurred during analysis: {str(e)}",
            "confidence": "N/A"
             }