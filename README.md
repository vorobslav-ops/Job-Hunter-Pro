# 🚀 Job Hunter Pro Dashboard & ATS

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/remkiraops)

A fully visual, interactive Applicant Tracking System (ATS) web application that cross-references the UK Government's Visa Sponsor list with the Companies House database to find tech companies actively sponsoring visas, and then hunts for matching job postings on Adzuna. Now featuring a 100% offline AI email sorter!

---

## 🧠 Core Features

*   **🎯 Tab 1: Review Queue:** Pings the Adzuna API using multi-title queries to find open roles. Flags jobs instantly if the hiring company is on your VIP Sponsor List or mentions visa sponsorship, allowing you to review cards and save them to your database with one click.
*   **📊 Tab 2: My ATS Dashboard:** A fully editable, SQLite-backed application tracking system. Manage your application statuses (Applied, Interview Scheduled, Ghosted, Rejected) with an automated 30-day follow-up alert metric.
*   **⚙️ Tab 3: The Big Merge:** A built-in data pipeline that automatically scrapes millions of rows from GOV.UK and Companies House to build your VIP list. Features dual-filtering modes: use default Tech/SaaS SIC codes or input custom 5-digit UK SIC codes directly in the UI.
*   **📨 Tab 4: Autonomous AI Inbox Sorter:** Securely fetches recent unread job-related emails from your Gmail and classifies them completely locally (offline) into *Interview*, *Rejection*, *Next Steps*, or *Other* using the Ollama `phi3` AI model.

---

## 💻 Hardware Recommendations for Local AI

Tab 4 utilizes an entirely local Large Language Model to ensure maximum privacy. 
*   **Optimal Performance:** A dedicated GPU (e.g., NVIDIA RTX 3060 Mobile or equivalent) and 14GB+ of system RAM will process and categorize emails in milliseconds. 
*   **Minimum Requirements:** The AI will automatically fall back to CPU inference if a compatible GPU is unavailable, which will simply take a few seconds longer per email.

---

## 🔑 Prerequisites & Setup

You need to configure three basic integrations before running the app for the first time.

**1. Adzuna API (Job Searching)**
1. Go to [developer.adzuna.com](https://developer.adzuna.com/) and register for a free account.
2. Create a new application in your developer dashboard to generate your **App ID** and **App Key**.
3. Create a `.env` file in the root directory and add your keys:
    ```env
    ADZUNA_APP_ID="your_app_id_here"
    ADZUNA_APP_KEY="your_app_key_here"
    ```

**2. Gmail API (Inbox Connection)**
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API** and configure the OAuth Consent Screen (ensure you add your email address as a Test User).
3. Create a Desktop App OAuth Client ID.
4. Download the JSON file, rename it exactly to `credentials.json`, and place it in the project directory alongside your `.env` file.

**3. Ollama (Local AI Engine)**
1. Download and install [Ollama](https://ollama.com/) on your system.
2. Open your terminal and pull the required lightweight model:
    ```bash
    ollama pull phi3
    ```

---

## 🛠️ How to Use (Pre-Compiled Binaries)

Standalone executables are available for Windows and Linux in the GitHub Releases/Actions tab. These binaries contain a bundled local web server and do not require Python to be installed.

### For Windows:
1. Download `Job-Hunter-Pro-Windows.exe` and place it in a folder alongside your `.env` and `credentials.json` files.
2. Double-click the executable. A terminal will briefly flash, and your default web browser will automatically open to `http://localhost:8501`.

### For Linux (Ubuntu / Pop!_OS):
1. Download `Job-Hunter-Pro-Linux` and place it in a folder alongside your `.env` and `credentials.json` files.
2. Right-click the file -> **Properties** -> **Permissions** -> check **Allow executing file as program**.
3. Double-click to launch, or run from terminal: `./Job-Hunter-Pro-Linux`

---

## 💻 How to Run from Source (For Developers)

1. **Clone this repository:**
    ```bash
    git clone [https://github.com/vorobslav-ops/Job-Hunter-Pro.git](https://github.com/vorobslav-ops/Job-Hunter-Pro.git)
    cd Job-Hunter-Pro
    ```

2. **Set up a virtual environment and install dependencies:**
    ```bash
    python3 -m venv job_env
    source job_env/bin/activate
    pip install -r requirements.txt
    ```

3. **Launch the ATS:**
    ```bash
    streamlit run app.py
    ```

---

## ☕ Support the Project

If Job Hunter Pro helped you land a role, automated your workflow, or saved you hours of manual job searching, consider supporting development!

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/remkiraops)