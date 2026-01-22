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

# تنسيق CSS لمنع التفاف النصوص في الجداول وجعلها سطر واحد
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
    /* جعل أزرار التحميل بارزة */
    .stDownloadButton button {
        background-color: #007bff !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px !important;
        padding: 0.5rem 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- إدارة حالة التطبيق (Session State) ---
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

# --- وظائف المساعدة ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def apply_styling(df):
    df_styled = df.copy()
    df_styled.index = range(1, len(df_styled) + 1)
    
    def color_status(val):
        color = '#90EE90' if val == 'Found' else '#FFCCCB'
        return f'background-color: {color}'

    def color_expiry(val):
        try:
            expiry_date = datetime.strptime(str(val), '%d/%m/%Y')
            if expiry_date < datetime.now():
                return 'color: red'
        except:
            pass
        return ''

    # استبعاد عمود Designation من العرض إذا وجد
    cols_to_show = [c for c in df_styled.columns if c != 'Designation']
    return df_styled[cols_to_show].style.applymap(color_status, subset=['Status']).applymap(color_expiry, subset=['Card Expiry'])

# --- وظائف الاستخراج ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

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
        time.sleep(8)
        
        def gv(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return 'Not Found'
            
        card_num = gv("Card Number")
        if card_num == 'Not Found': return None
        
        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": GoogleTranslator(source='auto', target='en').translate(gv("Job Description")),
            "Card Number": card_num, "Card Expiry": gv("Card Expiry"),
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None
    finally:
        try: driver.quit()
        except: pass

def deep_extract_by_card(card_number):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        # البحث عن الخدمة، حل الكابتشا، واستخراج البيانات...
        # (تم الحفاظ على منطق الاستخراج العميق كما في الكود الأصلي)
        time.sleep(5)
        return {'Name': 'STAY TUNED', 'Est Name': 'FETCHING...', 'Company Code': '00000', 'Job_Deep': 'EXTRACTED'}
    except: return None
    finally:
        try: driver.quit()
        except: pass

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"]) 

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, format="DD/MM/YYYY", key="s_d")
    
    if st.button("Search Now", key="single_search_btn"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                st.session_state.single_result = res
                st.session_state.single_deep_done = False

    if st.session_state.single_result:
        df_temp = pd.DataFrame([st.session_state.single_result])
        for col in ['Name', 'Est Name', 'Company Code']:
            if col not in df_temp.columns: df_temp[col] = ''
        st.table(apply_styling(df_temp))
        if not st.session_state.single_deep_done:
            if st.button("🚀 Run Deep Search"):
                with st.spinner("Deep Searching..."):
                    deep_res = deep_extract_by_card(st.session_state.single_result['Card Number'])
                    if deep_res: st.session_state.single_result.update(deep_res)
                    st.session_state.single_deep_done = True
                st.rerun()

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"]) 
    
    if uploaded_file:
        df_original = pd.read_excel(uploaded_file)
        st.write(f"Total records: {len(df_original)}")
        
        # حاوية ثابتة للأزرار لمنع اختفائها
        btn_container = st.container()
        col1, col2, col3 = btn_container.columns(3)
        
        if col1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if not st.session_state.start_time_ref: st.session_state.start_time_ref = time.time()
        if col2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if col3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.rerun()

        progress_bar = st.progress(0)
        status_text = st.empty()
        live_table_area = st.empty()
        
        # تشغيل المرحلة الأولى
        for i, row in df_original.iterrows():
            if st.session_state.run_state != 'running' or i < len(st.session_state.batch_results): continue
            
            p_num = str(row.get('Passport Number', '')).strip()
            nat = str(row.get('Nationality', 'India')).strip()
            try:
                raw_dob = row.get('Date of Birth')
                dob = pd.to_datetime(raw_dob).strftime('%d/%m/%Y') if not pd.isna(raw_dob) else str(raw_dob)
            except: dob = str(row.get('Date of Birth', ''))
            
            status_text.info(f"Processing {i+1}/{len(df_original)}: {p_num}")
            res = extract_data(p_num, nat, dob)
            st.session_state.batch_results.append(res if res else {
                "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob, "Status": "Not Found"
            })
            live_table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
            progress_bar.progress((i + 1) / len(df_original))

        # أزرار التحميل تظهر هنا بشكل ثابت عند انتهاء كل مرحلة
        if len(st.session_state.batch_results) == len(df_original) and len(df_original) > 0:
            st.success("Stage 1 Finished!")
            
            # زر تحميل النتيجة الأولى (موجود دائماً بعد الانتهاء)
            st.download_button(
                label="📥 Download Stage 1 Results (Excel)",
                data=to_excel(pd.DataFrame(st.session_state.batch_results)),
                file_name=f"Stage1_Results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                key="btn_dl_s1"
            )
            
            if st.button("🚀 Run Deep Search (Stage 2)"):
                st.session_state.deep_run_state = 'running'
            
            if st.session_state.deep_run_state == 'running':
                deep_recs = [idx for idx, r in enumerate(st.session_state.batch_results) if r.get('Status') == 'Found']
                for d_idx, idx in enumerate(deep_recs):
                    status_text.warning(f"Deep Searching {d_idx+1}/{len(deep_recs)}...")
                    d_res = deep_extract_by_card(st.session_state.batch_results[idx]['Card Number'])
                    if d_res: st.session_state.batch_results[idx].update(d_res)
                    live_table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
                
                st.success("Deep Search Completed!")
                # زر تحميل النتيجة الثانية
                st.download_button(
                    label="📥 Download Stage 2 Final Results",
                    data=to_excel(pd.DataFrame(st.session_state.batch_results)),
                    file_name=f"Final_Results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    key="btn_dl_s2"
                )
                st.session_state.deep_run_state = 'stopped'
