import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import os

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal - Advanced Tracing", layout="wide")

# تخصيص CSS لتطابق الصورة
st.markdown("""
    <style>
    .stButton > button {
        border-radius: 5px;
        border: 1px solid #ccc;
        background-color: white;
        color: black;
    }
    .stProgress > div > div > div > div {
        background-color: #0072CE;
    }
    .success-msg {
        padding: 10px;
        background-color: #D4EDDA;
        color: #155724;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-msg {
        padding: 10px;
        background-color: #E7F3FF;
        color: #004085;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("HAMADA TRACING SITE - ADVANCED VERSION")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
if 'deep_search_results' not in st.session_state:
    st.session_state['deep_search_results'] = []
if 'start_time_ref' not in st.session_state:
    st.session_state['start_time_ref'] = None
if 'deep_run_state' not in st.session_state:
    st.session_state['deep_run_state'] = 'stopped'
if 'single_res' not in st.session_state:
    st.session_state['single_res'] = None

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

# --- دالة تحويل الوقت ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

# --- وظائف الاستخراج والترجمة ---
def translate_to_english(text):
    try:
        if text and text != 'Not Found' and text != 'N/A':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    if val == 'Found':
        color = '#90EE90'
    elif val == 'Not Found':
        color = '#FFCCCB'
    else:
        color = 'transparent'
    return f'background-color: {color}'

def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 15)
        
        passport_input = wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber")))
        passport_input.send_keys(passport)
        
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")))
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items:
            items[0].click()
        
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
            except:
                return 'Not Found'

        card_num = get_value("Card Number")
        if card_num == 'Not Found':
            return None
            
        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num,
            "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"),
            "Status": "Found",
            "Name": "N/A",
            "Est Name": "N/A",
            "Company Code": "N/A"
        }
    except Exception as e:
        return None
    finally:
        driver.quit()

def deep_search_extract(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 20)
        
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        dropdown_btn.click()
        
        option = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@role='option' and @value='EWPI']")))
        option.click()
        
        wait.until(EC.presence_of_element_located((By.ID, "txtWorkPermitNo")))
        driver.find_element(By.ID, "txtWorkPermitNo").send_keys(card_number)
        
        try:
            captcha_elements = driver.find_elements(By.CSS_SELECTOR, "div,span,b,strong")
            captcha_code = ""
            for el in captcha_elements:
                txt = el.text.strip()
                if len(txt) == 4 and txt.isdigit():
                    captcha_code = txt
                    break
            
            if captcha_code:
                captcha_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='التحقق'], input[placeholder*='captcha'], input[placeholder*='Captcha']")
                captcha_input.send_keys(captcha_code)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", captcha_input)
        except:
            pass
            
        driver.find_element(By.ID, "btnSearch").click()
        time.sleep(5)
        
        res = {
            "Card Number": card_number,
            "Name": "N/A",
            "Est Name": "N/A",
            "Company Code": "N/A",
            "Designation": "N/A"
        }
        
        labels_map = {
            "Name": ["Name", "Worker Name"],
            "Est Name": ["Establishment Name", "Company Name"],
            "Company Code": ["Establishment Number", "Company Code"],
            "Designation": ["Designation", "Profession"]
        }
        
        for key, labels in labels_map.items():
            for label in labels:
                try:
                    xpath = f"//*[contains(text(), '{label}')]/following::span[1]"
                    val = driver.find_element(By.XPATH, xpath).text.strip()
                    if val:
                        res[key] = val
                        break
                except:
                    continue
        
        return res
    except Exception as e:
        return None
    finally:
        driver.quit()

# --- واجهة المستخدم ---
tab1, tab2 = st.tabs(["Single Search", "Batch & Deep Search"])

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
                if res:
                    st.session_state['single_res'] = res
                else:
                    st.error("No data found.")
                    st.session_state['single_res'] = None

    if st.session_state['single_res']:
        st.table(pd.DataFrame([st.session_state['single_res']]))
        
        if st.button("🔍 Deep Search (Single)"):
            card_no = st.session_state['single_res'].get("Card Number")
            with st.spinner(f"Deep Searching Card: {card_no}..."):
                deep_res = deep_search_extract(card_no)
                if deep_res:
                    st.session_state['single_res'].update({
                        "Name": deep_res.get("Name"),
                        "Est Name": deep_res.get("Est Name"),
                        "Company Code": deep_res.get("Company Code"),
                        "Job Description": deep_res.get("Designation") if deep_res.get("Designation") != "N/A" else st.session_state['single_res']["Job Description"]
                    })
                    st.success("Deep Search Completed!")
                    st.rerun()
                else:
                    st.error("Deep Search failed to retrieve data.")

with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df, height=150)
        
        # أزرار التحكم كما في الصورة
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 1])
        with col_ctrl1:
            if st.button("▶️ Start / Resume"):
                st.session_state.run_state = 'running'
                if st.session_state.start_time_ref is None:
                    st.session_state.start_time_ref = time.time()
        with col_ctrl2:
            if st.button("⏸️ Pause"):
                st.session_state.run_state = 'paused'
        with col_ctrl3:
            if st.button("⏹️ Stop & Reset"):
                st.session_state.run_state = 'stopped'
                st.session_state.batch_results = []
                st.session_state.deep_search_results = []
                st.session_state.start_time_ref = None
                st.rerun()

        if st.session_state.run_state in ['running', 'paused']:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            live_table_area = st.empty()
            
            actual_success = 0
            for i, row in df.iterrows():
                while st.session_state.run_state == 'paused':
                    status_text.warning("Paused... click Resume to continue.")
                    time.sleep(1)
                if st.session_state.run_state == 'stopped':
                    break
                
                if i < len(st.session_state.batch_results):
                    if st.session_state.batch_results[i].get("Status") == "Found":
                        actual_success += 1
                    continue
                
                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                try:
                    dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except:
                    dob = str(row.get('Date of Birth', ''))
                
                status_text.info(f"Processing {i+1}/{len(df)}: {p_num}")
                res = extract_data(p_num, nat, dob)
                
                if res:
                    actual_success += 1
                    st.session_state.batch_results.append(res)
                else:
                    st.session_state.batch_results.append({
                        "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                        "Job Description": "N/A", "Card Number": "N/A", "Card Issue": "N/A",
                        "Card Expiry": "N/A", "Basic Salary": "N/A", "Total Salary": "N/A",
                        "Status": "Not Found", "Name": "N/A", "Est Name": "N/A", "Company Code": "N/A"
                    })
                
                elapsed_seconds = time.time() - st.session_state.start_time_ref
                time_str = format_time(elapsed_seconds)
                progress_bar.progress((i + 1) / len(df))
                stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** {time_str}")
                
                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                live_table_area.dataframe(styled_df, use_container_width=True)

            if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
                st.success(f"Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
                st.session_state.run_state = 'completed'

        # --- Deep Search Section (تطابق الصورة) ---
        if len(st.session_state.batch_results) > 0:
            st.divider()
            st.subheader("Deep Search (MOHRE Inquiry)")
            
            found_cards = [r for r in st.session_state.batch_results if r.get("Status") == "Found" and r.get("Card Number") != "N/A"]
            
            if not found_cards:
                st.info("No valid Card Numbers found to perform Deep Search.")
            else:
                if st.button("🔍 Deep Search"):
                    st.session_state.deep_run_state = 'running'
                
                if st.session_state.deep_run_state in ['running', 'completed']:
                    deep_progress = st.progress(0)
                    deep_status_container = st.empty()
                    deep_table_area = st.empty()
                    
                    if st.session_state.deep_run_state == 'running':
                        for idx, item in enumerate(found_cards):
                            card_no = item.get("Card Number")
                            
                            if any(d.get("Card Number") == card_no and d.get("Name") != "N/A" for d in st.session_state.deep_search_results):
                                continue
                                
                            deep_status_container.markdown(f'<div class="info-msg">Deep Searching Card: {card_no} ({idx+1}/{len(found_cards)})</div>', unsafe_allow_html=True)
                            deep_res = deep_search_extract(card_no)
                            
                            if deep_res:
                                # تحديث أو إضافة النتيجة
                                existing = next((d for d in st.session_state.deep_search_results if d["Card Number"] == card_no), None)
                                if existing:
                                    existing.update(deep_res)
                                else:
                                    st.session_state.deep_search_results.append(deep_res)
                                
                                # تحديث الجدول الرئيسي
                                for main_item in st.session_state.batch_results:
                                    if main_item.get("Card Number") == card_no:
                                        main_item["Name"] = deep_res.get("Name")
                                        main_item["Est Name"] = deep_res.get("Est Name")
                                        main_item["Company Code"] = deep_res.get("Company Code")
                                        if deep_res.get("Designation") != "N/A":
                                            main_item["Job Description"] = deep_res.get("Designation")
                            
                            deep_progress.progress((idx + 1) / len(found_cards))
                            deep_table_area.dataframe(pd.DataFrame(st.session_state.deep_search_results), use_container_width=True)
                        
                        st.session_state.deep_run_state = 'completed'
                    
                    if st.session_state.deep_run_state == 'completed':
                        deep_progress.progress(1.0)
                        deep_status_container.markdown('<div class="success-msg">Deep Search Completed!</div>', unsafe_allow_html=True)
                        deep_table_area.dataframe(pd.DataFrame(st.session_state.deep_search_results), use_container_width=True)

            # زر التحميل النهائي
            if len(st.session_state.batch_results) > 0:
                final_df = pd.DataFrame(st.session_state.batch_results)
                st.download_button(
                    label="📥 Download Full Report (CSV)",
                    data=final_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"mohre_full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
