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
st.set_page_config(page_title="MOHRE Portal - Advanced", layout="wide") 
st.title("HAMADA TRACING SITE - PRO VERSION") 

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

# قائمة الجنسيات (مختصرة للعرض، يفضل وضع القائمة الكاملة هنا)
countries_list = ["Select Nationality", "Egypt", "India", "Pakistan", "Bangladesh", "Philippines"] 

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

# --- دالات مساعدة ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless') # غيرها لـ False لو عايز تشوف المتصفح شغال
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # إخفاء هوية الأتمتة
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return uc.Chrome(options=options)

def force_english(driver):
    try:
        wait = WebDriverWait(driver, 7)
        lang_btn = wait.until(EC.presence_of_element_located((By.ID, "btnlanguage")))
        if "English" in lang_btn.text:
            driver.execute_script("arguments[0].click();", lang_btn)
            time.sleep(2)
    except:
        pass

# --- وظيفة البحث الأول (الموقع الأول) ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 10)
        
        wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber"))).send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        
        search_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")))
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()

        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob_str)
        driver.find_element(By.ID, "btnSubmit").click()
        
        time.sleep(5)
        
        def get_val(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return 'Not Found'

        card_num = get_val("Card Number")
        if card_num == 'Not Found': return None

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": get_val("Job Description"), "Card Number": card_num,
            "Card Issue": get_val("Card Issue"), "Card Expiry": get_val("Card Expiry"),
            "Basic Salary": get_val("Basic Salary"), "Total Salary": get_val("Total Salary"),
            "Status": "Found"
        }
    except: return None
    finally: driver.quit()

# --- وظيفة البحث العميق (الموقع الثاني - المنطق الجديد) ---
def deep_extract_by_card(card_number):
    driver = get_driver()
    wait = WebDriverWait(driver, 15)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        force_english(driver)

        # 1. اختيار الخدمة
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Please select the service')]")))
        dropdown.click()
        time.sleep(1)
        service_opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information')]")))
        service_opt.click()

        # 2. إدخال الرقم
        input_box = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter data here']")))
        input_box.send_keys(card_number)

        # 3. حل الكابتشا (منطق الكود الثاني)
        captcha_code = None
        elements = driver.find_elements(By.XPATH, "//div | //span | //b | //strong | //p")
        for el in elements:
            txt = el.text.strip()
            if re.match(r'^\d{4}$', txt):
                captcha_code = txt
                break
        
        if captcha_code:
            captcha_field = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'captcha')]")
            captcha_field.send_keys(captcha_code)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]").click()
            time.sleep(5)

            # 4. استخراج البيانات النهائية
            if "No Data Found" in driver.page_source:
                return None
            
            comp_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Est Name')]/..").text.replace("Est Name", "").replace(":", "").strip()
            cust_name = driver.find_element(By.XPATH, "//*[contains(text(), 'Name') and not(contains(text(), 'Est Name'))]/..").text.replace("Name", "").replace(":", "").strip()
            designation = driver.find_element(By.XPATH, "//*[contains(text(), 'Designation')]/..").text.replace("Designation", "").replace(":", "").strip()
            comp_code = driver.find_element(By.XPATH, "//*[contains(text(), 'Company Code')]/..").text.replace("Company Code", "").replace(":", "").strip()

            return {
                'Name': cust_name,
                'Est Name': comp_name,
                'Company Code': comp_code,
                'Designation': designation
            }
    except: return None
    finally: driver.quit()

# --- واجهة المستخدم (Tabs) ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    # ... (نفس كود البحث الفردي القديم)

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"]) 
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records: {len(df)}")

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume Stage 1"):
            st.session_state.run_state = 'running'
            if not st.session_state.start_time_ref: st.session_state.start_time_ref = time.time()
        if col_ctrl2.button("⏸️ Pause"):
            st.session_state.run_state = 'paused'
        if col_ctrl3.button("⏹️ Stop & Reset"):
            st.session_state.run_state = 'stopped'
            st.session_state.batch_results = []
            st.rerun()

        # عرض النتائج
        progress_bar = st.progress(0)
        live_table_area = st.empty()

        # المرحلة الأولى: استخراج أرقام البطاقات
        if st.session_state.run_state == 'running':
            for i, row in df.iterrows():
                if i < len(st.session_state.batch_results): continue
                if st.session_state.run_state != 'running': break

                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')

                res = extract_data(p_num, nat, dob)
                if not res:
                    res = {"Passport Number": p_num, "Nationality": nat, "Status": "Not Found"}
                
                st.session_state.batch_results.append(res)
                progress_bar.progress((i + 1) / len(df))
                live_table_area.dataframe(pd.DataFrame(st.session_state.batch_results))

        # المرحلة الثانية: Deep Search
        if len(st.session_state.batch_results) == len(df):
            st.success("Stage 1 Completed!")
            if st.button("🚀 Start Deep Search (Stage 2)"):
                st.session_state.deep_run_state = 'running'

            if st.session_state.deep_run_state == 'running':
                deep_progress = st.progress(0)
                found_records = [r for r in st.session_state.batch_results if r.get('Status') == 'Found']
                
                for idx, rec in enumerate(st.session_state.batch_results):
                    if rec.get('Status') == 'Found' and 'Name' not in rec:
                        card = rec.get('Card Number')
                        st.info(f"Deep Searching Card: {card}")
                        deep_res = deep_extract_by_card(card)
                        
                        if deep_res:
                            # تحديث البيانات ودمجها
                            st.session_state.batch_results[idx].update(deep_res)
                            # استبدال Job Description بالـ Designation المترجم/المستخرج
                            st.session_state.batch_results[idx]['Job Description'] = deep_res['Designation']
                        
                        deep_progress.progress((idx + 1) / len(st.session_state.batch_results))
                        live_table_area.dataframe(pd.DataFrame(st.session_state.batch_results))

                st.success("Deep Search Finished!")
                final_df = pd.DataFrame(st.session_state.batch_results)
                st.download_button("📥 Download Final Report", final_df.to_csv(index=False), "MOHRE_Final_Report.csv")
