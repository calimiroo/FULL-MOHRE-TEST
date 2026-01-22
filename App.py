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

# قائمة الجنسيات المختصرة (للتجربة)
countries_list = ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Jordan", "Syria", "Lebanon", "United Arab Emirates", "Sudan", "Morocco"] 

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
    """نسخة محسنة لتجنب InvalidArgumentException"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # ملاحظة: لا تضف أي experimental_options هنا مع UC
    try:
        driver = uc.Chrome(options=options, headless=True)
        return driver
    except Exception as e:
        st.error(f"Driver Error: {e}")
        return None

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- البحث في الموقع الأول (Stage 1) ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    if not driver: return None
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
            "Name": "", "Est Name": "", "Company Code": "", # خانات فارغة للمرحلة الثانية
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num, "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"), "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"), "Status": "Found"
        }
    except: return None
    finally:
        if driver: driver.quit()

# --- البحث العميق (Stage 2) ---
def deep_extract_by_card(card_number):
    driver = get_driver()
    if not driver: return None
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        try:
            lang_btn = wait.until(EC.presence_of_element_located((By.ID, "btnlanguage")))
            if "English" in lang_btn.text:
                driver.execute_script("arguments[0].click();", lang_btn)
                time.sleep(2)
        except: pass

        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Please select the service')]")))
        dropdown.click()
        time.sleep(1)
        service_opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information')]")))
        service_opt.click()

        input_box = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter data here']")))
        input_box.clear()
        input_box.send_keys(card_number)

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
            
            if "No Data Found" in driver.page_source: return None

            comp_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Est Name')]/..").text.replace("Est Name", "").replace(":", "").strip()
            cust_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Name') and not(contains(text(), 'Est Name'))]/..").text.replace("Name", "").replace(":", "").strip()
            designation = driver.find_element(By.XPATH, "//*[contains(text(), 'Designation')]/..").text.replace("Designation", "").replace(":", "").strip()
            try:
                comp_code = driver.find_element(By.XPATH, "//*[contains(text(), 'Company Code')]/..").text.replace("Company Code", "").replace(":", "").strip()
            except: comp_code = "N/A"

            return {'Name': cust_name, 'Est Name': comp_name, 'Company Code': comp_code, 'Designation': designation}
        return None
    except: return None
    finally:
        if driver: driver.quit()

# --- الواجهة الرسومية ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"]) 

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    if st.button("Search Now", use_container_width=True):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching Stage 1..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                st.session_state.single_result = res
                if not res: st.error("No data found.")

    if st.session_state.single_result:
        # عرض الجدول
        df_display = pd.DataFrame([st.session_state.single_result])
        st.dataframe(df_display.style.map(color_status, subset=['Status']), use_container_width=True)
        
        # زر البحث العميق للبحث الفردي
        if st.session_state.single_result.get('Status') == "Found":
            if st.button("🚀 Run Deep Search", type="primary"):
                with st.spinner("Fetching Name & Company Details..."):
                    d_res = deep_extract_by_card(st.session_state.single_result['Card Number'])
                    if d_res:
                        st.session_state.single_result.update(d_res)
                        st.session_state.single_result['Job Description'] = d_res['Designation']
                        st.success("Deep details updated!")
                        st.rerun()
                    else: st.error("Deep search failed.")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"]) 
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records: {len(df)}")

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None: st.session_state.start_time_ref = time.time()
        if col_ctrl2.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.rerun()

        progress_bar = st.progress(0)
        live_table_area = st.empty()

        # المرحلة الأولى (Batch)
        for i, row in df.iterrows():
            if st.session_state.run_state != 'running': break
            if i < len(st.session_state.batch_results): continue

            p_num = str(row.get('Passport Number', '')).strip()
            nat = str(row.get('Nationality', 'Egypt')).strip()
            try: dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except: dob = ""

            res = extract_data(p_num, nat, dob)
            if res: st.session_state.batch_results.append(res)
            else: st.session_state.batch_results.append({"Passport Number": p_num, "Status": "Not Found"})
            
            progress_bar.progress((i + 1) / len(df))
            live_table_area.dataframe(pd.DataFrame(st.session_state.batch_results).style.map(color_status, subset=['Status']), use_container_width=True)

        # زر البحث العميق للملف الكامل
        if len(st.session_state.batch_results) == len(df) and len(df) > 0:
            st.success("Stage 1 Finished!")
            if st.button("🚀 Run Deep Search for All Records"):
                st.session_state.deep_run_state = 'running'

            if st.session_state.deep_run_state == 'running':
                to_deep = [idx for idx, r in enumerate(st.session_state.batch_results) if r.get('Status') == 'Found' and not r.get('Name')]
                for idx in to_deep:
                    card = st.session_state.batch_results[idx].get('Card Number')
                    with st.spinner(f"Deep Search for Card: {card}"):
                        d_res = deep_extract_by_card(card)
                        if d_res:
                            st.session_state.batch_results[idx].update(d_res)
                            st.session_state.batch_results[idx]['Job Description'] = d_res['Designation']
                            # تحديث الجدول Live فوراً
                            live_table_area.dataframe(pd.DataFrame(st.session_state.batch_results).style.map(color_status, subset=['Status']), use_container_width=True)
                
                st.success("Deep Search Completed!")
                st.download_button("📥 Download Final Report", pd.DataFrame(st.session_state.batch_results).to_csv(index=False).encode('utf-8'), "final_report.csv")
