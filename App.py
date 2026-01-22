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
            else: st.error("Incorrect Password.")
    st.stop()

# --- وظائف التنسيق (تم إصلاح AttributeError هنا) ---
def style_dataframe(df):
    if df.empty: return df
    
    # تحديد الأعمدة التي ستظهر فقط وحذف Status و _status_hidden
    display_cols = [c for c in df.columns if c not in ['_status_hidden', 'Status']]
    
    def apply_row_style(row):
        # تلوين الصف بالكامل بناءً على القيمة المخفية
        color = '#d4edda' if row.get('_status_hidden') == 'Found' else '#f8d7da'
        return [f'background-color: {color}'] * len(row)

    # تطبيق التنسيق على الصفوف أولاً ثم تصفية الأعمدة للعرض
    return df.style.apply(apply_row_style, axis=1).set_properties(subset=display_cols).hide(axis='columns', subset=[c for c in df.columns if c not in display_cols])

# --- محرك البحث ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        return uc.Chrome(options=options, headless=True)
    except: return None

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

        card = get_v("Card Number")
        if card == 'N/A' or not card: return None

        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Name": "", "Est Name": "", "Company Code": "",
            "Job Description": GoogleTranslator(source='auto', target='en').translate(get_v("Job Description")),
            "Card Number": card, "Card Issue": get_v("Card Issue"), "Card Expiry": get_v("Card Expiry"),
            "Basic Salary": get_v("Basic Salary"), "Total Salary": get_v("Total Salary"),
            "_status_hidden": "Found"
        }
    except: return None
    finally: driver.quit()

def extract_stage2_deep(card_number):
    driver = get_driver()
    if not driver: return None
    wait = WebDriverWait(driver, 20)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        drop = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Please select the service')]")))
        drop.click()
        opt = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information')]")))
        opt.click()

        inp = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter data here']")))
        inp.send_keys(card_number)

        time.sleep(2)
        captcha = None
        for el in driver.find_elements(By.XPATH, "//div | //span | //b"):
            if re.match(r'^\d{4}$', el.text.strip()):
                captcha = el.text.strip()
                break
        
        if captcha:
            driver.find_element(By.XPATH, "//input[contains(@placeholder, 'captcha')]").send_keys(captcha)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]").click()
            time.sleep(5)
            
            res = {}
            res['Name'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Name') and not(contains(text(), 'Est Name'))]/..").text.split(':')[-1].strip()
            res['Est Name'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Est Name')]/..").text.split(':')[-1].strip()
            res['Company Code'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Company Code')]/..").text.split(':')[-1].strip()
            # إبدال الوظيفة القديمة بالجديدة مباشرة
            res['Job Description'] = driver.find_element(By.XPATH, "//*[contains(text(), 'Designation')]/..").text.split(':')[-1].strip()
            return res
        return None
    except: return None
    finally: driver.quit()

# --- الواجهة ---
t1, t2 = st.tabs(["Single Search", "Upload Excel File"])

with t1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="p_s")
    n_in = c2.selectbox("Nationality", countries_list, key="n_s")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="d_s")

    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Processing Stage 1..."):
                st.session_state.single_result = extract_stage1(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if not st.session_state.single_result: st.error("No record found.")

    if st.session_state.single_result:
        df_single = pd.DataFrame([st.session_state.single_result])
        st.dataframe(style_dataframe(df_single), use_container_width=True)
        
        if st.button("🚀 Run Deep Search (Individual)"):
            with st.spinner("Fetching Name & Company..."):
                deep = extract_stage2_deep(st.session_state.single_result['Card Number'])
                if deep:
                    st.session_state.single_result.update(deep)
                    st.success("Deep Search completed & Job Description replaced!")
                    st.rerun()
                else: st.error("Deep search failed.")

with t2:
    st.subheader("Batch File Processing")
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        df_f = pd.read_excel(up)
        if st.button("▶️ Start Batch"):
            st.session_state.batch_results = []
            st.session_state.run_state = 'running'
            
            pb = st.progress(0)
            table_hold = st.empty()

            for i, row in df_f.iterrows():
                p_v = str(row.get('Passport Number', '')).strip()
                n_v = str(row.get('Nationality', 'Egypt')).strip()
                try: d_v = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: d_v = ""

                res1 = extract_stage1(p_v, n_v, d_v)
                if res1: st.session_state.batch_results.append(res1)
                else: st.session_state.batch_results.append({"Passport Number": p_v, "_status_hidden": "Failed"})
                
                pb.progress((i+1)/len(df_f))
                table_hold.dataframe(style_dataframe(pd.DataFrame(st.session_state.batch_results)), use_container_width=True)

        if st.session_state.batch_results:
            if st.button("🚀 Run Deep Search for All Found"):
                for idx, r in enumerate(st.session_state.batch_results):
                    if r.get('_status_hidden') == 'Found' and not r.get('Name'):
                        deep = extract_stage2_deep(r['Card Number'])
                        if deep: st.session_state.batch_results[idx].update(deep)
                st.rerun()
            
            st.download_button("Download Full CSV", pd.DataFrame(st.session_state.batch_results).to_csv(index=False), "Full_MOHRE_Report.csv")
