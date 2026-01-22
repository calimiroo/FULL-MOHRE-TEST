import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import re
import io
import random
from selenium import webdriverimport streamlit as st
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

# --- إدارة جلسة العمل (Session State) ---
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

# --- دوال مساعدة ---
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
        return f'background-color: {"#90EE90" if val == "Found" else "#FFCCCB"}'
    def color_expiry(val):
        try:
            if datetime.strptime(str(val), '%d/%m/%Y') < datetime.now(): return 'color: red'
        except: pass
        return ''
    cols = [c for c in df_styled.columns if c != 'Designation']
    return df_styled[cols].style.applymap(color_status, subset=['Status']).applymap(color_expiry, subset=['Card Expiry'])

# --- وظائف الاستخراج ---
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

def deep_extract(card_number):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        # منطق اختيار الخدمة وحل الكابتشا...
        time.sleep(5)
        # استخراج الاسم والشركة...
        return {'Name': 'Sample Name', 'Est Name': 'Sample Est', 'Company Code': '12345', 'Job_Deep': 'Manager'}
    except: return None
    finally: driver.quit()

# --- الواجهة ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"]) 

with tab1:
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, format="DD/MM/YYYY", key="s_d")
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                st.session_state.single_result = res
                st.session_state.single_deep_done = False
    
    if st.session_state.single_result:
        df_s = pd.DataFrame([st.session_state.single_result])
        for col in ['Name', 'Est Name', 'Company Code']: 
            if col not in df_s.columns: df_s[col] = ''
        st.table(apply_styling(df_s))
        if not st.session_state.single_deep_done:
            if st.button("🚀 Run Deep Search"):
                with st.spinner("Deep Searching..."):
                    d_res = deep_extract(st.session_state.single_result['Card Number'])
                    if d_res: st.session_state.single_result.update(d_res)
                    st.session_state.single_deep_done = True
                    st.rerun()

with tab2:
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"]) 
    if uploaded_file:
        df_orig = pd.read_excel(uploaded_file)
        c_ctrl1, c_ctrl2, c_ctrl3 = st.columns(3)
        if c_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if not st.session_state.start_time_ref: st.session_state.start_time_ref = time.time()
        if c_ctrl2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if c_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.rerun()

        prog = st.progress(0)
        table_area = st.empty()
        
        for i, row in df_orig.iterrows():
            if st.session_state.run_state != 'running' or i < len(st.session_state.batch_results): continue
            p = str(row.get('Passport Number', '')).strip()
            n = str(row.get('Nationality', 'India')).strip()
            # إصلاح معالجة التاريخ لتجنب التحذيرات
            try:
                raw_dob = row.get('Date of Birth')
                dob = pd.to_datetime(raw_dob).strftime('%d/%m/%Y') if not pd.isna(raw_dob) else ""
            except: dob = str(raw_dob)

            res = extract_data(p, n, dob)
            st.session_state.batch_results.append(res if res else {
                "Passport Number": p, "Nationality": n, "Date of Birth": dob, "Status": "Not Found"
            })
            table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
            prog.progress((i + 1) / len(df_orig))

        if len(st.session_state.batch_results) == len(df_orig) and len(df_orig) > 0:
            st.success("Stage 1 Finished!")
            st.download_button("📥 Download Stage 1", data=to_excel(pd.DataFrame(st.session_state.batch_results)), file_name="results_s1.xlsx")
            
            if st.button("🚀 Run Deep Search (Stage 2)"):
                st.session_state.deep_run_state = 'running'
            
            if st.session_state.deep_run_state == 'running':
                for idx, rec in enumerate(st.session_state.batch_results):
                    if rec.get('Status') == 'Found' and 'Name' not in rec:
                        d_res = deep_extract(rec['Card Number'])
                        if d_res: st.session_state.batch_results[idx].update(d_res)
                        table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
                st.success("Deep Search Completed!")
                st.download_button("📥 Download Final Results", data=to_excel(pd.DataFrame(st.session_state.batch_results)), file_name="final_results.xlsx")
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# --- إعداد الصفحة --- 
st.set_page_config(page_title="MOHRE Portal", layout="wide") 
st.title("HAMADA TRACING SITE TEST") 

# --- تحسين مظهر الجدول وجعله سطر واحد (No Wrap) ومنع انقسام النص ---
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

# --- إدارة جلسة العمل (Session State) ---
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
if 'deep_progress' not in st.session_state:
    st.session_state['deep_progress'] = 0
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'single_deep_done' not in st.session_state:
    st.session_state['single_deep_done'] = False

# قائمة الجنسيات الكاملة
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

# --- دالة تحويل الوقت ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

# --- دالة تحويل الجدول لملف Excel ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- وظائف الاستخراج والترجمة ---
def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=en-US")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
    return driver

# دالة التنسيق والترقيم من 1
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

    # إخفاء عمود Designation تماماً في العرض
    cols_to_show = [c for c in df_styled.columns if c != 'Designation']
    return df_styled[cols_to_show].style.applymap(color_status, subset=['Status']).applymap(color_expiry, subset=['Card Expiry'])

# --- استخراج بيانات من الموقع الأول ---
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
            if items:
                items[0].click()
        except:
            pass
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)
        
        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except:
                return 'Not Found'
        
        card_num = get_value("Card Number")
        if card_num == 'Not Found':
            return None
            
        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num,
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"),
            "Status": "Found"
        }
    except:
        return None
    finally:
        try: driver.quit()
        except: pass

# --- وظيفة البحث العميق ---
def deep_extract_by_card(card_number):
    driver = setup_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        force_english(driver) 
        wait = WebDriverWait(driver, 20)
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Please select the service')]")))
        dropdown.click()
        time.sleep(1.5)
        service_opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information')]")))
        service_opt.click()
        input_box = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter data here']")))
        input_box.clear()
        input_box.send_keys(card_number)
        
        captcha_code = solve_captcha_using_your_script(driver)
        if captcha_code:
            captcha_field = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'captcha')]")
            captcha_field.clear()
            captcha_field.send_keys(captcha_code)
        else: return None
        
        driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]").click()
        time.sleep(5)
        if "No Data Found" in driver.page_source: return None
        else:
            comp_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Est Name')]/..").text.replace("Est Name", "").replace(":", "").strip()
            cust_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Name') and not(contains(text(), 'Est Name'))]/..").text.replace("Name", "").replace(":", "").strip()
            designation = driver.find_element(By.XPATH, "//*[contains(text(), 'Designation')]/..").text.replace("Designation", "").replace(":", "").strip()
            try:
                company_code = driver.find_element(By.XPATH, "//*[contains(text(), 'Company Code')]/..").text.replace("Company Code", "").replace(":", "").strip()
            except: company_code = 'Not Found'
            return {'Name': cust_name, 'Est Name': comp_name, 'Company Code': company_code, 'Job_Deep': designation}
    except: return None
    finally:
        try: driver.quit()
        except: pass

def force_english(driver):
    try:
        wait = WebDriverWait(driver, 10)
        lang_btn = wait.until(EC.presence_of_element_located((By.ID, "btnlanguage")))
        if "English" in lang_btn.text:
            driver.execute_script("arguments[0].click();", lang_btn)
            wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Please select the service"))
            time.sleep(2)
    except: pass

def solve_captcha_using_your_script(driver):
    try:
        elements = driver.find_elements(By.XPATH, "//div | //span | //b | //strong | //p")
        for el in elements:
            text = el.text.strip()
            if re.match(r'^\d{4}$', text): return text
    except: pass
    return None

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"]) 

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    # التعديل المطلوب: التاريخ بتنسيق DD/MM/YYYY
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), format="DD/MM/YYYY", key="s_d")
    
    if st.button("Search Now", key="single_search_button"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res:
                    st.session_state.single_result = res
                    st.session_state.single_deep_done = False
                else:
                    st.error("No data found.")
                    st.session_state.single_result = None

    if st.session_state.single_result:
        df_temp = pd.DataFrame([st.session_state.single_result])
        for col in ['Name', 'Est Name', 'Company Code']:
            if col not in df_temp.columns: df_temp[col] = ''
        st.table(apply_styling(df_temp))

        if st.session_state.single_result.get('Status') == 'Found' and not st.session_state.single_deep_done:
            if st.button("🚀 Run Deep Search", key="btn_deep_single"):
                with st.spinner("Deep Searching..."):
                    deep_res = deep_extract_by_card(st.session_state.single_result['Card Number'])
                    if deep_res:
                        st.session_state.single_result.update({
                            'Job Description': deep_res['Job_Deep'], 
                            'Name': deep_res['Name'],
                            'Est Name': deep_res['Est Name'], 
                            'Company Code': deep_res['Company Code']
                        })
                    st.session_state.single_deep_done = True
                st.rerun()

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"]) 
    
    if uploaded_file:
        df_original = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df_original)}")
        
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None: st.session_state.start_time_ref = time.time()
        if col_ctrl2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.rerun()

        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_area = st.empty()
        live_table_area = st.empty()
        
        # المرحلة الأولى: استخراج البيانات الأساسية
        for i, row in df_original.iterrows():
            while st.session_state.run_state == 'paused':
                status_text.warning("Paused...")
                time.sleep(1)
            if st.session_state.run_state == 'stopped': break
            
            if i < len(st.session_state.batch_results):
                progress_bar.progress((i + 1) / len(df_original))
                continue

            p_num = str(row.get('Passport Number', '')).strip()
            nat = str(row.get('Nationality', 'Egypt')).strip()
            try: dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except: dob = str(row.get('Date of Birth', ''))
                
            status_text.info(f"Processing {i+1}/{len(df_original)}: {p_num}")
            res = extract_data(p_num, nat, dob)
            
            st.session_state.batch_results.append(res if res else {
                "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                "Job Description": "N/A", "Card Number": "N/A", "Card Expiry": "N/A",
                "Basic Salary": "N/A", "Total Salary": "N/A", "Status": "Not Found"
            })
            
            elapsed = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            found_count = len([x for x in st.session_state.batch_results if x.get('Status') == 'Found'])
            stats_area.markdown(f"✅ **Success:** {found_count} | ⏱️ **Time:** {format_time(elapsed)}")
            live_table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
            progress_bar.progress((i + 1) / len(df_original))

        # عند انتهاء المرحلة الأولى
        if len(st.session_state.batch_results) == len(df_original) and len(st.session_state.batch_results) > 0:
            st.success("Stage 1 Finished!")
            
            # إعداد ملف المرحلة الأولى للتحميل
            df_stage1 = pd.DataFrame(st.session_state.batch_results)
            excel_data1 = to_excel(df_stage1)
            st.download_button("📥 Download Stage 1 Results", data=excel_data1, file_name="stage1_results.xlsx", key="dl_stage1")
            
            if st.button("🚀 Run Deep Search (Stage 2)"):
                st.session_state.deep_run_state = 'running'
            
            if st.session_state.deep_run_state == 'running':
                deep_bar = st.progress(0)
                deep_recs = [idx for idx, r in enumerate(st.session_state.batch_results) if r.get('Status') == 'Found']
                
                for d_idx, idx in enumerate(deep_recs):
                    card = st.session_state.batch_results[idx]['Card Number']
                    status_text.info(f"Deep Searching {d_idx+1}/{len(deep_recs)}: {card}")
                    d_res = deep_extract_by_card(card)
                    if d_res:
                        st.session_state.batch_results[idx].update({
                            'Name': d_res['Name'], 
                            'Est Name': d_res['Est Name'],
                            'Company Code': d_res['Company Code'], 
                            'Job Description': d_res['Job_Deep']
                        })
                    deep_bar.progress((d_idx + 1) / len(deep_recs))
                    live_table_area.table(apply_styling(pd.DataFrame(st.session_state.batch_results)))
                
                st.success("Deep Search Completed!")
                
                # إعداد ملف المرحلة الثانية للتحميل
                df_stage2 = pd.DataFrame(st.session_state.batch_results)
                excel_data2 = to_excel(df_stage2)
                st.download_button("📥 Download Stage 2 Results (Final)", data=excel_data2, file_name="final_deep_results.xlsx", key="dl_stage2")
                st.session_state.deep_run_state = 'stopped'
