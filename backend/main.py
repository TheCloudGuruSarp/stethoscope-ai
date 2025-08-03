# main.py v6.0
# Removed Google SSO Auth and Firestore DB integration for simplicity.

import base64
import json
import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

app = FastAPI(
    title="Stethoscope AI API (v6.0)",
    description="A simplified backend for analyzing server data without user authentication.",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD SECRETS & INITIALIZE SERVICES ---
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATA MODELS ---
class AnalyzeRequest(BaseModel):
    data: str

# --- CORE LOGIC ---
def get_ai_synthesis(data: dict) -> str:
    """Uses Gemini to get a deep analysis, including security and package checks."""
    prompt = f"""
    You are "Stethoscope AI", an expert Linux System Administrator and Security Analyst.
    Your task is to analyze the following server data and provide a comprehensive health and security report in Markdown format.

    RAW SERVER DATA:
    ```json
    {json.dumps(data, indent=2)}
    ```

    INSTRUCTIONS FOR YOUR RESPONSE:
    1.  Start with a "## Executive Summary".
    2.  Create a "## 🛡️ Security Analysis" section. Calculate a "Security Score" out of 100. List security findings.
    3.  Create a "## 📦 Package Security" section. Analyze the `package_updates` list. If it contains critical packages like `openssh-server`, `openssl`, `kernel`, etc., list them in a Markdown table.
    4.  Create a "## 🩺 Performance Analysis" section for performance issues.
    5.  For every issue, use 🔴 (Critical) or 🟡 (Warning) in a level 3 heading (`###`).
    6.  Under each issue, provide **Root Cause Analysis** and **Solution** sub-sections.
    7.  If no issues, the report should be a single "## ✅ All Systems Normal" section.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise ConnectionError(f"Could not get analysis from AI service: {e}")

# --- API ENDPOINT ---
@app.post("/api/v1/analyze")
async def analyze_server(request: AnalyzeRequest):
    try:
        decoded_bytes = base64.b64decode(request.data)
        server_data = json.loads(decoded_bytes.decode('utf-8'))
        final_report = get_ai_synthesis(server_data)
        return {"status": "success", "report": final_report}
    except (base64.binascii.Error, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid Data Format: The provided text is not a valid output from the analyzer script.")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

