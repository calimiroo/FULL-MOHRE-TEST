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
if 'single_res' not in st.session_state:
    st.session_state['single_res'] = None

# قائمة الجنسيات (محفوظة كما هي)
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
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- استخراج بيانات من الموقع الأول ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 15)
        
        passport_input = wait.until(EC.presence_of_element_located((By.ID, "txtPassportNumber")))
        passport_input.send_keys(passport)
        
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        try:
            search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")))
            search_box.send_keys(nationality)
            time.sleep(1)
            items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
            if items:
                items[0].click()
        except:
            pass

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
    except Exception:
        return None
    finally:
        driver.quit()

# --- وظيفة البحث العميق في الموقع الثاني ---
def deep_extract_by_card(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 20)
        
        # 1) اختيار الخدمة
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        dropdown_btn.click()
        time.sleep(1)
        
        option = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[@role='option' and @value='EWPI']")))
        option.click()
        time.sleep(2)
        
        # 2) إدخال رقم البطاقة
        wait.until(EC.presence_of_element_located((By.ID, "txtWorkPermitNo")))
        driver.find_element(By.ID, "txtWorkPermitNo").send_keys(card_number)
        
        # 3) ملء الكابتشا آلياً
        try:
            js_fill_captcha = r"""
            try{
                const tryFill=()=>{
                    const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));
                    const input=Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"));
                    if(code&&input){input.value=code;input.dispatchEvent(new Event('input',{bubbles:true}));}
                };
                tryFill();
            }catch(e){}            
            """
            driver.execute_script(js_fill_captcha)
        except:
            pass
        
        time.sleep(1)
        
        # 4) الضغط على بحث
        driver.find_element(By.ID, "btnSearch").click()
        time.sleep(5)
        
        # 5) استخراج البيانات
        res = {
            "Card Number": card_number,
            "Name": "Not Found",
            "Est Name": "Not Found",
            "Company Code": "Not Found",
            "Designation": "Not Found"
        }
        
        labels_map = {
            "Name": ["Name", "Worker Name", "lblNameEn"],
            "Est Name": ["Establishment Name", "Company Name", "lblEstablishmentNameEn"],
            "Company Code": ["Establishment Number", "Company Code", "lblEstablishmentNo"],
            "Designation": ["Designation", "Profession", "lblDesignationEn"]
        }
        
        for key, labels in labels_map.items():
            for label in labels:
                try:
                    if label.startswith("lbl"):
                        val = driver.find_element(By.ID, label).text.strip()
                    else:
                        xpath = f"//*[contains(text(), '{label}')]/following::span[1]"
                        val = driver.find_element(By.XPATH, xpath).text.strip()
                    if val and val != "N/A":
                        res[key] = val
                        break
                except:
                    continue
        return res
    except Exception:
        return None
    finally:
        driver.quit()

# --- واجهة المستخدم ---
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
                if res:
                    st.session_state['single_res'] = res
                else:
                    st.error("No data found.")
                    st.session_state['single_res'] = None

    if st.session_state['single_res']:
        st.table(pd.DataFrame([st.session_state['single_res']]))
        card_no = st.session_state['single_res'].get("Card Number")
        if card_no and card_no != "N/A":
            if st.button(f"🔍 Deep Search for Card: {card_no}"):
                with st.spinner(f"Deep Searching Card: {card_no}..."):
                    deep_res = deep_search_extract = deep_extract_by_card(card_no)
                    if deep_res:
                        st.session_state['single_res'].update({
                            "Name": deep_res.get("Name"),
                            "Est Name": deep_res.get("Est Name"),
                            "Company Code": deep_res.get("Company Code"),
                            "Job Description": deep_res.get("Designation") if deep_res.get("Designation") != "Not Found" else st.session_state['single_res']["Job Description"]
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

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        if col_ctrl1.button("▶️ Start / Resume"):
            st.session_state.run_state = 'running'
            if st.session_state.start_time_ref is None:
                st.session_state.start_time_ref = time.time()
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

        for i, row in df.iterrows():
            while st.session_state.run_state == 'paused':
                status_text.warning("Paused... click Resume to continue.")
                time.sleep(1)
            if st.session_state.run_state == 'stopped':
                break

            if i < len(st.session_state.batch_results):
                if st.session_state.batch_results[i].get("Status") == "Found":
                    actual_success += 1
                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                live_table_area.dataframe(styled_df, use_container_width=True)
                progress_bar.progress((i + 1) / len(df))
                elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
                stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** `{format_time(elapsed_seconds)}`")
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

            elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** `{format_time(elapsed_seconds)}`")

            current_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = current_df.style.map(color_status, subset=['Status'])
            live_table_area.dataframe(styled_df, use_container_width=True)

        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success(f"Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
            final_df = pd.DataFrame(st.session_state.batch_results)
            st.download_button("Download Full Report (CSV)", final_df.to_csv(index=False).encode('utf-8'), "full_results.csv")

            if st.button("Deep Search (Search cards on inquiry.mohre.gov.ae)"):
                st.session_state.deep_run_state = 'running'
                st.session_state.deep_progress = 0

            if st.session_state.deep_run_state == 'running':
                deep_total = sum(1 for r in st.session_state.batch_results if r.get('Status') == 'Found' and r.get('Card Number') not in [None, 'N/A', 'Not Found', ''])
                if deep_total == 0:
                    st.info("No 'Found' records with valid Card Number to Deep Search.")
                    st.session_state.deep_run_state = 'stopped'
                else:
                    deep_idx = 0
                    deep_success = 0
                    deep_progress_bar = st.progress(0)
                    for idx, rec in enumerate(st.session_state.batch_results):
                        if st.session_state.deep_run_state != 'running': break
                        if rec.get('Status') != 'Found': continue
                        card = rec.get('Card Number')
                        if not card or card in ['N/A', 'Not Found']: continue

                        deep_status_area.info(f"Deep Searching {deep_idx+1}/{deep_total}: {card}")
                        deep_res = deep_extract_by_card(card)
                        if deep_res:
                            deep_success += 1
                            st.session_state.batch_results[idx]['Job Description'] = deep_res.get('Designation', 'Not Found')
                            st.session_state.batch_results[idx]['Name'] = deep_res.get('Name', '')
                            st.session_state.batch_results[idx]['Est Name'] = deep_res.get('Est Name', '')
                            st.session_state.batch_results[idx]['Company Code'] = deep_res.get('Company Code', '')
                        
                        deep_idx += 1
                        deep_progress_bar.progress(min(1.0, deep_idx / deep_total))
                        current_df = pd.DataFrame(st.session_state.batch_results)
                        live_table_area.dataframe(current_df.style.map(color_status, subset=['Status']), use_container_width=True)

                    st.success(f"Deep Search Completed: {deep_success}/{deep_total} succeeded")
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    st.download_button("Download Final Full Report (CSV)", final_df.to_csv(index=False).encode('utf-8'), "full_results_with_deep.csv")
                    st.session_state.deep_run_state = 'stopped'
