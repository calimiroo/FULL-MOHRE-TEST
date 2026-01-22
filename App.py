import streamlit as st 
import pandas as pd 
import time 
import re
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta 
from deep_translator import GoogleTranslator 

# --- إعداد الصفحة --- 
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
if 'deep_progress' not in st.session_state:
    st.session_state['deep_progress'] = 0

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

# --- دالات المساعدة ---
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
    # إعدادات إضافية من الكود الثاني لضمان الاستقرار
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return uc.Chrome(options=options)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- البحث في الموقع الأول ---
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
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(8)

        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except: return 'Not Found'

        card_num = get_value("Card Number")
        if card_num == 'Not Found': return None

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num, "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"), "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"), "Status": "Found"
        }
    except: return None
    finally:
        try: driver.quit()
        except: pass

# --- البحث العميق (تطبيق الكود الثاني الناجح) ---
def deep_extract_by_card(card_number):
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        
        # 1. Force English (Logic from script 2)
        try:
            lang_btn = wait.until(EC.presence_of_element_located((By.ID, "btnlanguage")))
            if "English" in lang_btn.text:
                driver.execute_script("arguments[0].click();", lang_btn)
                wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Please select the service"))
        except: pass

        # 2. Dropdown Selection
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Please select the service')]")))
        dropdown.click()
        time.sleep(1.5)
        service_opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information')]")))
        service_opt.click()

        # 3. Enter Card Number
        input_box = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter data here']")))
        input_box.clear()
        input_box.send_keys(card_number)

        # 4. Solve Captcha (Logic from script 2)
        captcha_code = None
        elements = driver.find_elements(By.XPATH, "//div | //span | //b | //strong | //p")
        for el in elements:
            txt = el.text.strip()
            if re.match(r'^\d{4}$', txt):
                captcha_code = txt
                break
        
        if captcha_code:
            captcha_field = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'captcha')]")
            captcha_field.clear()
            captcha_field.send_keys(captcha_code)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]").click()
            time.sleep(5)
            
            if "No Data Found" in driver.page_source:
                return None
            
            # 5. Extraction using script 2 XPaths
            comp_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Est Name')]/..").text.replace("Est Name", "").replace(":", "").strip()
            cust_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Name') and not(contains(text(), 'Est Name'))]/..").text.replace("Name", "").replace(":", "").strip()
            designation = driver.find_element(By.XPATH, "//*[contains(text(), 'Designation')]/..").text.replace("Designation", "").replace(":", "").strip()
            
            # محاولة جلب كود الشركة إذا وجد
            try:
                comp_code = driver.find_element(By.XPATH, "//*[contains(text(), 'Company Code')]/..").text.replace("Company Code", "").replace(":", "").strip()
            except: comp_code = "N/A"

            return {
                'Name': cust_name,
                'Est Name': comp_name,
                'Company Code': comp_code,
                'Designation': designation
            }
        return None
    except: return None
    finally:
        try: driver.quit()
        except: pass

# --- واجهة المستخدم (تطابق الكود الأول تماماً) ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"]) 

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res: st.table(pd.DataFrame([res]))
                else: st.error("No data found.")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"]) 
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df, height=150)

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None: st.session_state.start_time_ref = time.time()
        if col_ctrl2.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.session_state.start_time_ref = None
            st.session_state.deep_run_state = 'stopped'
            st.session_state.deep_progress = 0
            st.rerun()

        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_area = st.empty()
        live_table_area = st.empty()
        deep_status_area = st.empty()
        deep_progress_bar = st.empty()

        actual_success = 0

        # حلقة المعالجة الأساسية
        for i, row in df.iterrows():
            while st.session_state.run_state == 'paused':
                status_text.warning("Paused... click Resume to continue.")
                time.sleep(1)
            if st.session_state.run_state == 'stopped': break

            if i < len(st.session_state.batch_results):
                if st.session_state.batch_results[i].get("Status") == "Found": actual_success += 1
                current_df = pd.DataFrame(st.session_state.batch_results)
                live_table_area.dataframe(current_df.style.map(color_status, subset=['Status']), use_container_width=True)
                progress_bar.progress((i + 1) / len(df))
                continue

            p_num = str(row.get('Passport Number', '')).strip()
            nat = str(row.get('Nationality', 'Egypt')).strip()
            try: dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except: dob = str(row.get('Date of Birth', ''))

            status_text.info(f"Processing Stage 1: {i+1}/{len(df)}")
            res = extract_data(p_num, nat, dob)
            
            if res:
                actual_success += 1
                st.session_state.batch_results.append(res)
            else:
                st.session_state.batch_results.append({
                    "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                    "Job Description": "N/A", "Card Number": "N/A", "Status": "Not Found"
                })

            elapsed = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ **Success:** {actual_success} | ⏱️ **Time:** `{format_time(elapsed)}`")
            live_table_area.dataframe(pd.DataFrame(st.session_state.batch_results).style.map(color_status, subset=['Status']), use_container_width=True)

        # عند اكتمال المرحلة الأولى
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success("Stage 1 Completed!")
            
            if st.button("🚀 Deep Search (Apply logic from script 2)"):
                st.session_state.deep_run_state = 'running'

            if st.session_state.deep_run_state == 'running':
                to_deep = [idx for idx, r in enumerate(st.session_state.batch_results) if r.get('Status') == 'Found']
                deep_total = len(to_deep)
                
                if deep_total > 0:
                    deep_idx = 0
                    deep_prog = st.progress(0)
                    for idx in to_deep:
                        rec = st.session_state.batch_results[idx]
                        card = rec.get('Card Number')
                        deep_status_area.info(f"Deep Searching {deep_idx+1}/{deep_total}: {card}")
                        
                        deep_res = deep_extract_by_card(card)
                        if deep_res:
                            # تحديث البيانات بناءً على طلبك
                            st.session_state.batch_results[idx]['Job Description'] = deep_res['Designation']
                            st.session_state.batch_results[idx]['Name'] = deep_res['Name']
                            st.session_state.batch_results[idx]['Est Name'] = deep_res['Est Name']
                            st.session_state.batch_results[idx]['Company Code'] = deep_res['Company Code']
                        
                        deep_idx += 1
                        deep_prog.progress(deep_idx / deep_total)
                        live_table_area.dataframe(pd.DataFrame(st.session_state.batch_results).style.map(color_status, subset=['Status']), use_container_width=True)
                    
                    st.success("Deep Search Completed Successfully!")
                    st.download_button("📥 Download Final Report (CSV)", pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8'), "final_report.csv")
                    st.session_state.deep_run_state = 'stopped'
