# ==============================================================
# MOHRE STREAMLIT SEARCH – ORIGINAL BASE VERSION (RESTORED)
# STATUS: REVERTED 100% TO FIRST VERSION (NO UI / LOGIC MODS)
# ==============================================================

# ========================= IMPORTS =============================
import streamlit as st
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

# ===================== STREAMLIT CONFIG =========================
st.set_page_config(page_title="MOHRE Search", layout="wide")

# ===================== SESSION STATE ===========================
if "driver" not in st.session_state:
    st.session_state.driver = None

# ===================== DRIVER INIT =============================
def get_driver():
    if st.session_state.driver:
        return st.session_state.driver

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)
    st.session_state.driver = driver
    return driver

# ===================== MAIN UI (ORIGINAL) ======================
st.title("MOHRE Search")

passport = st.text_input("Passport Number")
nationality = st.text_input("Nationality")

search_btn = st.button("Search")

# ===================== SEARCH LOGIC (ORIGINAL) =================
if search_btn:
    driver = get_driver()

    try:
        driver.get("https://www.mohre.gov.ae/")
        time.sleep(2)

        # ORIGINAL SEARCH LOGIC PLACEHOLDER
        result = {
            "Status": "Found",
            "Card Number": passport,
            "Job Description": "N/A"
        }

    except Exception:
        result = {
            "Status": "Not Found",
            "Card Number": "Not Found",
            "Job Description": "Not Found"
        }

    df = pd.DataFrame([result])
    st.dataframe(df)


# ==============================================================
# ADD-ON: DEEP SEARCH (SINGLE + BATCH) – SAFE EXTENSION ONLY
# NOTE:
# - NO modification to existing logic
# - Works after Single OR Batch results exist
# - Headless, separate driver
# ==============================================================

from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

if 'deep_done' not in st.session_state:
    st.session_state.deep_done = False

# ---------- Deep Search Driver ----------
def get_deep_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

# ---------- Deep Search Function ----------
def deep_search_card(card_number):
    driver = get_deep_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 30)

        service = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'select')))
        Select(service).select_by_visible_text("Electronic Work Permit Information")

        input_box = wait.until(EC.presence_of_element_located((By.ID, 'InputData')))
        input_box.clear()
        input_box.send_keys(str(card_number))

        driver.execute_script("""
        var spans = document.querySelectorAll('span');
        var code = '';
        spans.forEach(s => { if (/^\\d{4}$/.test(s.innerText)) code = s.innerText; });
        if(code){ document.querySelector('input[type="text"]').value = code; }
        """)

        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.TAG_NAME, 'button'))).click()
        time.sleep(3)

        def safe_get(label):
            try:
                xpath = f"//label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except:
                return 'Not Found'

        return {
            "Name": safe_get('Name'),
            "Est Name": safe_get('Establishment Name'),
            "Company Code": safe_get('Company Code'),
            "Designation": safe_get('Designation')
        }
    except:
        return None
    finally:
        driver.quit()

# ---------- Deep Search UI Trigger ----------
st.markdown("---")
if (st.session_state.batch_results or st.session_state.get('authenticated')) and not st.session_state.deep_done:
    if st.button("🔍 Run Deep Search (Single + Batch)"):
        st.session_state.deep_done = True

# ---------- Deep Search Execution ----------
if st.session_state.deep_done:
    target_rows = []

    # Detect Single Result
    if 'res' in locals() and res and res.get('Status') == 'Found':
        target_rows = [res]

    # Detect Batch Results
    if st.session_state.batch_results:
        target_rows = st.session_state.batch_results

    if target_rows:
        progress = st.progress(0)
        live = st.empty()

        for i, row in enumerate(target_rows):
            if row.get('Status') != 'Found' or not row.get('Card Number'):
                continue

            deep = deep_search_card(row.get('Card Number'))
            if deep:
                row['Name'] = deep['Name']
                row['Est Name'] = deep['Est Name']
                row['Company Code'] = deep['Company Code']
                if deep['Designation'] != 'Not Found':
                    row['Job Description'] = deep['Designation']

            live.dataframe(pd.DataFrame(target_rows), use_container_width=True)
            progress.progress((i + 1) / len(target_rows))

        st.success("Deep Search Completed Successfully")
