import os
import sys
import zipfile
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# ==========================================
# 1. CONFIGURATION (Dynamic & Portable)
# ==========================================
# Automatically detect current directory (works on Linux, Windows, and PyInstaller binaries)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MATCHED_SPONSORS_FILE = os.path.join(BASE_DIR, 'matched_sponsors_with_industries.csv')
FINAL_OUTPUT = os.path.join(BASE_DIR, 'nuclear_matches.csv')

# Adzuna API Credentials (Replace with placeholders for public upload)
APP_ID = 'YOUR_ADZUNA_APP_ID'
APP_KEY = 'YOUR_ADZUNA_APP_KEY'

print("\n" + "="*50)
print("🚀 LAUNCHING JOB HUNTER PRO")
print("="*50)

# Get Job Titles via interactive prompt
raw_queries = input("\nEnter job titles (separated by commas)\n[Press Enter for defaults]: ")
if raw_queries.strip():
    QUERIES = [q.strip() for q in raw_queries.split(',')]
else:
    QUERIES = [
        "Revenue Operations", "Technical Project Manager", "Salesforce Administrator",
        "CRM Manager", "Marketing Operations", "Sales Operations", 
        "Automation Manager", "Business Systems Manager", "Technical PM", "Salesforce"
    ]

# Get Industries via interactive prompt
raw_industries = input("\nEnter target industries (separated by commas)\n[Press Enter for defaults]: ")
if raw_industries.strip():
    TARGET_INDUSTRIES = [i.strip().upper() for i in raw_industries.split(',')]
else:
    TARGET_INDUSTRIES = [
        'SOFTWARE', 'COMPUTER', 'INFORMATION', 'DATA', 
        'CONSULTANCY', 'TECHNOLOGY', 'MANAGEMENT', 'CLOUD'
    ]

# ==========================================
# 2. AUTOMATIC DATA RETRIEVAL (Web Scraping)
# ==========================================
def download_file(url, dest):
    print(f"Downloading {os.path.basename(dest)}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

print("\n[+] Fetching latest datasets from Government & Companies House...")

# 2a. Gov UK Sponsor List
gov_url = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
res = requests.get(gov_url)
soup = BeautifulSoup(res.text, 'html.parser')

csv_tag = soup.find('a', href=lambda href: href and '.csv' in href.lower() and 'worker' in href.lower())
if not csv_tag:
    print("Error: Could not find the Sponsor CSV on GOV.UK")
    exit()

csv_link = csv_tag['href']
if csv_link.startswith('/'):
    csv_link = "https://www.gov.uk" + csv_link

SPONSOR_FILE = os.path.join(BASE_DIR, csv_link.split('/')[-1])
if not os.path.exists(SPONSOR_FILE):
    download_file(csv_link, SPONSOR_FILE)

# 2b. Companies House Data
ch_url = "https://download.companieshouse.gov.uk/en_output.html"
res = requests.get(ch_url)
soup = BeautifulSoup(res.text, 'html.parser')

zip_tag = soup.find('a', href=lambda href: href and 'BasicCompanyDataAsOneFile' in href)
if not zip_tag:
    print("Error: Could not find the Companies House ZIP.")
    exit()

zip_link = zip_tag['href']
if not zip_link.startswith('http'):
    zip_link = "https://download.companieshouse.gov.uk/" + zip_link

zip_file_path = os.path.join(BASE_DIR, zip_link.split('/')[-1])

if not os.path.exists(MATCHED_SPONSORS_FILE):
    if not os.path.exists(zip_file_path):
        download_file(zip_link, zip_file_path)
    
    print("Ensuring Companies House Data is extracted...")
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        csv_filename = zip_ref.namelist()[0]
        BIG_FILE = os.path.join(BASE_DIR, csv_filename)
        
        if not os.path.exists(BIG_FILE):
            print(f"Extracting {csv_filename} (this takes a moment)...")
            zip_ref.extract(csv_filename, BASE_DIR)
else:
    BIG_FILE = "" 
    
print("[+] Datasets verified and ready.\n")

# ==========================================
# 3. PHASE 1: THE BIG MERGE (Sponsors + SIC Codes)
# ==========================================
def standardize(series):
    return series.astype(str).str.upper().str.replace(r'\b(LTD|LIMITED|PLC|LLP)\b', '', regex=True).str.strip()

if not os.path.exists(MATCHED_SPONSORS_FILE):
    print("Phase 1: Building the VIP Sponsor List...")
    sponsors = pd.read_csv(SPONSOR_FILE, encoding='ISO-8859-1')
    sponsors['MatchKey'] = standardize(sponsors['Organisation Name'])
    
    results = []
    chunk_count = 0
    industry_pattern = '|'.join(TARGET_INDUSTRIES)
    
    for chunk in pd.read_csv(BIG_FILE, chunksize=200000, encoding='ISO-8859-1', low_memory=False):
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
        if chunk_count % 5 == 0:
            print(f"  ...Processed {chunk_count * 200000} rows...")

    if results:
        final_df = pd.concat(results).drop_duplicates(subset=['CompanyName'])
        final_df.to_csv(MATCHED_SPONSORS_FILE, index=False)
        print(f"Success! VIP list saved to {MATCHED_SPONSORS_FILE}")
    else:
        print("Error: No matches found during the merge. Please check your source files.")
        exit()
else:
    print("Phase 1 Skipped: VIP Sponsor list already exists.")

# ==========================================
# 4. PHASE 2: ADZUNA JOB SEARCH
# ==========================================
print("\nPhase 2: Querying Adzuna...")
df = pd.read_csv(MATCHED_SPONSORS_FILE, low_memory=False)

sponsor_list = df['CompanyName'].str.upper().str.replace(' LTD', '').str.replace(' LIMITED', '').unique().tolist()
sponsor_set = set(sponsor_list)

all_matches = []

for query in QUERIES:
    print(f"Hunting for: {query}...")
    for page in range(1, 6):
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}"
        params = {
            'app_id': APP_ID,
            'app_key': APP_KEY,
            'results_per_page': 50,
            'what': query,
            'content-type': 'application/json'
        }
        
        try:
            r = requests.get(url, params=params)
            data = r.json()
            
            for job in data.get('results', []):
                title = job.get('title', '')
                desc = job.get('description', '').upper()
                company = job.get('company', {}).get('display_name', '').upper()
                
                is_sponsor = any(s in company for s in sponsor_set)
                mentions_visa = "SPONSOR" in desc or "VISA" in desc or "TIER 2" in desc
                
                if is_sponsor or mentions_visa:
                    all_matches.append({
                        'Title': title,
                        'Company': company,
                        'Link': job.get('redirect_url'),
                        'Reason': "Verified Sponsor" if is_sponsor else "Mentions Sponsorship"
                    })
            time.sleep(0.5)
        except Exception as e:
            continue

if all_matches:
    results_df = pd.DataFrame(all_matches).drop_duplicates(subset=['Link'])
    results_df.to_csv(FINAL_OUTPUT, index=False)
    print(f"\nBOOM! Found {len(results_df)} leads. Check {FINAL_OUTPUT}")
else:
    print("\nNo jobs matching your criteria were found this time.")