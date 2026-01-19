# ===============================
# HAMADA MOHRE FULL PROJECT
# Main + Deep Search (Single File)
# ===============================

import streamlit as st
import pandas as pd
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="HAMADA MOHRE FULL SYSTEM", layout="wide")
st.title("HAMADA MOHRE FULL SEARCH SYSTEM")

# ===============================
# SESSION STATE INIT
# ===============================
defaults = {
    "authenticated": False,
    "run_state": "stopped",
    "deep_run_state": "stopped",
    "batch_results": [],
    "deep_results": {},
    "start_time_ref": None,
    "deep_start_time": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===============================
# LOGIN
# ===============================
if not st.session_state.authenticated:
    with st.form("login"):
        st.subheader("Protected Access")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()

# ===============================
# HELPERS
# ===============================
def format_time(sec):
    return str(timedelta(seconds=int(sec)))

def translate_en(txt):
    try:
        if txt and txt != "Not Found":
            return GoogleTranslator(source="auto", target="en").translate(txt)
        return txt
    except:
        return txt

def get_driver(headless=True):
    opt = uc.ChromeOptions()
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    if headless:
        opt.add_argument("--headless=new")
    return uc.Chrome(options=opt, use_subprocess=False)

def color_status(val):
    return "background-color: #90EE90" if val == "Found" else "background-color: #FFCCCB"

# ===============================
# MAIN SEARCH FUNCTION (UNCHANGED LOGIC)
# ===============================
def extract_main(passport, nationality, dob):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)

        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)

        search = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search.send_keys(nationality)
        time.sleep(1)
        driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")[0].click()

        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.send_keys(dob)

        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def gv(lbl):
            try:
                xp = f"//span[contains(text(),'{lbl}')]/following::span[1]"
                v = driver.find_element(By.XPATH, xp).text.strip()
                return v if v else "Not Found"
            except:
                return "Not Found"

        card = gv("Card Number")
        if card == "Not Found":
            return None

        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob,
            "Card Number": card,
            "Card Issue": gv("Card Issue"),
            "Card Expiry": gv("Card Expiry"),
            "Basic Salary": gv("Basic Salary"),
            "Total Salary": gv("Total Salary"),
            "Status": "Found"
        }
    except:
        return None
    finally:
        driver.quit()

# ===============================
# DEEP SEARCH FUNCTION
# ===============================
def deep_search(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)

        # Select EWPI
        driver.find_element(By.ID, "dropdownButton").click()
        time.sleep(1)
        for li in driver.find_elements(By.CSS_SELECTOR, "#optionsList li"):
            if "Electronic Work Permit" in li.text:
                li.click()
                break

        time.sleep(2)
        driver.find_element(By.ID, "txtCardNumber").send_keys(card_number)

        # Inject CAPTCHA solver
        driver.execute_script("""
        (function(){
        const tryFill=()=>{
        const code=[...document.querySelectorAll('div,span,b,strong')]
        .map(e=>e.innerText.trim()).find(t=>/^\\d{4}$/.test(t));
        const inp=[...document.querySelectorAll('input')]
        .find(i=>i.placeholder?.includes("التحقق")||i.placeholder?.toLowerCase().includes("captcha"));
        if(code&&inp){inp.value=code;inp.dispatchEvent(new Event('input',{bubbles:true}));}
        else{setTimeout(tryFill,500);}
        };tryFill();})();
        """)

        time.sleep(3)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)

        def gv(lbl):
            try:
                xp = f"//label[contains(text(),'{lbl}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xp).text.strip()
            except:
                return "N/A"

        return {
            "Name": gv("Name"),
            "Designation": gv("Designation"),
            "Est Name": gv("Est Name"),
            "Company Code": gv("Company Code")
        }
    except:
        return None
    finally:
        driver.quit()

# ===============================
# UI
# ===============================
tab1, tab2 = st.tabs(["Single Search", "Batch Search"])

# ===============================
# SINGLE SEARCH
# ===============================
with tab1:
    c1, c2, c3 = st.columns(3)
    p = c1.text_input("Passport")
    n = c2.text_input("Nationality")
    d = c3.text_input("DOB DD/MM/YYYY")

    if st.button("Search"):
        with st.spinner("Searching..."):
            r = extract_main(p, n, d)
            if r:
                st.success("Found")
                df = pd.DataFrame([r])
                st.dataframe(df)

                if st.button(f"🔍 Deep Search Card {r['Card Number']}"):
                    with st.spinner("Deep Searching..."):
                        dr = deep_search(r["Card Number"])
                        if dr:
                            for k, v in dr.items():
                                df[k] = v
                            st.dataframe(df)
            else:
                st.error("Not Found")

# ===============================
# BATCH SEARCH
# ===============================
with tab2:
    file = st.file_uploader("Upload Excel", type="xlsx")
    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("▶ Start Batch"):
            st.session_state.run_state = "running"
            st.session_state.start_time_ref = time.time()

        if st.session_state.run_state == "running":
            for i, row in df.iterrows():
                res = extract_main(
                    str(row["Passport Number"]),
                    str(row["Nationality"]),
                    pd.to_datetime(row["Date of Birth"]).strftime("%d/%m/%Y")
                )
                if res:
                    st.session_state.batch_results.append(res)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": row["Passport Number"],
                        "Status": "Not Found"
                    })

                live = pd.DataFrame(st.session_state.batch_results)
                st.dataframe(live.style.applymap(color_status, subset=["Status"]))

            st.success("Main Batch Done")

        if st.session_state.batch_results:
            if st.button("🔍 Deep Search All Found"):
                for r in st.session_state.batch_results:
                    if r.get("Status") == "Found":
                        dr = deep_search(r["Card Number"])
                        if dr:
                            r.update(dr)
                final = pd.DataFrame(st.session_state.batch_results)
                st.dataframe(final)
                st.download_button(
                    "⬇ Download Final CSV",
                    final.to_csv(index=False).encode(),
                    "FULL_MOHRE_REPORT.csv"
                )
