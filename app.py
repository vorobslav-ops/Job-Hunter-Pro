import streamlit as st
import sqlite3
import pandas as pd
import requests
import os
import zipfile
import time
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
load_dotenv()
APP_ID = os.getenv('ADZUNA_APP_ID')
APP_KEY = os.getenv('ADZUNA_APP_KEY')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHED_SPONSORS_FILE = os.path.join(BASE_DIR, 'matched_sponsors_with_industries.csv')
DB_FILE = os.path.join(BASE_DIR, 'job_tracker.db')

# Initialize SQLite Database
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS applications 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             title TEXT, company TEXT, link TEXT, 
             snippet TEXT, reason TEXT, status TEXT, 
             date_applied TEXT, last_updated TEXT)''')
conn.commit()

# Session State for Job Queue
if 'job_results' not in st.session_state:
    st.session_state.job_results = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

st.set_page_config(page_title="Job Hunter Pro ATS", page_icon="🚀", layout="wide")
st.title("🚀 Job Hunter Pro Dashboard & ATS")

# Helper function to load sponsor set
@st.cache_data
def load_sponsors():
    if os.path.exists(MATCHED_SPONSORS_FILE):
        df_sp = pd.read_csv(MATCHED_SPONSORS_FILE, low_memory=False)
        names = df_sp['CompanyName'].astype(str).str.upper().str.replace(r'\b(LTD|LIMITED|PLC|LLP)\b', '', regex=True).str.strip().unique().tolist()
        return set(names)
    return set()

sponsor_set = load_sponsors()

tab1, tab2, tab3 = st.tabs(["🎯 Review Queue", "📊 My ATS Dashboard", "⚙️ Update Sponsor Database"])

# ==========================================
# TAB 1: REVIEW QUEUE
# ==========================================
with tab1:
    st.header("Search & Review Sponsored Roles")
    
    col_q, col_pages = st.columns([3, 1])
    with col_q:
        query = st.text_input("Job Title / Query", placeholder="e.g., Salesforce Administrator, Technical PM, RevOps")
    with col_pages:
        num_pages = st.number_input("Adzuna Pages to Scan (50 jobs/page)", min_value=1, max_value=5, value=2)

    if st.button("🔍 Hunt for Verified Jobs", use_container_width=True):
        if not APP_ID or not APP_KEY:
            st.error("Missing Adzuna API Keys! Please make sure your .env file is set up.")
        elif not query.strip():
            st.warning("Please enter a job title to search.")
        elif not sponsor_set:
            st.warning("VIP Sponsor list is missing! Head over to the 'Update Sponsor Database' tab to generate it.")
        else:
            with st.spinner("Querying Adzuna and cross-referencing sponsors..."):
                found_jobs = []
                # Split the input into a list of individual job titles
                search_titles = [q.strip() for q in query.split(',') if q.strip()]
                
                for title in search_titles:
                    for page in range(1, int(num_pages) + 1):
                        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}"
                        params = {
                            'app_id': APP_ID,
                            'app_key': APP_KEY,
                            'results_per_page': 50,
                            'what': title,
                            'content-type': 'application/json'
                        }
                        try:
                            r = requests.get(url, params=params, timeout=10)
                            if r.status_code == 200:
                                data = r.json()
                                for job in data.get('results', []):
                                    job_title = job.get('title', 'Unknown Title')
                                    desc = job.get('description', '').upper()
                                    company = job.get('company', {}).get('display_name', 'Unknown').upper()
                                    
                                    clean_company = company.replace(" LTD", "").replace(" LIMITED", "").strip()
                                    is_sponsor = any(s in clean_company for s in sponsor_set) if sponsor_set else False
                                    mentions_visa = "SPONSOR" in desc or "VISA" in desc or "TIER 2" in desc
                                    
                                    if is_sponsor or mentions_visa:
                                        found_jobs.append({
                                            'title': job_title,
                                            'company': job.get('company', {}).get('display_name', 'Unknown'),
                                            'snippet': job.get('description', 'No description provided.'),
                                            'link': job.get('redirect_url', '#'),
                                            'reason': "Verified VIP Sponsor" if is_sponsor else "Mentions Visa in Posting"
                                        })
                            time.sleep(0.3)
                        except Exception as e:
                            st.error(f"Error fetching from Adzuna for {title}: {e}")

                st.session_state.job_results = found_jobs
                st.session_state.current_index = 0
                st.rerun()

    # Card Display
    if st.session_state.job_results:
        total = len(st.session_state.job_results)
        idx = st.session_state.current_index
        
        if idx < total:
            job = st.session_state.job_results[idx]
            
            st.divider()
            st.caption(f"Showing lead {idx + 1} of {total}")
            
            # Badge
            badge_color = "🟢" if "Verified" in job['reason'] else "🟡"
            st.markdown(f"### {job['title']}")
            st.markdown(f"**🏢 Company:** `{job['company']}` | **Match Type:** {badge_color} *{job['reason']}*")
            
            with st.container(border=True):
                st.write("**Job Snippet:**")
                st.write(job['snippet'])
                st.markdown(f"[👉 Click here to Open Official Job Posting]({job['link']})")

            col_sub, col_skip = st.columns(2)
            with col_sub:
                if st.button("✅ Submitted (Log to Dashboard)", use_container_width=True, type="primary"):
                    today = datetime.now().strftime("%Y-%m-%d")
                    c.execute("""INSERT INTO applications 
                                 (title, company, link, snippet, reason, status, date_applied, last_updated) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                              (job['title'], job['company'], job['link'], job['snippet'], job['reason'], "Applied", today, today))
                    conn.commit()
                    st.session_state.current_index += 1
                    st.rerun()
            with col_skip:
                if st.button("⏭️ Skip", use_container_width=True):
                    st.session_state.current_index += 1
                    st.rerun()
        else:
            st.success("🎉 You've reviewed all sponsored leads in this search batch!")

# ==========================================
# TAB 2: ATS DASHBOARD
# ==========================================
with tab2:
    st.header("Application Tracking System")
    
    df = pd.read_sql_query("SELECT id, title, company, status, reason, date_applied, last_updated, link FROM applications ORDER BY id DESC", conn)
    
    if not df.empty:
        # Calculate 30-day Follow Up
        applied_dates = pd.to_datetime(df['date_applied'], errors='coerce')
        days_passed = (pd.Timestamp.now() - applied_dates).dt.days
        df['Follow-Up Needed?'] = (days_passed >= 30) & (df['status'] == 'Applied')
        
        # Follow-Up Metric Highlights
        follow_ups_count = df['Follow-Up Needed?'].sum()
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Applications", len(df))
        col_m2.metric("Interviews Scheduled", (df['status'] == "Interview Scheduled").sum())
        col_m3.metric("Follow-ups Required (30+ Days)", follow_ups_count, delta="Action Needed" if follow_ups_count > 0 else None, delta_color="inverse")

        st.write("✏️ **Directly update application statuses below:**")
        edited_df = st.data_editor(
            df,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "status": st.column_config.SelectboxColumn("Status", options=["Applied", "Interview Scheduled", "Ghosted", "Rejected"], required=True),
                "link": st.column_config.LinkColumn("Posting Link"),
                "Follow-Up Needed?": st.column_config.CheckboxColumn("Follow-Up Alert", disabled=True),
                "title": st.column_config.TextColumn("Title", disabled=True),
                "company": st.column_config.TextColumn("Company", disabled=True),
                "reason": st.column_config.TextColumn("Reason", disabled=True),
                "date_applied": st.column_config.TextColumn("Date Applied", disabled=True),
                "last_updated": st.column_config.TextColumn("Last Updated", disabled=True)
            },
            hide_index=True,
            use_container_width=True
        )
        
        col_save, col_flw = st.columns([1, 2])
        with col_save:
            if st.button("💾 Save Status Changes", type="primary"):
                today = datetime.now().strftime("%Y-%m-%d")
                for _, row in edited_df.iterrows():
                    c.execute("UPDATE applications SET status = ?, last_updated = ? WHERE id = ?", 
                              (row['status'], today, int(row['id'])))
                conn.commit()
                st.success("Dashboard successfully updated!")
                st.rerun()

    else:
        st.info("No applications logged yet. Find jobs in the **Review Queue** tab and click 'Submitted' to start tracking!")

# ==========================================
# TAB 3: THE BIG MERGE
# ==========================================
with tab3:
    st.header("Update VIP Sponsor Database")
    st.write("Run this when you want to re-scrape the latest UK Visa lists and filter by industries.")
    
    st.write("**Industry Filtering Options**")
    filter_mode = st.radio(
        "Choose your SIC Code filtering mode:",
        ["Default (Tech & Consulting)", "Custom Keywords"]
    )
    
    if filter_mode == "Default (Tech & Consulting)":
        st.info("**Default mode active.** This searches the Companies House SIC descriptions for the following keywords:\n\n`SOFTWARE`, `COMPUTER`, `INFORMATION`, `DATA`, `CONSULTANCY`, `TECHNOLOGY`, `MANAGEMENT`, `CLOUD`")
        target_industries = ['SOFTWARE', 'COMPUTER', 'INFORMATION', 'DATA', 'CONSULTANCY', 'TECHNOLOGY', 'MANAGEMENT', 'CLOUD']
    else:
        st.info("**Custom mode active.** Enter UK SIC code descriptions or 5-digit codes (e.g., `62012` for Software Development, `FINANCE`, `MANUFACTURING`) you want to target.")
        custom_input = st.text_input("Enter custom SIC keywords (comma-separated):", "FINANCE, ACCOUNTING, 69201")
        target_industries = [i.strip().upper() for i in custom_input.split(',')]

    if st.button("⚡ Start Database Merge", type="primary"):
        with st.status("The Big Merge: Crunching Millions of Rows...", expanded=True) as status:
            
            st.write("📥 1/4 Downloading GOV.UK Sponsor List...")
            gov_url = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
            res = requests.get(gov_url)
            soup = BeautifulSoup(res.text, 'html.parser')
            csv_tag = soup.find('a', href=lambda h: h and '.csv' in h.lower() and 'worker' in h.lower())
            
            if not csv_tag:
                st.error("Could not find the Sponsor CSV on GOV.UK")
                st.stop()
                
            csv_link = csv_tag['href']
            if csv_link.startswith('/'):
                csv_link = "https://www.gov.uk" + csv_link
            
            SPONSOR_FILE = os.path.join(BASE_DIR, csv_link.split('/')[-1])
            with open(SPONSOR_FILE, 'wb') as f:
                f.write(requests.get(csv_link).content)
            st.write("✅ GOV.UK file ready.")

            st.write("📥 2/4 Fetching Companies House Directory (this takes a moment)...")
            ch_url = "https://download.companieshouse.gov.uk/en_output.html"
            res = requests.get(ch_url)
            soup = BeautifulSoup(res.text, 'html.parser')
            zip_tag = soup.find('a', href=lambda h: h and 'BasicCompanyDataAsOneFile' in h)
            
            if not zip_tag:
                st.error("Could not find the Companies House ZIP")
                st.stop()
                
            zip_link = zip_tag['href']
            if not zip_link.startswith('http'):
                zip_link = "https://download.companieshouse.gov.uk/" + zip_link
                
            zip_file_path = os.path.join(BASE_DIR, zip_link.split('/')[-1])
            
            if not os.path.exists(zip_file_path):
                with open(zip_file_path, 'wb') as f:
                    r = requests.get(zip_link, stream=True)
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            st.write("✅ Companies House ZIP ready.")

            st.write("📦 3/4 Extracting Massive CSV Database...")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                csv_filename = zip_ref.namelist()[0]
                BIG_FILE = os.path.join(BASE_DIR, csv_filename)
                if not os.path.exists(BIG_FILE):
                    zip_ref.extract(csv_filename, BASE_DIR)
            st.write("✅ Extraction complete.")

            st.write("🧠 4/4 Cross-Referencing Databases & Filtering Industries...")
            
            def standardize(series):
                return series.astype(str).str.upper().str.replace(r'\b(LTD|LIMITED|PLC|LLP)\b', '', regex=True).str.strip()

            sponsors = pd.read_csv(SPONSOR_FILE, encoding='ISO-8859-1')
            sponsors['MatchKey'] = standardize(sponsors['Organisation Name'])
            
            industry_pattern = '|'.join(target_industries)
            
            results = []
            chunk_count = 0
            progress_text = st.empty()
            
            for chunk in pd.read_csv(BIG_FILE, chunksize=200000, encoding='ISO-8859-1', low_memory=False, on_bad_lines='skip'):
                chunk.columns = chunk.columns.str.strip()
                chunk['MatchKey'] = standardize(chunk['CompanyName'])
                
                matched_chunk = chunk.merge(sponsors, on='MatchKey', how='inner')
                
                if not matched_chunk.empty:
                    keep_cols = ['CompanyName', 'SICCode.SicText_1', 'RegAddress.PostTown', 'CompanyStatus']
                    available_cols = [col for col in keep_cols if col in matched_chunk.columns]
                    
                    filtered_chunk = matched_chunk[matched_chunk['SICCode.SicText_1'].str.contains(industry_pattern, case=False, na=False, regex=True)]
                    
                    if not filtered_chunk.empty:
                        results.append(filtered_chunk[available_cols])
                        
                chunk_count += 1
                progress_text.write(f"Crunching chunk {chunk_count}: Processed {chunk_count * 200000} rows...")

            if results:
                final_df = pd.concat(results).drop_duplicates(subset=['CompanyName'])
                final_df.to_csv(MATCHED_SPONSORS_FILE, index=False)
                progress_text.write(f"✅ Success! Created VIP list with {len(final_df)} companies.")
                st.cache_data.clear() 
            else:
                st.error("No matches found during the merge.")
                
            status.update(label="Heavy Data Merge Complete!", state="complete")
        
        st.success("Sponsor database rebuilt successfully! The app is ready to hunt.")