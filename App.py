import streamlit as st 
import pandas as pd 
import time 
import re
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta 
from deep_translator import GoogleTranslator 

# --- إعداد الصفحة --- 
st.set_page_config(page_title="MOHRE Portal", layout="wide") 
st.title("HAMADA TRACING SITE TEST") 

# --- إدارة جلسة العمل ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'

# قائمة الجنسيات الكاملة كما طلبت
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
            else: st.error("Incorrect Password.")
    st.stop()

# --- وظائف التنسيق المتقدمة ---
def style_dataframe(df):
    """تلوين كامل الصف وحذف أعمدة الحالة من العرض النهائي"""
    if df.empty: return df
    
    def apply_row_style(row):
        # تلوين بناءً على الحالة المخفية
        color = '#d4edda' if row.get('_status_hidden') == 'Found' else '#f8d7da'
        return [f'background-color: {color}'] * len(row)

    # تحديد الأعمدة التي ستظهر للمستخدم فقط
    display_cols = [c for c in df.columns if c not in ['_status_hidden', 'Status']]
    return df.style.apply(apply_row_style, axis=1).subset(display_cols)

# --- محرك البحث ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    try:
        return uc.Chrome(options=options, headless=True)
    except Exception as e:
        st.error(f"Driver Init Error: {e}")
        return None

def extract_stage1(passport, nationality, dob_str):
    driver = get_driver()
    if not driver: return None
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
        dob_input.send_keys(dob_str)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)

        def get_v(lbl):
            try:
                xp = f"//*[contains(text(), '{lbl}')]/following::span[1] | //label[contains(text(), '{lbl}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xp).text.strip()
            except: return 'N/A'

        card_num = get_v("Card Number")
        if card_num == 'N/A' or not card_num: return None

        # ترجمة مسمى الوظيفة الأولي
        raw_job = get_v("Job Description")
        try:
            translated_job = GoogleTranslator(source='auto', target='en').translate(raw_job)
        except: translated_job = raw_job

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Name": "", "Est Name": "", "Company Code": "", # ستمتلئ في البحث العميق
            "Job Description": translated_job,
            "Card Number": card_num, "Card Issue": get_v("Card Issue"), 
            "Card Expiry": get_v("Card Expiry"), "Basic Salary": get_v("Basic Salary"),
            "Total Salary": get_v("Total Salary"), "_status_hidden": "Found"
        }
    except: return None
    finally: driver.quit()

def extract_stage2_deep(card_number):
    driver = get_driver()
    if not driver: return None
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        
        # اختيار الخدمة المطلوبة
        drop = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Please select the service')]")))
        drop.click()
        service = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information')]")))
        service.click()

        # إدخال رقم بطاقة العمل
        input_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter data here']")))
        input_field.send_keys(card_number)

        # منطق حل الكابتشا النصية
        time.sleep(2)
        captcha_code = None
        elements = driver.find_elements(By.XPATH, "//div | //span | //b | //strong")
        for el in elements:
            text = el.text.strip()
            if re.match(r'^\d{4}$', text):
                captcha_code = text
                break
        
        if captcha_code:
            driver.find_element(By.XPATH, "//input[contains(@placeholder, 'captcha')]").send_keys(captcha_code)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]").click()
            time.sleep(5)
            
            if "No Data Found" in driver.page_source: return None

            # استخراج البيانات واستبدال الوظيفة القديمة بالجديدة
            res = {}
            res['Name'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Name') and not(contains(text(), 'Est Name'))]/..").text.split(':')[-1].strip()
            res['Est Name'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Est Name')]/..").text.split(':')[-1].strip()
            res['Company Code'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Company Code')]/..").text.split(':')[-1].strip()
            res['Job Description'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Designation')]/..").text.split(':')[-1].strip()
            return res
        return None
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم الرسومية ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    col1, col2, col3 = st.columns(3)
    passport_input = col1.text_input("Passport Number", key="p_single")
    nationality_input = col2.selectbox("Nationality", countries_list, key="n_single")
    dob_input = col3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), max_value=datetime.now(), key="d_single")

    if st.button("Search Now", use_container_width=True):
        if passport_input and nationality_input != "Select Nationality" and dob_input:
            with st.spinner("Searching Stage 1..."):
                st.session_state.single_result = extract_stage1(passport_input, nationality_input, dob_input.strftime("%d/%m/%Y"))
                if not st.session_state.single_result:
                    st.error("No record found in MOHRE.")

    if st.session_state.single_result:
        # عرض البيانات الحالية
        df_single = pd.DataFrame([st.session_state.single_result])
        st.dataframe(style_dataframe(df_single), use_container_width=True)
        
        # زر البحث العميق للبحث الفردي
        if st.session_state.single_result.get('_status_hidden') == "Found":
            if st.button("🚀 Run Deep Search (Fetch Name & Company)", type="primary"):
                with st.spinner("Refining information from Inquiry Portal..."):
                    deep_data = extract_stage2_deep(st.session_state.single_result['Card Number'])
                    if deep_data:
                        st.session_state.single_result.update(deep_data)
                        st.success("Deep Search completed! Designation replaced Job Description.")
                        st.rerun()
                    else: st.error("Deep search failed. Captcha might have changed.")

with tab2:
    st.subheader("Batch File Processing")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        df_file = pd.read_excel(uploaded_file)
        st.write(f"Total Rows: {len(df_file)}")

        c_start, c_pause, c_reset = st.columns(3)
        if c_start.button("▶️ Start Processing"):
            st.session_state.run_state = 'running'
            st.session_state.batch_results = []
        if c_pause.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
        if c_reset.button("⏹️ Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.rerun()

        progress_bar = st.progress(0)
        table_placeholder = st.empty()

        # معالجة الملف
        for i, row in df_file.iterrows():
            if st.session_state.run_state != 'running': break
            if i < len(st.session_state.batch_results): continue

            # استخراج البيانات من الصف
            p_val = str(row.get('Passport Number', '')).strip()
            n_val = str(row.get('Nationality', 'Egypt')).strip()
            try: d_val = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except: d_val = str(row.get('Date of Birth', ''))

            # المرحلة الأولى
            res_stage1 = extract_stage1(p_val, n_val, d_val)
            if res_stage1:
                st.session_state.batch_results.append(res_stage1)
            else:
                st.session_state.batch_results.append({"Passport Number": p_val, "_status_hidden": "Failed"})
            
            progress_bar.progress((i + 1) / len(df_file))
            table_placeholder.dataframe(style_dataframe(pd.DataFrame(st.session_state.batch_results)), use_container_width=True)

        # خيار البحث العميق الجماعي
        if len(st.session_state.batch_results) == len(df_file) and len(df_file) > 0:
            st.success("Stage 1 Complete!")
            if st.button("🚀 Run Deep Search for All Records"):
                for idx, record in enumerate(st.session_state.batch_results):
                    if record.get('_status_hidden') == 'Found' and not record.get('Name'):
                        with st.spinner(f"Deep searching: {record['Card Number']}"):
                            deep_res = extract_stage2_deep(record['Card Number'])
                            if deep_res:
                                st.session_state.batch_results[idx].update(deep_res)
                                table_placeholder.dataframe(style_dataframe(pd.DataFrame(st.session_state.batch_results)), use_container_width=True)
                st.success("All records updated!")

            csv_data = pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Final CSV Report", csv_data, "MOHRE_Final_Report.csv")
