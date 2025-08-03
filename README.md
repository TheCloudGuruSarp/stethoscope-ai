# Stethoscope AI 🩺

**Instant, AI-Powered Diagnostics for Your Linux Server.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

Stethoscope AI is an on-demand expert consultant for complex server issues. It allows any user to run a secure, read-only script on their Linux server, which generates a snapshot of the system's performance and security configuration. This snapshot is then analyzed by a powerful AI backend to provide a comprehensive health report with actionable insights and solutions.

---

## ✨ Key Features

* **AI-Powered Analysis:** Leverages Google's Gemini AI to provide human-like reasoning, root cause analysis, and expert recommendations.
* **Comprehensive Health Report:** Analyzes performance, security, package updates, and more.
* **Server Security Score:** Proactively identifies security vulnerabilities (SSH config, firewall status) and provides a score out of 100.
* **Outdated Package Detection:** Identifies critical software (like OpenSSH) that needs updating.
* **Agentless & Anonymous:** Uses a 100% read-only script. No agents to install, no user accounts needed, and no data is stored.
* **Instant Metrics Dashboard:** Visualizes key metrics like OS info, uptime, and expanded system information as soon as you provide the snapshot.

## 🚀 How It Works

The process is designed to be simple and secure:

1.  **Get The Command:** Copy the `curl` command from the web interface.
2.  **Run on Your Server:** Execute the command via SSH on any Linux server. It gathers a comprehensive snapshot and outputs a Base64 encoded string.
3.  **Get AI-Powered Insights:** Paste the output into the web app and instantly receive your detailed report.

## 🛠️ Technology Stack

This project is composed of three main parts:

| Component    | Technology                                                    | Description                                                                    |
| ------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Frontend** | `HTML`, `Tailwind CSS`, `JavaScript`, `Marked.js`             | A static, single-page application that serves as the user interface.           |
| **Backend** | `Python 3.10+`, `FastAPI`, `Uvicorn`                          | A high-performance API that handles data decoding and analysis.                |
| **AI** | `Google Gemini API`                                           | The core AI for analysis and generating human-readable reports.                |
| **Script** | `Bash`                                                        | The agentless, read-only script that collects server metrics.                  |

## ⚙️ Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Python 3.10+
* A Google Account for the Gemini API key.

### Installation & Setup

1.  **Clone the repo:**
    ```sh
    git clone [https://github.com/your_username/stethoscope-ai.git](https://github.com/your_username/stethoscope-ai.git)
    cd stethoscope-ai
    ```

2.  **Setup the Backend:**
    * Navigate to the backend directory: `cd backend`
    * Install Python dependencies: `pip install -r requirements.txt`
    * Create a `.env` file in the `backend` directory and populate it with your `GEMINI_API_KEY`. See the **Configuration** section below.
    * Run the backend server: `uvicorn main:app --reload`
    * The API will be available at `http://127.0.0.1:8000`.

3.  **Setup the Frontend:**
    * Open the `index.html` file in your browser. No build step is required.
    * **Important:** Make sure the `API_ENDPOINT` variable in the `<script>` section of `index.html` points to your backend URL (e.g., `http://127.0.0.1:8000`).

## 🔑 Configuration

The backend requires a `.env` file with the following environment variable:

* **`GEMINI_API_KEY`**: Your API key for the Google Gemini AI.

**Example `.env` file:**
GEMINI_API_KEY="AIzaSyAxxxxxxxxxxxx"
## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
