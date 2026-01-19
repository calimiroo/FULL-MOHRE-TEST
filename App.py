import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal Pro", layout="wide")
st.title("MOHRE DATA TRACING SYSTEM (PRO)")

# --- إدارة جلسة العمل ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'single_res' not in st.session_state:
    st.session_state['single_res'] = None
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []

# قائمة الجنسيات
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- تسجيل الدخول ---
if not st.session_state['authenticated']:
    with st.form("login"):
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
    st.stop()

# --- تعريف الدرايفر (بدون ظهور المتصفح) ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

# --- دالة الترجمة ---
def translate_ar_to_en(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

# --- البحث الأول (Contract Search) ---
def extract_contract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        # اختيار الجنسية
        try:
            s_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
            s_box.send_keys(nationality)
            time.sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
            if items: items[0].click()
        except: pass

        # إدخال التاريخ
        dob_field = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_field)
        dob_field.clear()
        dob_field.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_field)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(5)

        def get_val(label):
            try:
                xp = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xp).text.strip()
            except: return 'Not Found'

        card = get_val("Card Number")
        if card == 'Not Found': return None

        return {
            "Passport": passport, "Nationality": nationality, "DOB": dob_str,
            "Card Number": card, "Job": translate_ar_to_en(get_val("Job Description")),
            "Basic": get_val("Basic Salary"), "Total": get_val("Total Salary"),
            "Expiry": get_val("Card Expiry"), "Status": "Found"
        }
    except: return None
    finally: driver.quit()

# --- البحث العميق المطور (Inquiry Search) ---
def deep_search_inquiry(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        time.sleep(3)

        # 1) النقر على Work Permit أولاً
        btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        btn.click()
        time.sleep(1)
        
        lis = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
        for li in lis:
            if 'Work Permit' in li.text:
                li.click()
                break
        time.sleep(1.5)

        # 2) النقر على Electronic Work Permit Information
        lis = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
        for li in lis:
            if 'Electronic Work Permit Information' in li.text or 'EWPI' in li.get_attribute('value'):
                li.click()
                break
        time.sleep(1)

        # 3) إدخال رقم البطاقة
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        for inp in inputs:
            ph = (inp.get_attribute('placeholder') or '').lower()
            if 'captcha' not in ph and 'التحقق' not in ph:
                inp.clear()
                inp.send_keys(card_number)
                break

        # 4) سكريبت تجاوز الكابتشا
        js_captcha = r"""
        try {
            const code = Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));
            const input = Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق") || i.placeholder.toLowerCase().includes("captcha"));
            if(code && input){
                input.value = code;
                input.dispatchEvent(new Event('input', {bubbles:true}));
            }
        } catch(e) {}
        """
        driver.execute_script(js_captcha)
        time.sleep(1)

        # 5) الضغط على بحث
        try:
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'بحث')]").click()
        
        time.sleep(5)

        # 6) استخراج البيانات
        def fetch(lbl):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{lbl}')]/following::span[1]").text.strip()
            except: return 'Not Found'

        return {
            'Name': fetch('Name'),
            'Est Name': fetch('Est Name') if fetch('Est Name') != 'Not Found' else fetch('Establishment Name'),
            'Company Code': fetch('Company Code'),
            'Designation': fetch('Designation')
        }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم (التنسيق) ---
t1, t2 = st.tabs(["Single Search", "Batch Processing"])

with t1:
    st.subheader("Individual Trace")
    col1, col2, col3 = st.columns(3)
    p_num = col1.text_input("Passport Number")
    nat_val = col2.selectbox("Nationality", countries_list)
    dob_val = col3.date_input("Date of Birth", value=None, min_value=datetime(1950,1,1))

    if st.button("Initial Search"):
        if p_num and nat_val != "Select Nationality" and dob_val:
            with st.spinner("Fetching Contract Data..."):
                res = extract_contract_data(p_num, nat_val, dob_val.strftime("%d/%m/%Y"))
                st.session_state.single_res = res
                if not res: st.error("No record found for this passport.")

    if st.session_state.single_res:
        res = st.session_state.single_res
        st.success("Phase 1 Complete!")
        st.table(pd.DataFrame([res]))

        # زر البحث العميق يظهر هنا بعد النتيجة الأولى
        if st.button(f"🔍 Run Deep Search for Card: {res['Card Number']}"):
            with st.spinner("Accessing Inquiry Portal & Bypassing Captcha..."):
                deep = deep_search_inquiry(res['Card Number'])
                if deep:
                    # تحديث البيانات
                    res['Name'] = deep['Name']
                    res['Est Name'] = deep['Est Name']
                    res['Company Code'] = deep['Company Code']
                    res['Job'] = deep['Designation'] # استبدال المسمى الوظيفي
                    st.session_state.single_res = res
                    st.rerun()
                else:
                    st.error("Deep search failed. Captcha might have changed.")

with t2:
    st.subheader("Excel Batch Mode")
    up = st.file_uploader("Upload XLSX", type=["xlsx"])
    if up:
        df_input = pd.read_excel(up)
        st.write(f"Total rows: {len(df_input)}")
        if st.button("Start Batch Process"):
            # (منطق الـ Batch المعتاد الخاص بك يوضع هنا مع استخدام الدوال الجديدة)
            pass
