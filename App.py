import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
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
            else: st.error("Incorrect Password.")
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
    except: return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=en-US')
    options.add_argument('--accept-lang=en-US,en;q=0.9')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

def extract_data(passport, nationality, dob_str):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()

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
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"),
            "Status": "Found"
        }
    except Exception as e:
        st.error(f"Initial search error: {str(e)}")
        return None
    finally: driver.quit()

# --- New Function: Deep Extract Data ---
def deep_extract_data(card_num):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)

        # Force English if needed
        lang_button = driver.find_element(By.ID, "btnlanguage")
        if "English" in lang_button.text or "استعلام" in driver.title:
            lang_button.click()
            time.sleep(3)
            driver.refresh()
            time.sleep(5)

        # Select "Electronic Work Permit Information" (value="EWPI")
        driver.find_element(By.ID, "dropdownButton").click()
        time.sleep(2)
        search_input = driver.find_element(By.ID, "searchInput")
        search_input.send_keys("Electronic Work Permit Information")
        time.sleep(2)
        options = driver.find_elements(By.CSS_SELECTOR, "#optionsList li")
        for opt in options:
            if "Electronic Work Permit Information" in opt.text:
                opt.click()
                break
        time.sleep(5)  # Wait for form to load

        # Find input by label proximity (robust)
        permit_input_xpath = "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'electronic work permit number') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'work permit number') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permit number')]/following-sibling::input[1] | //span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'electronic work permit number') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'work permit number') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'permit number')]/following::input[1]"
        permit_input = driver.find_element(By.XPATH, permit_input_xpath)
        permit_input.send_keys(card_num)

        # Bypass captcha with provided JS
        driver.execute_script("""(function(){try{const tryFill=()=>{const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));const input=Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"));if(code&&input){input.value=code;input.dispatchEvent(new Event('input',{bubbles:true}));}else{setTimeout(tryFill,500);}};tryFill();}catch(e){console.error('Error:',e);}})();""")
        time.sleep(3)

        # Submit by text (robust)
        submit_xpath = "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'inquiry') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search') or @type='submit']"
        driver.find_element(By.XPATH, submit_xpath).click()
        time.sleep(10)

        def get_value(label):
            try:
                xpath = f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label.lower()}')]/following::span[1] | //label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label.lower()}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return translate_to_english(val) if val else 'N/A'
            except: return 'N/A'

        return {
            "Name": get_value("Name"),
            "Est Name": get_value("Est Name"),
            "Company Code": get_value("Company Code"),
            "Designation": get_value("Designation")
        }
    except Exception as e:
        st.error(f"Deep search error for card {card_num}: {str(e)}")
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
                    st.session_state.single_res = res
                    st.rerun()
                else:
                    st.error("No data found.")
                    st.session_state.single_res = None

    if 'single_res' in st.session_state and st.session_state.single_res:
        single_df = pd.DataFrame([st.session_state.single_res])
        styled_single_df = single_df.style.map(color_status, subset=['Status']) if 'Status' in single_df.columns else single_df
        st.dataframe(styled_single_df)

        if st.session_state.single_res.get('Status') == 'Found' and 'Name' not in st.session_state.single_res:
            if st.button("Deep Search"):
                with st.spinner("Deep Searching..."):
                    card_num = st.session_state.single_res['Card Number']
                    deep_res = deep_extract_data(card_num)
                    if deep_res:
                        st.session_state.single_res['Name'] = deep_res.get('Name', 'N/A')
                        st.session_state.single_res['Est Name'] = deep_res.get('Est Name', 'N/A')
                        st.session_state.single_res['Company Code'] = deep_res.get('Company Code', 'N/A')
                        st.session_state.single_res['Job Description'] = deep_res.get('Designation', st.session_state.single_res['Job Description'])
                        st.rerun()

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

                # تخطي ما تمت معالجته
                if i < len(st.session_state.batch_results):
                    if st.session_state.batch_results[i].get("Status") == "Found":
                        actual_success += 1
                    continue

                p_num = str(row.get('Passport Number', '')).strip()
                nat = str(row.get('Nationality', 'Egypt')).strip()
                try: dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                except: dob = str(row.get('Date of Birth', ''))

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
                        "Status": "Not Found"
                    })

                # حساب الوقت الكلي بصيغة ساعات:دقائق:ثواني
                elapsed_seconds = time.time() - st.session_state.start_time_ref
                time_str = format_time(elapsed_seconds)

                progress_bar.progress((i + 1) / len(df))
                stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** {time_str}")

                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                live_table_area.dataframe(styled_df, use_container_width=True)

            if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
                st.success(f"Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
                final_df = pd.DataFrame(st.session_state.batch_results)
                st.download_button("Download Full Report (CSV)", final_df.to_csv(index=False).encode('utf-8'), "full_results.csv")

                # --- New Addition: Deep Search Button and Logic ---
                if 'deep_search_state' not in st.session_state:
                    st.session_state['deep_search_state'] = 'stopped'
                if 'deep_start_time_ref' not in st.session_state:
                    st.session_state['deep_start_time_ref'] = None

                if st.button("Deep Search"):
                    st.session_state.deep_search_state = 'running'
                    st.session_state.deep_start_time_ref = time.time()
                    found_indices = [i for i, res in enumerate(st.session_state.batch_results) if res['Status'] == 'Found']
                    total_found = len(found_indices)

                    if total_found == 0:
                        st.warning("No 'Found' records to perform Deep Search on.")
                        st.session_state.deep_search_state = 'stopped'
                    else:
                        deep_progress_bar = st.progress(0)
                        deep_status_text = st.empty()
                        deep_stats_area = st.empty()
                        # Use the same live_table_area to update the table without hiding original

                        processed_count = 0

                        for idx in found_indices:
                            if st.session_state.deep_search_state != 'running':
                                break

                            res = st.session_state.batch_results[idx]
                            card_num = res['Card Number']
                            deep_status_text.info(f"Deep Searching {processed_count + 1}/{total_found}: Card {card_num}")

                            deep_res = deep_extract_data(card_num)

                            if deep_res:
                                # Update existing res: Add new fields, replace Job Description with Designation
                                res['Name'] = deep_res.get('Name', 'N/A')
                                res['Est Name'] = deep_res.get('Est Name', 'N/A')
                                res['Company Code'] = deep_res.get('Company Code', 'N/A')
                                res['Job Description'] = deep_res.get('Designation', res['Job Description'])  # Replace, fallback to original

                            processed_count += 1

                            # Update time and progress
                            deep_elapsed_seconds = time.time() - st.session_state.deep_start_time_ref
                            deep_time_str = format_time(deep_elapsed_seconds)
                            deep_progress_bar.progress(processed_count / total_found)
                            deep_stats_area.markdown(f"🔍 **Deep Processed:** {processed_count} | ⏱️ **Deep Time:** {deep_time_str}")

                            # Update the live table (same as original)
                            current_df = pd.DataFrame(st.session_state.batch_results)
                            styled_df = current_df.style.map(color_status, subset=['Status'])
                            live_table_area.dataframe(styled_df, use_container_width=True)

                        if processed_count == total_found:
                            st.success(f"Deep Search Completed! Total Deep Time: {format_time(time.time() - st.session_state.deep_start_time_ref)}")
                            st.session_state.deep_search_state = 'stopped'
                            updated_df = pd.DataFrame(st.session_state.batch_results)
                            st.download_button("Download Updated Full Report (CSV)", updated_df.to_csv(index=False).encode('utf-8'), "updated_full_results.csv")
