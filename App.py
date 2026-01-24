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
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# --- إعداد الصفحة --- 
st.set_page_config(page_title="MOHRE Portal", layout="wide") 
st.title("HAMADA TRACING SITE TEST") 

# --- تحسين مظهر الجدول ---
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
    </style>
    """, unsafe_allow_html=True)

# --- إدارة جلسة العمل ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'deep_run_state' not in st.session_state:
    st.session_state['deep_run_state'] = 'stopped'
if 'deep_finished' not in st.session_state:
    st.session_state['deep_finished'] = False
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None

# قائمة الدول المبسطة
countries_list = ["Select Nationality", "India", "Pakistan", "Philippines", "Egypt", "Bangladesh", "Nepal", "Sri Lanka"]

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

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def apply_styling(df):
    # تعبئة القيم الفارغة بنص فارغ بدلاً من nan (لتحسين المظهر كما في صورتك)
    df_clean = df.fillna('')
    df_clean.index = range(1, len(df_clean) + 1)
    
    def color_status(val):
        color = '#90EE90' if val == 'Found' else '#FFCCCB' if val == 'Not Found' else 'white'
        return f'background-color: {color}'
        
    def color_expiry(val):
        try:
            if val and datetime.strptime(str(val), '%d/%m/%Y') < datetime.now():
                return 'color: red'
        except: pass
        return ''
        
    return df_clean.style.applymap(color_status, subset=['Status']).applymap(color_expiry, subset=['Card Expiry'] if 'Card Expiry' in df_clean.columns else [])

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # تعطيل subprocess لتوافق أعلى مع بايثون 3.13
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)

def extract_data(passport, nationality, dob_str):
    time.sleep(random.uniform(2, 4))
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
            search_box.send_keys(nationality)
            time.sleep(1.5)
            items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
            if items: items[0].click()
        except: pass
        
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)
        
        def gv(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1]"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return ''
            
        card = gv("Card Number")
        if not card: return None
        
        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": GoogleTranslator(source='auto', target='en').translate(gv("Job Description")) if gv("Job Description") else 'N/A',
            "Card Number": card, "Card Expiry": gv("Card Expiry"),
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None
    finally:
        try: driver.quit()
        except: pass

def deep_extract_by_card(card_number):
    driver = setup_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 20)
        # البحث عن الكابتشا وإدخال البيانات (محاكاة)
        time.sleep(5)
        return {'Name': 'FULL NAME FROM SITE', 'Est Name': 'ESTABLISHMENT NAME', 'Company Code': '778899'}
    except: return None
    finally:
        try: driver.quit()
        except: pass

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing (Excel)"]) 

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, format="DD/MM/YYYY")
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality":
            with st.spinner("Searching Stage 1..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                st.session_state.single_result = res
    
    if st.session_state.single_result:
        st.table(apply_styling(pd.DataFrame([st.session_state.single_result])))

with tab2:
    st.subheader("Batch Control")
    up = st.file_uploader("Upload Excel File", type=["xlsx"]) 
    
    if up:
        df_orig = pd.read_excel(up)
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume"): st.session_state.run_state = 'running'
        if col_ctrl2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if col_ctrl3.button("⏹️ Reset All"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.deep_finished = False
            st.rerun()

        prog = st.progress(0)
        table_area = st.empty()
        
        # المرحلة الأولى
        for i, row in df_orig.iterrows():
            if st.session_state.run_state != 'running' or i < len(st.session_state.batch_results):
                continue
            
            p = str(row.get('Passport Number', ''))
            n = str(row.get('Nationality', ''))
            try: d = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except: d = str(row.get('Date of Birth', ''))
            
            res = extract_data(p, n, d)
            st.session_state.batch_results.append(res if res else {"Passport Number": p, "Nationality": n, "Date of Birth": d, "Status": "Not Found"})
            
            table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
            prog.progress((i + 1) / len(df_orig))

        if len(st.session_state.batch_results) == len(df_orig) and len(df_orig) > 0:
            st.success("Stage 1 Finished!")
            
            # المرحلة الثانية (البحث العميق)
            if not st.session_state.deep_finished:
                if st.button("🚀 Run Deep Search (Stage 2)"):
                    st.session_state.deep_run_state = 'running'
            
            if st.session_state.deep_run_state == 'running':
                for idx, item in enumerate(st.session_state.batch_results):
                    if item.get('Status') == 'Found' and 'Name' not in item:
                        d_res = deep_extract_by_card(item['Card Number'])
                        if d_res: st.session_state.batch_results[idx].update(d_res)
                        table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
                st.session_state.deep_run_state = 'stopped'
                st.session_state.deep_finished = True
                st.rerun()

            # أزرار التحميل الثابتة
            st.divider()
            c_d1, c_d2 = st.columns(2)
            c_d1.download_button("📥 Download Stage 1", data=to_excel(pd.DataFrame(st.session_state.batch_results)), file_name="stage1_results.xlsx")
            if st.session_state.deep_finished:
                c_d2.download_button("📥 Download Final Deep Results", data=to_excel(pd.DataFrame(st.session_state.batch_results)), file_name="final_deep_results.xlsx")
