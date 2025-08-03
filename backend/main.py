# main.py v4.0
# New Feature: Processes security data and requests a security score from the AI.

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
    title="Stethoscope AI API (v4.0)",
    description="The backend service that analyzes performance and security data.",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD SECRETS ---
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
    """Uses Gemini to get a deep analysis, including a security score."""
    
    # --- UPDATED PROMPT WITH SECURITY FOCUS ---
    prompt = f"""
    You are "Stethoscope AI", an expert Linux System Administrator and Security Analyst.
    Your task is to analyze the following server data and provide a comprehensive health and security report in Markdown format.

    RAW SERVER DATA (in JSON format):
    ```json
    {json.dumps(data, indent=2)}
    ```

    INSTRUCTIONS FOR YOUR RESPONSE:
    1.  Start with a brief "## Executive Summary" of the server's overall health.
    2.  **NEW:** Create a "## 🛡️ Security Analysis" section. Based on the `security` object in the JSON, calculate a "Security Score" from 0 to 100. Display it like: `(Score: 75/100)`. Then, list your security findings.
    3.  For each security issue (e.g., PermitRootLogin is yes, Firewall is inactive), create a level 3 heading starting with 🔴 (Critical) or 🟡 (Warning).
    4.  Create a "## 🩺 Performance Analysis" section. List any performance issues you find here, using the same 🔴 and 🟡 emoji format.
    5.  For every issue (both security and performance), provide two sub-sections:
        - **Root Cause Analysis:** Explain WHY it's an issue.
        - **Solution:** Provide clear, copy-pasteable commands or step-by-step instructions to fix it.
    6.  If you find no issues at all, the report should just be a single "## ✅ All Systems Normal" section.
    7.  The tone must be professional, clear, and reassuring.
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

