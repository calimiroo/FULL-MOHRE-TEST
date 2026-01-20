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
if 'single_search_result' not in st.session_state:
    st.session_state['single_search_result'] = None

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
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)


def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'


# --- استخراج بيانات من الموقع الأول ---
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
            if items:
                items[0].click()
        except Exception:
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
            # حقول Deep Search (فارغة في البداية)
            "Name": "",
            "Est Name": "",
            "Company Code": "",
            "Designation": ""
        }
    except Exception as e:
        st.error(f"Error in extract_data: {str(e)}")
        return None
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# --- وظيفة البحث العميق المحسّنة ---
def deep_extract_by_card(card_number):
    """البحث العميق المحسّن مع معالجة أفضل للعناصر"""
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(3)

        # 1) اختيار نوع الاستعلام
        try:
            dropdown_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "dropdownButton"))
            )
            dropdown_btn.click()
            time.sleep(1)
            
            # محاولة العثور على EWPI
            dropdown_items = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
            for item in dropdown_items:
                if 'EWPI' in item.get_attribute('value') or 'Electronic Work Permit' in item.text:
                    driver.execute_script("arguments[0].click();", item)
                    break
        except Exception as e:
            st.warning(f"Dropdown selection issue: {str(e)}")

        time.sleep(2)

        # 2) إدخال رقم البطاقة - البحث عن الحقل الصحيح
        card_input = None
        try:
            # جرب عدة طرق للعثور على حقل الإدخال
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for inp in inputs:
                # تحقق من أن الحقل ليس للكابتشا
                placeholder = inp.get_attribute('placeholder') or ''
                if 'التحقق' not in placeholder and 'captcha' not in placeholder.lower():
                    card_input = inp
                    break
            
            if card_input:
                card_input.clear()
                time.sleep(0.5)
                card_input.send_keys(card_number)
                time.sleep(1)
        except Exception as e:
            st.warning(f"Input field issue: {str(e)}")

        # 3) معالجة الكابتشا
        try:
            captcha_code = None
            # البحث عن كود الكابتشا في الصفحة
            page_elements = driver.find_elements(By.XPATH, "//*[string-length(normalize-space(text()))=4 and number(normalize-space(text()))=normalize-space(text())]")
            for elem in page_elements:
                text = elem.text.strip()
                if len(text) == 4 and text.isdigit():
                    captcha_code = text
                    break
            
            if captcha_code:
                # البحث عن حقل إدخال الكابتشا
                captcha_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for inp in captcha_inputs:
                    placeholder = inp.get_attribute('placeholder') or ''
                    if 'التحقق' in placeholder or 'captcha' in placeholder.lower() or 'verification' in placeholder.lower():
                        inp.clear()
                        inp.send_keys(captcha_code)
                        break
        except Exception as e:
            st.warning(f"Captcha handling issue: {str(e)}")

        time.sleep(2)

        # 4) الضغط على زر البحث
        try:
            search_button = None
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.strip().lower()
                if any(word in btn_text for word in ['search', 'بحث', 'view', 'submit']):
                    search_button = btn
                    break
            
            if search_button:
                driver.execute_script("arguments[0].click();", search_button)
                time.sleep(5)
        except Exception as e:
            st.warning(f"Search button click issue: {str(e)}")

        # 5) استخراج البيانات - طريقة محسّنة
        def extract_field_value(label_text):
            """استخراج قيمة الحقل بطرق متعددة"""
            try:
                # الطريقة 1: البحث عن Label ثم القيمة التالية
                labels = driver.find_elements(By.XPATH, f"//*[contains(text(), '{label_text}')]")
                for label in labels:
                    try:
                        # محاولة الحصول على العنصر التالي
                        parent = label.find_element(By.XPATH, "./..")
                        siblings = parent.find_elements(By.XPATH, "./*")
                        for i, sib in enumerate(siblings):
                            if label_text in sib.text and i + 1 < len(siblings):
                                value = siblings[i + 1].text.strip()
                                if value and value != label_text:
                                    return value
                    except:
                        continue
                
                # الطريقة 2: البحث في نص الصفحة الكامل
                page_text = driver.find_element(By.TAG_NAME, "body").text
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if label_text in line:
                        # تحقق من السطر الحالي أولاً
                        if ':' in line:
                            parts = line.split(':', 1)
                            if len(parts) > 1 and parts[1].strip():
                                return parts[1].strip()
                        # تحقق من السطر التالي
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and next_line != label_text:
                                return next_line
                
                return 'Not Found'
            except Exception as e:
                return 'Not Found'

        # استخراج جميع الحقول
        name = extract_field_value('Name')
        est_name = extract_field_value('Est Name')
        if est_name == 'Not Found':
            est_name = extract_field_value('Establishment Name')
        company_code = extract_field_value('Company Code')
        if company_code == 'Not Found':
            company_code = extract_field_value('Est Code')
        designation = extract_field_value('Designation')
        if designation == 'Not Found':
            designation = extract_field_value('Job Title')

        # التحقق من وجود بيانات فعلية
        if all(v == 'Not Found' for v in [name, est_name, company_code, designation]):
            # محاولة أخيرة: حفظ لقطة شاشة للتشخيص
            try:
                driver.save_screenshot(f'/tmp/debug_{card_number}.png')
                st.info(f"No data found for card {card_number}. Screenshot saved for debugging.")
            except:
                pass
            return None

        return {
            'Name': name,
            'Est Name': est_name,
            'Company Code': company_code,
            'Designation': designation
        }

    except Exception as e:
        st.error(f"Deep search error for card {card_number}: {str(e)}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


# --- واجهة المستخدم ---

tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"]) 

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🔍 Search Now", use_container_width=True):
            if p_in and n_in != "Select Nationality" and d_in:
                with st.spinner("Searching in first portal..."):
                    res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                    if res:
                        st.session_state['single_search_result'] = res
                        st.success("✅ Data found!")
                    else:
                        st.session_state['single_search_result'] = None
                        st.error("❌ No data found.")
            else:
                st.warning("⚠️ Please fill all fields")
    
    # عرض النتيجة إذا كانت موجودة
    if st.session_state.get('single_search_result'):
        result_df = pd.DataFrame([st.session_state['single_search_result']])
        
        # إعادة ترتيب الأعمدة
        basic_cols = ["Passport Number", "Nationality", "Date of Birth", "Job Description", 
                      "Card Number", "Card Issue", "Card Expiry", "Basic Salary", "Total Salary", "Status"]
        deep_cols = ["Name", "Est Name", "Company Code", "Designation"]
        
        # عرض البيانات الأساسية
        st.subheader("📋 Basic Information")
        display_df = result_df[basic_cols].copy()
        styled_df = display_df.style.map(color_status, subset=['Status'])
        st.dataframe(styled_df, width=None)
        
        # زر البحث العميق
        with col_btn2:
            if st.button("🔎 Deep Search", use_container_width=True):
                card_num = st.session_state['single_search_result'].get('Card Number')
                if card_num and card_num not in ['N/A', 'Not Found', '']:
                    with st.spinner(f"Deep searching for card: {card_num}..."):
                        deep_res = deep_extract_by_card(card_num)
                        if deep_res:
                            # تحديث النتيجة
                            st.session_state['single_search_result']['Name'] = deep_res.get('Name', 'Not Found')
                            st.session_state['single_search_result']['Est Name'] = deep_res.get('Est Name', 'Not Found')
                            st.session_state['single_search_result']['Company Code'] = deep_res.get('Company Code', 'Not Found')
                            st.session_state['single_search_result']['Designation'] = deep_res.get('Designation', 'Not Found')
                            # استبدال Job Description بـ Designation
                            st.session_state['single_search_result']['Job Description'] = deep_res.get('Designation', st.session_state['single_search_result']['Job Description'])
                            st.success("✅ Deep search completed!")
                            st.rerun()
                        else:
                            st.error("❌ Deep search failed - no additional data found")
                else:
                    st.warning("⚠️ No valid Card Number for deep search")
        
        # عرض بيانات البحث العميق إن وجدت
        if any(st.session_state['single_search_result'].get(col) for col in deep_cols):
            st.subheader("🔎 Deep Search Results")
            deep_df = result_df[deep_cols].copy()
            st.dataframe(deep_df, width=None)
        
        # زر التحميل
        final_single_df = pd.DataFrame([st.session_state['single_search_result']])
        csv = final_single_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Result (CSV)",
            data=csv,
            file_name=f"result_{p_in}.csv",
            mime="text/csv"
        )

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
        deep_progress_container = st.empty()

        actual_success = 0

        # البحث الأساسي
        for i, row in df.iterrows():
            while st.session_state.run_state == 'paused':
                status_text.warning("⏸️ Paused... click Resume to continue.")
                time.sleep(1)
            if st.session_state.run_state == 'stopped':
                break

            if i < len(st.session_state.batch_results):
                if st.session_state.batch_results[i].get("Status") == "Found":
                    actual_success += 1
                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                live_table_area.dataframe(styled_df, width=None)
                progress_bar.progress((i + 1) / len(df))
                elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
                stats_area.markdown(f"✅ **Success:** {actual_success} | ⏱️ **Time:** `{format_time(elapsed_seconds)}`")
                continue

            p_num = str(row.get('Passport Number', '')).strip()
            nat = str(row.get('Nationality', 'Egypt')).strip()
            try:
                dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except:
                dob = str(row.get('Date of Birth', ''))

            status_text.info(f"🔍 Processing {i+1}/{len(df)}: {p_num}")
            res = extract_data(p_num, nat, dob)

            if res:
                actual_success += 1
                st.session_state.batch_results.append(res)
            else:
                st.session_state.batch_results.append({
                    "Passport Number": p_num,
                    "Nationality": nat,
                    "Date of Birth": dob,
                    "Job Description": "N/A",
                    "Card Number": "N/A",
                    "Card Issue": "N/A",
                    "Card Expiry": "N/A",
                    "Basic Salary": "N/A",
                    "Total Salary": "N/A",
                    "Status": "Not Found",
                    "Name": "",
                    "Est Name": "",
                    "Company Code": "",
                    "Designation": ""
                })

            elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ **Success:** {actual_success} | ⏱️ **Time:** `{format_time(elapsed_seconds)}`")

            current_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = current_df.style.map(color_status, subset=['Status'])
            live_table_area.dataframe(styled_df, width=None)

        # عند اكتمال البحث الأساسي
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success(f"✅ Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
            final_df = pd.DataFrame(st.session_state.batch_results)
            
            csv_basic = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Basic Report (CSV)", csv_basic, "basic_results.csv", mime="text/csv")

            # زر البحث العميق
            if st.button("🔎 Start Deep Search", key="deep_search_btn"):
                st.session_state.deep_run_state = 'running'
                st.rerun()

            # تنفيذ البحث العميق
            if st.session_state.deep_run_state == 'running':
                found_records = [r for r in st.session_state.batch_results 
                               if r.get('Status') == 'Found' and r.get('Card Number') not in [None, 'N/A', 'Not Found', '']]
                
                if not found_records:
                    st.info("ℹ️ No 'Found' records with valid Card Number to Deep Search.")
                    st.session_state.deep_run_state = 'stopped'
                else:
                    deep_total = len(found_records)
                    deep_success = 0
                    
                    with deep_progress_container.container():
                        deep_prog_bar = st.progress(0)
                        deep_stat_text = st.empty()
                    
                    for idx, rec in enumerate(st.session_state.batch_results):
                        if st.session_state.deep_run_state != 'running':
                            break
                        if rec.get('Status') != 'Found':
                            continue
                        card = rec.get('Card Number')
                        if not card or card in ['N/A', 'Not Found']:
                            continue

                        deep_stat_text.info(f"🔎 Deep Search {deep_success+1}/{deep_total}: Card {card}")
                        
                        deep_res = deep_extract_by_card(card)
                        if deep_res:
                            deep_success += 1
                            st.session_state.batch_results[idx]['Name'] = deep_res.get('Name', 'Not Found')
                            st.session_state.batch_results[idx]['Est Name'] = deep_res.get('Est Name', 'Not Found')
                            st.session_state.batch_results[idx]['Company Code'] = deep_res.get('Company Code', 'Not Found')
                            st.session_state.batch_results[idx]['Designation'] = deep_res.get('Designation', 'Not Found')
                            st.session_state.batch_results[idx]['Job Description'] = deep_res.get('Designation', st.session_state.batch_results[idx]['Job Description'])
                        else:
                            st.session_state.batch_results[idx]['Name'] = 'Not Found'
                            st.session_state.batch_results[idx]['Est Name'] = 'Not Found'
                            st.session_state.batch_results[idx]['Company Code'] = 'Not Found'

                        deep_prog_bar.progress((deep_success) / deep_total)
                        
                        # تحديث الجدول
                        updated_df = pd.DataFrame(st.session_state.batch_results)
                        styled_updated = updated_df.style.map(color_status, subset=['Status'])
                        live_table_area.dataframe(styled_updated, width=None)

                    st.success(f"✅ Deep Search Completed: {deep_success}/{deep_total} succeeded")
                    
                    final_deep_df = pd.DataFrame(st.session_state.batch_results)
                    csv_deep = final_deep_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Full Report with Deep Search (CSV)", 
                                     csv_deep, 
                                     "full_results_deep.csv",
                                     mime="text/csv")
                    st.session_state.deep_run_state = 'stopped'
