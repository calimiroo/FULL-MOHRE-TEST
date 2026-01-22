import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import re
import io
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# --- إعداد الصفحة وتحسين المظهر --- 
st.set_page_config(page_title="MOHRE Portal - Final", layout="wide") 
st.title("HAMADA TRACING SITE TEST") 

# تنسيق CSS لضمان عرض الجداول بشكل سطر واحد ومنع التفاف النص
st.markdown("""
    <style>
    .stTable td, .stTable th {
        white-space: nowrap !important;
        text-align: left !important;
        padding: 8px 15px !important;
    }
    .stTable {
        display: block !important;
        overflow-x: auto !important;
    }
    .stDownloadButton button {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- إدارة حالة التطبيق (Session State) - إصلاح خطأ السطر 39 ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'deep_run_state' not in st.session_state:
    st.session_state['deep_run_state'] = 'stopped'
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'single_deep_done' not in st.session_state:
    st.session_state['single_deep_done'] = False

# قائمة الجنسيات
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 

# --- تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("Protected Access")
        pwd_input = st.text_input("Enter Password", type="password")
        if st.form_submit_button("Login"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Incorrect Password.")
    st.stop()

# --- دوال المساعدة للتحميل والتنسيق ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def apply_styling(df):
    df_styled = df.copy()
    df_styled.index = range(1, len(df_styled) + 1)
    
    def color_status(val):
        return f'background-color: {"#90EE90" if val == "Found" else "#FFCCCB"}'

    def color_expiry(val):
        try:
            if datetime.strptime(str(val), '%d/%m/%Y') < datetime.now(): return 'color: red'
        except: pass
        return ''

    cols = [c for c in df_styled.columns if c != 'Designation']
    return df_styled[cols].style.applymap(color_status, subset=['Status']).applymap(color_expiry, subset=['Card Expiry'])

# --- وظائف الاستخراج (Stage 1 & 2) ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, use_subprocess=False)

def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
            search_box.send_keys(nationality)
            time.sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
            if items: items[0].click()
        except: pass
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)
        def gv(label):
            try: return driver.find_element(By.XPATH, f"//span[contains(text(), '{label}')]/following::span[1]").text.strip()
            except: return 'Not Found'
        card = gv("Card Number")
        if card == 'Not Found': return None
        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": GoogleTranslator(source='auto', target='en').translate(gv("Job Description")),
            "Card Number": card, "Card Expiry": gv("Card Expiry"),
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None
    finally: driver.quit()

def deep_extract(card_num):
    # محاكي للبحث العميق (يجب استبداله بكود Selenium الفعلي للبحث العميق)
    time.sleep(2)
    return {'Name': 'SUCCESS', 'Est Name': 'RECORDS FOUND', 'Company Code': 'ACTIVE'}

# --- واجهة المستخدم الرئيسية ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing (Excel)"])

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", format="DD/MM/YYYY", key="s_d")
    
    if st.button("Search Now"):
        with st.spinner("Searching..."):
            res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
            st.session_state.single_result = res
            st.session_state.single_deep_done = False

    if st.session_state.single_result:
        st.table(apply_styling(pd.DataFrame([st.session_state.single_result])))

with tab2:
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        df_orig = pd.read_excel(uploaded_file)
        col1, col2, col3 = st.columns(3)
        if col1.button("▶️ Start"): st.session_state.run_state = 'running'
        if col2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if col3.button("⏹️ Reset"): 
            st.session_state.batch_results = []
            st.rerun()

        status_area = st.empty()
        table_area = st.empty()

        for i, row in df_orig.iterrows():
            if st.session_state.run_state != 'running' or i < len(st.session_state.batch_results): continue
            p = str(row.get('Passport Number', ''))
            n = str(row.get('Nationality', ''))
            try: d = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except: d = str(row.get('Date of Birth', ''))
            
            status_area.info(f"Processing {i+1}/{len(df_orig)}")
            res = extract_data(p, n, d)
            st.session_state.batch_results.append(res if res else {"Passport Number": p, "Status": "Not Found"})
            table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))

        if len(st.session_state.batch_results) == len(df_orig) and len(df_orig) > 0:
            st.success("Stage 1 Finished!")
            # زر تحميل النتيجة الأولى
            st.download_button("📥 Download Stage 1 Results", data=to_excel(pd.DataFrame(st.session_state.batch_results)), file_name="stage1.xlsx")
            
            if st.button("🚀 Run Deep Search (Stage 2)"):
                st.session_state.deep_run_state = 'running'
            
            if st.session_state.deep_run_state == 'running':
                for idx, item in enumerate(st.session_state.batch_results):
                    if item.get('Status') == 'Found' and 'Name' not in item:
                        status_area.warning(f"Deep Searching: {item['Card Number']}")
                        d_res = deep_extract(item['Card Number'])
                        st.session_state.batch_results[idx].update(d_res)
                        table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
                st.success("Deep Search Completed!")
                # زر تحميل النتيجة الثانية
                st.download_button("📥 Download Stage 2 Results", data=to_excel(pd.DataFrame(st.session_state.batch_results)), file_name="final_results.xlsx")
