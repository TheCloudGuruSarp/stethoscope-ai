# main.py v3.0
# To run this:
# 1. pip install "fastapi[all]" uvicorn python-dotenv google-generativeai
# 2. Create a .env file with your GEMINI_API_KEY
# 3. Run in terminal: uvicorn main:app --reload

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
    title="Stethoscope AI API (v3.0)",
    description="The backend service that analyzes encoded server data with improved reporting.",
    version="3.0.0"
)

# --- CORS Middleware ---
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
    """Uses Gemini to get a deep analysis and recommendations with improved formatting."""
    
    # --- UPDATED PROMPT ---
    prompt = f"""
    You are "Stethoscope AI", a world-class Linux System Administrator.
    Your task is to analyze the following server data and provide a concise, actionable health report in Markdown format.

    RAW SERVER DATA (in JSON format):
    ```json
    {json.dumps(data, indent=2)}
    ```

    INSTRUCTIONS FOR YOUR RESPONSE:
    1.  Start with a brief "## Executive Summary" of the server's overall health.
    2.  Identify all potential issues. For each issue, create a new section.
    3.  For CRITICAL issues (e.g., service down, disk almost full, extreme load), start the heading with a red circle emoji and level 3 markdown heading, like this: `### 🔴 Critical Issue Title`.
    4.  For WARNINGS or recommendations (e.g., high load, potential misconfiguration), start the heading with a yellow circle emoji, like this: `### 🟡 Warning Title`.
    5.  Under each issue's heading, provide two sub-sections using bold markdown:
        - **Root Cause Analysis:** Explain WHY the issue is happening by correlating different data points from the JSON. Be specific.
        - **Solution:** Provide clear, copy-pasteable commands or step-by-step instructions to help the user fix the problem.
    6.  If you find no significant issues, the entire report should just be a single "## ✅ All Systems Normal" section with a brief, positive summary.
    7.  The tone must be professional, clear, and reassuring. Do not wrap your entire response in a single markdown code block.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise ConnectionError(f"Could not get analysis from AI service: {e}")

# --- API ENDPOINT ---
@app.post("/api/v1/analyze")
async def analyze_server(request: AnalyzeRequest):
    """
    Receives Base64 encoded data, decodes it, analyzes it with AI, and returns a report.
    """
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

