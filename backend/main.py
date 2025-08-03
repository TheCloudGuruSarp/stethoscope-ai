# main.py v5.0
# New Features: Google SSO Auth, Firestore DB for history, package analysis.

import base64
import json
import os
import datetime
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONFIGURATION ---
load_dotenv()

app = FastAPI(
    title="Stethoscope AI API (v5.0)",
    description="Backend with Google Auth, Firestore history, and advanced analysis.",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD SECRETS & INITIALIZE SERVICES ---
# Google Client ID for verifying tokens
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("CRITICAL: GOOGLE_CLIENT_ID environment variable not set.")

# Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# Firebase / Firestore
# IMPORTANT: Your Firebase service account key should be stored as a JSON string
# in an environment variable, e.g., FIREBASE_CREDENTIALS
cred_json_str = os.getenv("FIREBASE_CREDENTIALS")
if not cred_json_str:
    raise ValueError("CRITICAL: FIREBASE_CREDENTIALS environment variable not set.")
cred_json = json.loads(cred_json_str)
cred = credentials.Certificate(cred_json)
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- AUTHENTICATION ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates Google ID token and returns user's Google ID (sub)."""
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return idinfo['sub']  # 'sub' is the unique user ID
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    3.  **NEW:** Create a "## 📦 Package Security" section. Analyze the `package_updates` list. If it contains critical packages like `openssh-server`, `openssl`, `kernel`, etc., list them in a Markdown table.
    4.  Create a "## 🩺 Performance Analysis" section for performance issues.
    5.  For every issue, use 🔴 (Critical) or 🟡 (Warning) in a level 3 heading (`###`).
    6.  Under each issue, provide **Root Cause Analysis** and **Solution** sub-sections.
    7.  If no issues, the report should be a single "## ✅ All Systems Normal" section.
    """
    try:
        response = model.generate_content(prompt)
        # Extract a short summary for the history list
        summary = response.text.splitlines()[0].replace("## ", "")
        return response.text, summary
    except Exception as e:
        raise ConnectionError(f"Could not get analysis from AI service: {e}")

# --- API ENDPOINTS ---
@app.post("/api/v1/analyze")
async def analyze_server(request: AnalyzeRequest, user_id: str = Depends(get_current_user)):
    try:
        decoded_bytes = base64.b64decode(request.data)
        server_data = json.loads(decoded_bytes.decode('utf-8'))
        
        final_report, summary = get_ai_synthesis(server_data)
        
        # Save to Firestore
        doc_ref = db.collection('analyses').document(user_id).collection('scans').document()
        doc_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'report': final_report,
            'summary': summary,
            'distro': server_data.get('os_info', {}).get('distro', 'Unknown')
        })

        # Keep only the last 5 scans
        scans_query = db.collection('analyses').document(user_id).collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).get()
        if len(scans_query) > 5:
            for i in range(5, len(scans_query)):
                scans_query[i].reference.delete()

        return {"status": "success", "report": final_report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/api/v1/history")
async def get_history(user_id: str = Depends(get_current_user)):
    """Fetches the last 5 analysis reports for the authenticated user."""
    docs = db.collection('analyses').document(user_id).collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream()
    
    history = []
    for doc in docs:
        data = doc.to_dict()
        history.append({
            "id": doc.id,
            "timestamp": data['timestamp'].isoformat(),
            "report": data['report'],
            "summary": data.get('summary', 'Analysis Report')
        })
    return history

