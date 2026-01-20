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

# --- إعداد الصفحة الرسمي لعام 2026 --- 
st.set_page_config(page_title="MOHRE Worker Tracking", layout="wide") 
st.title("🛡️ HAMADA TRACING SITE - VERSION 2.0 (2026)") 

# --- إدارة حالة الجلسة (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'single_search_result' not in st.session_state:
    st.session_state['single_search_result'] = None

# قائمة الجنسيات المعتمدة
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Egypt", "France", "Germany", "India", "Jordan", "Kuwait", "Lebanon", "Morocco", "Oman", "Pakistan", "Palestine", "Qatar", "Saudi Arabia", "Sudan", "Syria", "Tunisia", "Turkey", "UAE", "UK", "USA", "Yemen"]

# --- نظام تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.container():
        st.subheader("🔑 Access Required")
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Enter System"):
                if pwd == "Bilkish":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.error("Invalid Password.")
    st.stop()

# --- وظائف التشغيل الأساسية ---
def get_driver():
    """تهيئة المتصفح لتجاوز حماية البوتات"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # منع كشف الأتمتة
    options.add_argument('--disable-blink-features=AutomationControlled')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def translate_job(text):
    """ترجمة مسمى المهنة آلياً"""
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

def color_status(val):
    """تنسيق ألوان الحالة في الجداول"""
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- البحث الأساسي (Portal 1: MyContract) ---
def extract_basic_data(passport, nationality, dob):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4) # مهلة للتحميل
        
        # إدخال رقم الجواز
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        
        # اختيار الجنسية
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        # إدخال تاريخ الميلاد (تجاوز وضع القراءة فقط)
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def fetch_field(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "Not Found"

        card = fetch_field("Card Number")
        if card == "Not Found" or not card: return None

        return {
            "Passport": passport, "Nationality": nationality, "Date of Birth": dob,
            "Job Description": translate_job(fetch_field("Job Description")),
            "Card Number": card, "Card Issue": fetch_field("Card Issue"),
            "Card Expiry": fetch_field("Card Expiry"), "Total Salary": fetch_field("Total Salary"),
            "Status": "Found", "Name": "None", "Est Name": "None", "Company Code": "None", "Designation": "None"
        }
    except Exception as e:
        return None
    finally: driver.quit()

# --- البحث العميق (Portal 2: Inquiry - معالجة الكابتشا) ---
def deep_search_process(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)
        
        # اختيار نوع الخدمة (EWPI)
        wait = WebDriverWait(driver, 15)
        btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        btn.click()
        time.sleep(1)
        # النقر على خيار تصريح العمل الإلكتروني
        driver.execute_script("document.querySelectorAll('#dropdownList li')[1].click();")
        
        time.sleep(3)
        
        # استخراج كود الكابتشا (غالباً ما يكون نصاً ظاهراً في كود الصفحة)
        page_source = driver.page_source
        captcha_match = re.findall(r'\b\d{4}\b', page_source) # البحث عن كود من 4 أرقام
        
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        card_field = None
        captcha_field = None
        
        for inp in inputs:
            p_text = (inp.get_attribute('placeholder') or '').lower()
            if 'captcha' in p_text or 'تحقق' in p_text:
                captcha_field = inp
            else:
                card_field = inp
            
        if card_field: card_field.send_keys(card_number)
        if captcha_field and captcha_match: captcha_field.send_keys(captcha_match[0])
        
        # النقر على بحث
        driver.find_element(By.XPATH, "//button[contains(., 'Search') or contains(., 'بحث')]").click()
        time.sleep(6)
        
        def get_deep_val(label):
            try:
                # البحث عن القيمة بناءً على النص المجاور
                xpath = f"//*[contains(text(), '{label}')]/following-sibling::*"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "Not Found"

        return {
            "Name": get_deep_val("Name"),
            "Est Name": get_deep_val("Establishment Name") or get_deep_val("Est Name"),
            "Company Code": get_deep_val("Est Code") or get_deep_val("Company Code"),
            "Designation": get_deep_val("Designation") or get_deep_val("Job Title")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم الرسومية ---
tab1, tab2 = st.tabs(["🔍 Single Search", "📂 Batch Processing (Excel)"])

with tab1:
    st.subheader("Individual Worker Inquiry")
    c1, c2, c3 = st.columns(3)
    p_input = c1.text_input("Passport Number")
    n_input = c2.selectbox("Nationality", countries_list)
    d_input = c3.date_input("Date of Birth", min_value=datetime(1950,1,1))

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("🚀 Run Basic Search", use_container_width=True):
        if p_input and n_input != "Select Nationality":
            with st.spinner("Searching Portal 1..."):
                res = extract_basic_data(p_input, n_input, d_input.strftime("%d/%m/%Y"))
                if res:
                    st.session_state['single_search_result'] = res
                    st.success("✅ Basic record found!")
                else:
                    st.error("❌ No record found.")
        else: st.warning("Please enter all details.")

    if st.session_state['single_search_result']:
        st.write("### 📋 Basic Information")
        # استخدام التحديث الجديد width="stretch" لمنع الأخطاء الظاهرة في الصور
        res_df = pd.DataFrame([st.session_state['single_search_result']])
        st.dataframe(res_df.style.map(color_status, subset=['Status']), width="stretch")
        
        if col_btn2.button("🕵️ Run Deep Search", use_container_width=True):
            card_num = st.session_state['single_search_result'].get('Card Number')
            if card_num and card_num != "Not Found":
                with st.spinner("Decoding Inquiry Portal..."):
                    deep_data = deep_search_process(card_num)
                    if deep_data:
                        st.session_state['single_search_result'].update(deep_data)
                        st.success("✅ Deep details retrieved!")
                        st.rerun()
                    else:
                        st.error("❌ Deep search failed (Captcha or Timeout).")

with tab2:
    st.subheader("Bulk Excel Search")
    uploaded_file = st.file_uploader("Upload File (.xlsx)", type=["xlsx"])
    if uploaded_file:
        df_upload = pd.read_excel(uploaded_file)
        st.dataframe(df_upload.head(), width="stretch")
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        if col_ctrl1.button("▶️ Start Batch Process", use_container_width=True):
            st.session_state.run_state = 'running'
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            table_placeholder = st.empty()
            
            for i, row in df_upload.iterrows():
                if st.session_state.run_state == 'stopped': break
                
                pass_no = str(row.get('Passport Number', '')).strip()
                nat_name = str(row.get('Nationality', '')).strip()
                try: 
                    birth_d = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: birth_d = ""
                
                status_placeholder.info(f"Processing ({i+1}/{len(df_upload)}): {pass_no}")
                
                res_item = extract_basic_data(pass_no, nat_name, birth_d)
                if not res_item:
                    res_item = {"Passport": pass_no, "Status": "Not Found", "Card Number": "N/A"}
                
                st.session_state.batch_results.append(res_item)
                progress_bar.progress((i + 1) / len(df_upload))
                
                # تحديث الجدول لحظياً
                table_placeholder.dataframe(pd.DataFrame(st.session_state.batch_results), width="stretch")
            
            st.success("✅ Batch processing completed!")
            csv_data = pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv_data, "mohre_full_results.csv", "text/csv")
