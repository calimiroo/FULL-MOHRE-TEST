import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- 1. إعدادات الصفحة وحالة الجلسة ---
st.set_page_config(page_title="MOHRE Portal Pro", layout="wide")
st.title("MOHRE DATA TRACING SYSTEM (Full Fixed Version)")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'single_res' not in st.session_state: st.session_state['single_res'] = None
if 'batch_results' not in st.session_state: st.session_state['batch_results'] = []
if 'run_state' not in st.session_state: st.session_state['run_state'] = 'stopped'
if 'start_time_ref' not in st.session_state: st.session_state['start_time_ref'] = None
if 'deep_run_state' not in st.session_state: st.session_state['deep_run_state'] = 'stopped'

countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- 2. نظام الدخول ---
if not st.session_state['authenticated']:
    with st.form("login"):
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == "Bilkish": st.session_state['authenticated'] = True; st.rerun()
            else: st.error("Wrong Password")
    st.stop()

# --- 3. الدوال الأساسية ---
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def format_time(seconds): return str(timedelta(seconds=int(seconds)))

def translate_ar_en(text):
    try:
        if text and text != 'Not Found': return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except: return text

# --- البحث الأول ---
def extract_contract(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        try:
            sb = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
            sb.send_keys(nationality)
            time.sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
            if items: items[0].click()
        except: pass
        dob_in = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_in)
        dob_in.clear(); dob_in.send_keys(dob_str)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_in)
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(7)
        def gv(lbl):
            try: return driver.find_element(By.XPATH, f"//span[contains(text(), '{lbl}')]/following::span[1] | //label[contains(text(), '{lbl}')]/following-sibling::div").text.strip()
            except: return 'Not Found'
        c_num = gv("Card Number")
        if c_num == 'Not Found': return None
        return {
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_ar_en(gv("Job Description")), "Card Number": c_num,
            "Card Issue": gv("Card Issue"), "Card Expiry": gv("Card Expiry"),
            "Basic Salary": gv("Basic Salary"), "Total Salary": gv("Total Salary"), "Status": "Found"
        }
    except: return None
    finally: driver.quit()

# --- البحث العميق ---
def deep_search(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        # مسار Work Permit
        btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton"))); btn.click(); time.sleep(1)
        for li in driver.find_elements(By.CSS_SELECTOR, "#dropdownList li"):
            if 'Work Permit' in li.text: li.click(); break
        time.sleep(2)
        for li in driver.find_elements(By.CSS_SELECTOR, "#dropdownList li"):
            if 'Electronic Work Permit Information' in li.text or 'EWPI' in li.get_attribute('value'): li.click(); break
        time.sleep(1)
        # إدخال البطاقة
        for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='text']"):
            ph = (inp.get_attribute('placeholder') or '').lower()
            if 'captcha' not in ph and 'التحقق' not in ph:
                inp.clear(); inp.send_keys(card_number); break
        # الكابتشا
        js_cap = r"try{const code=[...document.querySelectorAll('div,span,b,strong')].map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));const inp=[...document.querySelectorAll('input')].find(i=>i.placeholder.includes('التحقق')||i.placeholder.toLowerCase().includes('captcha'));if(code&&inp){inp.value=code;inp.dispatchEvent(new Event('input',{bubbles:true}));}}catch(e){}"
        driver.execute_script(js_cap); time.sleep(1)
        try: driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except: driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'بحث')]").click()
        time.sleep(5)
        def fv(l):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{l}')]/following::span[1]").text.strip()
            except: return 'Not Found'
        return {'Name': fv('Name'), 'Est Name': fv('Est Name') if fv('Est Name') != 'Not Found' else fv('Establishment Name'), 'Company Code': fv('Company Code'), 'Designation': fv('Designation')}
    except: return None
    finally: driver.quit()

# --- 4. واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

# --- واجهة الفردي ---
with tab1:
    st.subheader("Individual Trace")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="p_1")
    n_in = c2.selectbox("Nationality", countries_list, key="n_1")
    d_in = c3.date_input("DOB", value=None, min_value=datetime(1950,1,1), key="d_1")
    if st.button("Search Contract"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Finding Contract..."):
                st.session_state.single_res = extract_contract(p_in, n_in, d_in.strftime("%d/%m/%Y"))
    
    if st.session_state.single_res:
        sr = st.session_state.single_res
        st.table(pd.DataFrame([sr]))
        if st.button(f"Deep Search for Card: {sr['Card Number']}"):
            with st.spinner("Accessing Inquiry Portal..."):
                dr = deep_search(sr['Card Number'])
                if dr:
                    sr.update({'Name': dr['Name'], 'Est Name': dr['Est Name'], 'Company Code': dr['Company Code'], 'Job Description': dr['Designation']})
                    st.session_state.single_res = sr; st.rerun()
                else: st.error("Deep search failed.")

# --- واجهة المجمع ---
with tab2:
    st.subheader("Batch Control")
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        df_up = pd.read_excel(up)
        st.write(f"Records: {len(df_up)}")
        b1, b2, b3 = st.columns(3)
        if b1.button("▶️ Start"): st.session_state.run_state = 'running'
        if b2.button("⏸️ Pause"): st.session_state.run_state = 'paused'
        if b3.button("⏹️ Reset"): st.session_state.run_state = 'stopped'; st.session_state.batch_results = []; st.session_state.start_time_ref = None; st.rerun()

        prg = st.progress(0); st_txt = st.empty(); st_stats = st.empty(); st_table = st.empty()
        
        if st.session_state.run_state == 'running':
            if not st.session_state.start_time_ref: st.session_state.start_time_ref = time.time()
            for i, row in df_up.iterrows():
                if i < len(st.session_state.batch_results): continue
                while st.session_state.run_state == 'paused': time.sleep(1)
                if st.session_state.run_state == 'stopped': break
                
                p = str(row.get('Passport Number','')).strip()
                n = str(row.get('Nationality','')).strip()
                try: d = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: d = str(row.get('Date of Birth',''))
                
                st_txt.info(f"Processing {i+1}/{len(df_up)}: {p}")
                res = extract_contract(p, n, d)
                if not res: res = {"Passport Number": p, "Nationality": n, "Date of Birth": d, "Status": "Not Found"}
                st.session_state.batch_results.append(res)
                
                # تحديث العرض
                prg.progress((i+1)/len(df_up))
                elapsed = time.time() - st.session_state.start_time_ref
                st_stats.markdown(f"⏱️ Time: `{format_time(elapsed)}` | ✅ Done: {i+1}")
                st_table.dataframe(pd.DataFrame(st.session_state.batch_results), use_container_width=True)
            
            if len(st.session_state.batch_results) == len(df_up):
                st.success("Batch Phase 1 Done!")
                final_df = pd.DataFrame(st.session_state.batch_results)
                st.download_button("Download Phase 1 CSV", final_df.to_csv(index=False).encode('utf-8'), "phase1.csv")
                
                if st.button("🚀 Run Deep Search for Found Records"):
                    st.session_state.deep_run_state = 'running'
                    
        if st.session_state.deep_run_state == 'running':
            # منطق البحث العميق للمجمع
            for idx, item in enumerate(st.session_state.batch_results):
                if item.get('Status') == 'Found' and 'Name' not in item:
                    st_txt.warning(f"Deep searching card: {item['Card Number']}")
                    dr = deep_search(item['Card Number'])
                    if dr:
                        item.update({'Name': dr['Name'], 'Est Name': dr['Est Name'], 'Company Code': dr['Company Code'], 'Job Description': dr['Designation']})
                    st.session_state.batch_results[idx] = item
                    st_table.dataframe(pd.DataFrame(st.session_state.batch_results), use_container_width=True)
            st.success("Deep Search Completed!")
            st.session_state.deep_run_state = 'stopped'
