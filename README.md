# 🚀 Job Hunter Pro

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/remkiraops)

An automated, terminal-based application that cross-references the UK Government's Visa Sponsor list with the Companies House database to find tech companies actively sponsoring visas, and then hunts for matching job postings on Adzuna.

---

## 🧠 How It Works
1. **The Big Merge:** Automatically scrapes GOV.UK for the latest Worker Visa Sponsor list and Companies House for the UK business directory. It cross-references both datasets to build a VIP list of verified visa sponsors, aggressively filtering out non-tech industries (like retail or farming) using official SIC codes.
2. **The Job Hunt:** Pings the Adzuna API using your custom job titles to find open roles. It flags a job if the hiring company is on your VIP Sponsor List OR if the job description explicitly mentions visa sponsorship.

*Note: The script utilizes a "Smart Skip." It only downloads and crunches the massive Government datasets if your VIP list is missing or deleted, saving massive amounts of system resources on daily runs.*

---

## 🔑 Prerequisite: Get Free Adzuna API Credentials
Whether you run the pre-compiled app or run from source code, you need a free API key:
1. Go to [developer.adzuna.com](https://developer.adzuna.com/) and register for a free account.
2. Create a new application in your developer dashboard to generate your unique **App ID** and **App Key**.

---

## 🛠️ How to Use (No Python Required)
Pre-compiled standalone binaries are provided for both Linux and Windows. 

### For Linux (Pop!_OS / Ubuntu):
1. Open your terminal in the `Linux-Build` folder.
2. Make the file executable:
   chmod +x job-hunter-pro-linux
3. Run the application:
   ./job-hunter-pro-linux
4. Enter your Adzuna `App ID` and `App Key` when prompted in the terminal.

### For Windows:
1. Open the `Windows-Build` folder.
2. Double-click `job-hunter-pro.exe`.
3. Enter your Adzuna `App ID` and `App Key` when prompted in the command window.

---

## 💻 How to Run from Source (For Developers)
1. **Clone this repository:**
   git clone https://github.com/vorobslav-ops/Job-Hunter-Pro.git
   cd Job-Hunter-Pro

2. **Install dependencies:**
   pip install -r requirements.txt

3. **Add your keys:**
   Open `Source-Code/master_job_search.py` in your editor and replace `YOUR_ADZUNA_APP_ID` and `YOUR_ADZUNA_APP_KEY` with your credentials.

4. **Run the script:**
   python3 Source-Code/master_job_search.py

---

## ⚙️ Customization
When launched, the app prompts you for target job titles and industries (comma-separated). 

Pressing **Enter** directly uses the built-in default stack (*Salesforce, Technical PM, RevOps, CRM Manager, Automation Manager*) combined with default SaaS/Tech SIC keywords (*Software, Computer, Data, Consultancy, Cloud*).

---

## ☕ Support the Project
If Job Hunter Pro helped you land a role or saved you hours of manual job searching, consider supporting development!

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/remkiraops)