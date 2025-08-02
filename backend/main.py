# main.py v2.0
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
load_dotenv() # Load variables from .env file

app = FastAPI(
    title="Stethoscope AI API (v2)",
    description="The backend service that analyzes encoded server data.",
    version="2.0.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD SECRETS ---
# Configure the Gemini API
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
    """Uses Gemini to get a deep analysis and recommendations."""
    prompt = f"""
    You are "Stethoscope AI", a world-class Linux System Administrator and performance analyst.
    Your task is to analyze the following server data and provide a concise, actionable health report in Markdown format.

    RAW SERVER DATA (in JSON format):
    ```json
    {json.dumps(data, indent=2)}
    ```

    INSTRUCTIONS:
    1.  Start with a brief "## Executive Summary" of the server's overall health.
    2.  If there are critical issues, create a "## 🔴 Critical Issues" section.
    3.  If there are warnings, create a "## 🟡 Warnings & Recommendations" section.
    4.  For each issue, provide a **Root Cause Analysis** where you correlate different data points to explain WHY it's happening.
    5.  For each issue, provide a **Solution** section with specific, copy-pasteable commands to help the user fix the problem.
    6.  If everything looks good, state that clearly and positively.
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
    """
    Receives Base64 encoded data, decodes it, analyzes it with AI, and returns a report.
    """
    try:
        # Step 1: Decode from Base64 to get the plain JSON string
        decoded_bytes = base64.b64decode(request.data)
        
        # Step 2: Parse the JSON string
        server_data = json.loads(decoded_bytes.decode('utf-8'))

        # Step 3: Get the deep analysis from the Gemini AI
        final_report = get_ai_synthesis(server_data)

        # Step 4: Return the final report to the user
        return {"status": "success", "report": final_report}

    except (base64.binascii.Error, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Bad Request: Invalid data format. The provided data is not valid Base64 encoded JSON. {e}")
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

