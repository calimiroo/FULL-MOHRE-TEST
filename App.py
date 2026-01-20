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

# --- إعداد الصفحة الأساسي --- 
# تم تحديث الكود ليتوافق مع واجهة عام 2026
st.set_page_config(page_title="MOHRE Portal - Hamada Edition", layout="wide") 
st.title("🛡️ HAMADA TRACING SITE - VERSION 2026") 

# --- إدارة حالة الجلسة (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'single_search_result' not in st.session_state:
    st.session_state['single_search_result'] = None

# قائمة الجنسيات الكاملة كما هي مطلوبة في الموقع
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Egypt", "France", "Germany", "India", "Jordan", "Kuwait", "Lebanon", "Morocco", "Oman", "Pakistan", "Palestine", "Qatar", "Saudi Arabia", "Sudan", "Syria", "Tunisia", "Turkey", "UAE", "UK", "USA", "Yemen"]

# --- نظام تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.container():
        st.subheader("🔑 Login Required")
        with st.form("login_form"):
            pwd = st.text_input("Enter Access Password", type="password")
            if st.form_submit_button("Enter System"):
                if pwd == "Bilkish":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.error("Invalid Password.")
    st.stop()

# --- وظائف المساعدة ---
def get_driver():
    """تهيئة المتصفح المخفي مع إعدادات تخطي الحماية"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def translate_text(text):
    """ترجمة النصوص الوظيفية للعربية/الإنجليزية"""
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

def color_status(val):
    """تلوين حالة البحث في الجداول"""
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- البحث الأساسي (Portal 1) ---
def extract_basic_data(passport, nationality, dob):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        
        # إدخال البيانات
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        
        # اختيار الجنسية من القائمة المنبثقة
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()
        
        # إدخال تاريخ الميلاد
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(6)

        # استخراج القيم
        def fetch(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return "Not Found"

        card = fetch("Card Number")
        if card == "Not Found" or not card: return None

        return {
            "Passport": passport, "Nationality": nationality, "DOB": dob,
            "Job": translate_text(fetch("Job Description")),
            "Card Number": card, "Issue": fetch("Card Issue"),
            "Expiry": fetch("Card Expiry"), "Salary": fetch("Total Salary"),
            "Status": "Found"
        }
    except: return None
    finally: driver.quit()

# --- البحث العميق (Portal 2 - Inquiry) ---
def deep_search(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(4)
        
        # اختيار نوع البحث
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        btn.click()
        time.sleep(1)
        driver.execute_script("document.querySelectorAll('#dropdownList li')[1].click();") # اختيار EWPI
        
        time.sleep(2)
        # إدخال رقم البطاقة وفك الكابتشا النصية
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        page_source = driver.page_source
        captcha_code = re.findall(r'\b\d{4}\b', page_source) # محاولة استخراج كود من 4 أرقام
        
        card_input = None
        captcha_input = None
        for inp in inputs:
            placeholder = (inp.get_attribute('placeholder') or '').lower()
            if 'captcha' in placeholder or 'تحقق' in placeholder: captcha_input = inp
            else: card_input = inp
            
        if card_input: card_input.send_keys(card_number)
        if captcha_input and captcha_code: captcha_input.send_keys(captcha_code[0])
        
        # الضغط على بحث
        driver.find_element(By.XPATH, "//button[contains(., 'Search') or contains(., 'بحث')]").click()
        time.sleep(5)
        
        # استخراج البيانات الإضافية
        def get_deep(label):
            try:
                return driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following-sibling::*").text.strip()
            except: return "N/A"

        return {
            "Name": get_deep("Name"),
            "Establishment": get_deep("Est Name") or get_deep("Establishment"),
            "Company Code": get_deep("Company Code") or get_deep("Est Code"),
            "Designation": get_deep("Designation")
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم الرسومية ---
tab1, tab2 = st.tabs(["🔍 Single Search", "📂 Batch Processing"])

with tab1:
    st.subheader("Manual Individual Search")
    col1, col2, col3 = st.columns(3)
    p_num = col1.text_input("Passport Number", placeholder="E.g. L123456")
    nat = col2.selectbox("Nationality", countries_list)
    dob_val = col3.date_input("Date of Birth", min_value=datetime(1950,1,1))

    c_b1, c_b2 = st.columns(2)
    if c_b1.button("🚀 Run Basic Search", use_container_width=True):
        if p_num and nat != "Select Nationality":
            with st.spinner("Accessing MOHRE Portal..."):
                res = extract_basic_data(p_num, nat, dob_val.strftime("%d/%m/%Y"))
                if res:
                    st.session_state['single_search_result'] = res
                    st.success("Data Found!")
                else:
                    st.error("No record found for these details.")
        else: st.warning("Please fill all fields.")

    if st.session_state['single_search_result']:
        # عرض النتائج باستخدام العرض الجديد لتفادي التحذيرات
        st.write("### 📄 Results Found")
        res_df = pd.DataFrame([st.session_state['single_search_result']])
        st.dataframe(res_df.style.map(color_status, subset=['Status']), width="stretch")
        
        if c_b2.button("🕵️ Run Deep Search", use_container_width=True):
            with st.spinner("Extracting Deep Details..."):
                deep_res = deep_search(st.session_state['single_search_result']['Card Number'])
                if deep_res:
                    st.session_state['single_search_result'].update(deep_res)
                    st.success("Deep Search Completed!")
                    st.rerun()
                else:
                    st.error("Deep search failed. Captcha error or Timeout.")

with tab2:
    st.subheader("Excel Batch Search")
    file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        st.dataframe(df.head(), width="stretch")
        
        if st.button("▶️ Start Batch Process"):
            st.session_state.run_state = 'running'
            progress = st.progress(0)
            table_placeholder = st.empty()
            
            for i, row in df.iterrows():
                p = str(row.get('Passport Number', '')).strip()
                n = str(row.get('Nationality', '')).strip()
                d = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                
                result = extract_basic_data(p, n, d)
                if not result:
                    result = {"Passport": p, "Status": "Not Found"}
                
                st.session_state.batch_results.append(result)
                progress.progress((i + 1) / len(df))
                
                # تحديث الجدول لحظياً مع العرض الجديد
                table_placeholder.dataframe(pd.DataFrame(st.session_state.batch_results), width="stretch")
            
            st.success("Batch Processing Finished!")
            st.download_button("📥 Download Full Results", 
                             pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8'),
                             "mohre_results.csv")
