# =========================
# IMPORTS
# =========================
import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# =========================
# SESSION STATE
# =========================
defaults = {
    "authenticated": False,
    "run_state": "stopped",
    "batch_results": [],
    "start_time_ref": None,
    "deep_run_state": "stopped",
    "deep_progress": 0,
    "deep_single_card": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# LOGIN
# =========================
if not st.session_state["authenticated"]:
    with st.form("login"):
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()

# =========================
# UTILS
# =========================
def format_time(sec):
    return str(timedelta(seconds=int(sec)))

def translate(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text

def get_driver():
    opt = uc.ChromeOptions()
    opt.add_argument("--headless")
    opt.add_argument("--disable-blink-features=AutomationControlled")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    return uc.Chrome(options=opt, headless=True)

def color_status(val):
    return "background-color:#90EE90" if val == "Found" else "background-color:#FFCCCB"

# =========================
# FIRST SEARCH
# =========================
def extract_data(passport, nationality, dob):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 20)

        wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal input").send_keys(nationality)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal li a")[0].click()

        dob_el = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly')", dob_el)
        dob_el.send_keys(dob)

        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)

        def grab(label):
            try:
                return driver.find_element(By.XPATH, f"//*[contains(text(),'{label}')]/following::span[1]").text.strip()
            except:
                return "Not Found"

        card = grab("Card Number")
        if card == "Not Found":
            return None

        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob,
            "Job Description": translate(grab("Job Description")),
            "Card Number": card,
            "Card Issue": grab("Card Issue"),
            "Card Expiry": grab("Card Expiry"),
            "Basic Salary": grab("Basic Salary"),
            "Total Salary": grab("Total Salary"),
            "Status": "Found"
        }
    finally:
        driver.quit()

# =========================
# DEEP SEARCH (FIXED)
# =========================
def deep_extract_by_card(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 30)

        wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton"))).click()
        time.sleep(1)
        for li in driver.find_elements(By.CSS_SELECTOR, "#dropdownList li"):
            if "Electronic Work Permit" in li.text:
                li.click()
                break

        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        input_box.clear()
        input_box.send_keys(card_number)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
        time.sleep(5)

        page = driver.find_element(By.TAG_NAME, "body").text

        def extract(label):
            for line in page.split("\n"):
                if label in line:
                    return line.split(":")[-1].strip()
            return "Not Found"

        return {
            "Name": extract("Name"),
            "Est Name": extract("Est Name"),
            "Company Code": extract("Company Code"),
            "Designation": extract("Designation")
        }
    finally:
        driver.quit()

# =========================
# UI
# =========================
tab1, tab2 = st.tabs(["Single Search", "Batch Search"])

# ---------- SINGLE ----------
with tab1:
    c1, c2, c3 = st.columns(3)
    p = c1.text_input("Passport Number")
    n = c2.text_input("Nationality", "Egypt")
    d = c3.date_input("Date of Birth")

    if st.button("Search Now"):
        res = extract_data(p, n, d.strftime("%d/%m/%Y"))
        if res:
            st.success("Found")
            st.table(pd.DataFrame([res]))

            st.markdown(
                f"""
                ### 🔍 Deep Search
                **Card Number:**  
                <a href="?deep={res['Card Number']}" target="_self">{res['Card Number']}</a>
                """,
                unsafe_allow_html=True
            )

            st.session_state.deep_single_card = res["Card Number"]
        else:
            st.error("No result")

# ---------- AUTO DEEP ----------
if st.session_state.deep_single_card:
    st.info(f"Deep Searching Card: {st.session_state.deep_single_card}")
    deep = deep_extract_by_card(st.session_state.deep_single_card)
    st.table(pd.DataFrame([deep]))
    st.session_state.deep_single_card = None
