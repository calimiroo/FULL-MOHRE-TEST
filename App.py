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

# --- إعداد الصفحة وتطبيق التحديث الجديد للعرض --- 
st.set_page_config(page_title="MOHRE Portal", layout="wide") 
st.title("HAMADA TRACING SITE TEST") 

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
if 'single_search_result' not in st.session_state:
    st.session_state['single_search_result'] = None

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

# --- وظائف مساعدة ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- وظيفة البحث الأساسي (MOHRE Portal) ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
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
        time.sleep(6)

        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip() or 'Not Found'
            except: return 'Not Found'

        card_num = get_value("Card Number")
        if card_num == 'Not Found': return None

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num, "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"), "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"), "Status": "Found",
            "Name": "", "Est Name": "", "Company Code": "", "Designation": ""
        }
    except: return None
    finally: driver.quit()

# --- وظيفة البحث العميق المحسّنة (Inquiry Portal) ---
def deep_extract_by_card(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(4)
        
        # 1. اختيار نوع الخدمة
        try:
            btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
            btn.click()
            time.sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
            for item in items:
                if 'EWPI' in item.get_attribute('value') or 'Work Permit' in item.text:
                    driver.execute_script("arguments[0].click();", item)
                    break
        except: return None

        time.sleep(2)
        
        # 2. إدخال رقم البطاقة والبحث عن الكابتشا الرقمية
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            captcha_val = ""
            # البحث عن نص مكون من 4 أرقام في الصفحة
            page_text = driver.find_element(By.TAG_NAME, "body").text
            import re
            numbers = re.findall(r'\b\d{4}\b', page_text)
            if numbers: captcha_val = numbers[0]

            card_field = None
            captcha_field = None
            for inp in inputs:
                p = (inp.get_attribute('placeholder') or '').lower()
                if 'captcha' in p or 'تحقق' in p: captcha_field = inp
                else: card_field = inp
            
            if card_field: card_field.send_keys(card_number)
            if captcha_field and captcha_val: captcha_field.send_keys(captcha_val)
            
            time.sleep(1)
            # النقر على زر البحث
            btns = driver.find_elements(By.TAG_NAME, "button")
            for b in btns:
                if any(x in b.text.lower() for x in ['search', 'بحث', 'view']):
                    driver.execute_script("arguments[0].click();", b)
                    break
            time.sleep(5)
        except: pass

        # 3. استخراج النتائج
        def find_res(label):
            try:
                # محاولة البحث عن النص المجاور للعنوان
                elem = driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following-sibling::*")
                return elem.text.strip() or 'Not Found'
            except: return 'Not Found'

        res = {
            'Name': find_res('Name'),
            'Est Name': find_res('Est Name') if find_res('Est Name') != 'Not Found' else find_res('Establishment'),
            'Company Code': find_res('Company Code') if find_res('Company Code') != 'Not Found' else find_res('Est Code'),
            'Designation': find_res('Designation') if find_res('Designation') != 'Not Found' else find_res('Job Title')
        }
        
        if all(v == 'Not Found' for v in res.values()): return None
        return res
    except: return None
    finally: driver.quit()

# --- الواجهة البرمجية ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"]) 

with tab1:
    st.subheader("Person Inquiry")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number")
    n_in = c2.selectbox("Nationality", countries_list)
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1))
    
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("🔍 Run Basic Search", use_container_width=True):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                st.session_state['single_search_result'] = res
                if not res: st.error("No record found in basic portal.")
        else: st.warning("Please fill all fields.")

    if st.session_state.get('single_search_result'):
        st.subheader("📋 Results")
        # التعديل الجديد هنا لإزالة التحذير
        st.dataframe(pd.DataFrame([st.session_state['single_search_result']]).style.map(color_status, subset=['Status']), width="stretch")
        
        if col_b2.button("🔎 Run Deep Search", use_container_width=True):
            card = st.session_state['single_search_result'].get('Card Number')
            if card and card != 'Not Found':
                with st.spinner("Accessing Inquiry Portal..."):
                    deep = deep_extract_by_card(card)
                    if deep:
                        st.session_state['single_search_result'].update(deep)
                        st.success("Deep data retrieved!")
                        st.rerun()
                    else: st.error("Deep search failed. Captcha might be incorrect or site timed out.")

with tab2:
    st.subheader("Excel Batch Upload")
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        df = pd.read_excel(up)
        # التعديل الجديد هنا لإزالة التحذير
        st.dataframe(df.head(), width="stretch")
        
        c_ctrl1, c_ctrl2, c_ctrl3 = st.columns(3)
        if c_ctrl1.button("▶️ Start"): st.session_state.run_state = 'running'
        if c_ctrl2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if c_ctrl3.button("⏹️ Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.rerun()

        if st.session_state.run_state != 'stopped':
            progress = st.progress(0)
            table_area = st.empty()
            
            for i, row in df.iterrows():
                if st.session_state.run_state == 'paused':
                    st.warning("Processing paused...")
                    break
                if i < len(st.session_state.batch_results): continue
                
                p = str(row.get('Passport Number', '')).strip()
                n = str(row.get('Nationality', '')).strip()
                try: d = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: d = ""
                
                res = extract_data(p, n, d)
                if not res:
                    res = {"Passport Number": p, "Status": "Not Found", "Card Number": "N/A"}
                
                st.session_state.batch_results.append(res)
                progress.progress((i+1)/len(df))
                # التعديل الجديد هنا لإزالة التحذير
                table_area.dataframe(pd.DataFrame(st.session_state.batch_results).style.map(color_status, subset=['Status']), width="stretch")
            
            if len(st.session_state.batch_results) == len(df):
                st.success("All basic records processed.")
                st.download_button("Download CSV", pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8'), "results.csv")
