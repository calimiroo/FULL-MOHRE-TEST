import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import logging
import os

# --- إعداد السجل ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST - FIXED")

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
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'deep_single_running' not in st.session_state:
    st.session_state['deep_single_running'] = False
if 'deep_single_card' not in st.session_state:
    st.session_state['deep_single_card'] = None
if 'deep_single_result' not in st.session_state:
    st.session_state['deep_single_result'] = {}
if 'deep_current_index' not in st.session_state:
    st.session_state['deep_current_index'] = 0
if 'single_search_executed' not in st.session_state:
    st.session_state['single_search_executed'] = False
if 'deep_search_started' not in st.session_state:
    st.session_state['deep_search_started'] = False

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
    # استخدام وضع headless الجديد لتجنب اكتشاف البوت
    options.add_argument('--headless=new') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080') # ضروري جداً للمواقع الحديثة
    options.add_argument('--start-maximized')
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
        
        # الانتظار حتى تحميل العناصر
        passport_field = wait.until(EC.element_to_be_clickable((By.ID, "txtPassportNumber")))
        passport_field.send_keys(passport)
        
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        try:
            search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")))
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
        # تفعيل الحدث للتأكد
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        
        driver.find_element(By.ID, "btnSubmit").click()
        
        # انتظار ذكي للنتيجة
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Card Number')]")))
        except TimeoutException:
            # إذا لم يظهر العنصر بعد 10 ثواني، نعتبره غير موجود
            pass

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
            "Status": "Found"
        }
    except Exception as e:
        logger.error(f"Error in extract_data for passport {passport}: {e}")
        return None
    finally:
        try:
            driver.quit()
        except Exception:
            pass

# --- وظيفة البحث العميق في الموقع الثاني (inquiry.mohre.gov.ae) ---
def deep_extract_by_card(card_number):
    """تحاول الوصول لصفحة Inquiry وتبحث برقم البطاقة"""
    if not card_number or card_number in ['N/A', 'Not Found', 'Not Available']:
        return {
            'Name': 'Invalid Card Number',
            'Est Name': 'Invalid Card Number',
            'Company Code': 'Invalid Card Number',
            'Designation': 'Invalid Card Number'
        }

    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 25)

        # 1. فتح القائمة المنسدلة للخدمات
        logger.info("Opening dropdown...")
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_btn)
        time.sleep(1)
        dropdown_btn.click()

        # 2. اختيار الخدمة الصحيحة
        logger.info("Selecting Service...")
        # استخدام XPath للبحث عن النص بدقة
        service_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(., 'Electronic Work Permit Information')]")))
        service_option.click()
        time.sleep(2) # انتظار تحميل نموذج الخدمة

        # 3. إدخال رقم البطاقة (تصحيح الخطأ هنا: استخدام send_keys بدلاً من JS)
        logger.info(f"Entering card number: {card_number}")
        
        # البحث عن الحقل بذكاء (قد يتغير الـ ID)
        card_input = None
        possible_selectors = [
            (By.NAME, "CardNumber"), # تخمين
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[@placeholder='Enter Work Permit Number']"),
            (By.XPATH, "//input[contains(@class, 'form-control')]")
        ]
        
        for by, val in possible_selectors:
            try:
                inputs = driver.find_elements(by, val)
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        card_input = inp
                        break
                if card_input: break
            except:
                pass
        
        if card_input:
            card_input.clear()
            # الطريقة الصحيحة لتفعيل تفاعل الموقع
            card_input.send_keys(card_number)
            time.sleep(0.5)
            # إرسال زر TAB للتأكد من خروج التركيز وتفعيل التحقق
            card_input.send_keys(Keys.TAB)
        else:
            logger.error("Could not find card input field")
            return None

        # 4. الضغط على زر البحث
        logger.info("Clicking Search...")
        time.sleep(1)
        search_btn = None
        try:
            search_btn = driver.find_element(By.ID, "btnSearch")
        except:
            # محاولة البحث عن الزر بالنص
            search_btn = driver.find_element(By.XPATH, "//button[contains(., 'Search') or contains(., 'بحث')]")
            
        if search_btn:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
            time.sleep(0.5)
            search_btn.click()
        else:
            logger.error("Search button not found")
            return None

        # 5. انتظار النتائج
        logger.info("Waiting for results...")
        # ننتظر ظهور أي عنصر يدل على النتيجة (مثل الاسم أو اسم المنشأة)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Person Name') or contains(text(), 'Company Name') or contains(text(), 'Designation')]")))
        except TimeoutException:
            logger.warning("Timeout waiting for results or No records found.")
            # قد تكون النتيجة "No Data Found"
            if "no data" in driver.page_source.lower():
                return {'Name': 'Not Available', 'Est Name': 'Not Available', 'Company Code': 'Not Available', 'Designation': 'Not Available'}

        # 6. استخراج البيانات (تحسين طريقة البحث عن النصوص)
        def robust_get_text(label_keywords):
            try:
                # نبحث عن الليبل أولاً
                for keyword in label_keywords:
                    # XPath يبحث عن العنصر الذي يحتوي النص، ثم يأخذ العنصر التالي له أو القيمة بداخله
                    xpaths = [
                        f"//*[contains(text(), '{keyword}')]/following-sibling::span[1]",
                        f"//*[contains(text(), '{keyword}')]/following-sibling::div[1]",
                        f"//*[contains(text(), '{keyword}')]/../following-sibling::div[1]", # أحيانا يكون في هيكل Grid
                        f"//label[contains(text(), '{keyword}')]/..//following-sibling::div"
                    ]
                    for xp in xpaths:
                        elems = driver.find_elements(By.XPATH, xp)
                        for elem in elems:
                            txt = elem.text.strip()
                            if txt and txt != keyword: # التأكد أنه ليس العنوان نفسه
                                return txt
                return 'Not Available'
            except Exception:
                return 'Not Available'

        name = robust_get_text(['Person Name', 'Name', 'الإسم'])
        est_name = robust_get_text(['Company Name', 'Establishment Name', 'Est Name', 'اسم المنشأة'])
        company_code = robust_get_text(['Company Code', 'Establishment Code', 'رقم المنشأة'])
        designation = robust_get_text(['Designation', 'Job', 'المهنة'])

        # تنظيف البيانات إذا رجعنا بنفس اسم الليبل
        return {
            'Name': name,
            'Est Name': est_name,
            'Company Code': company_code,
            'Designation': designation
        }

    except Exception as e:
        logger.error(f"Error in deep_extract_by_card: {e}")
        return {
            'Name': 'Error',
            'Est Name': 'Error',
            'Company Code': 'Error',
            'Designation': 'Error'
        }
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
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res:
                    st.session_state['single_result'] = res
                    st.session_state['deep_single_running'] = False
                    st.session_state['deep_single_card'] = None
                    st.session_state['deep_single_result'] = {}
                    st.session_state['single_search_executed'] = True
                else:
                    st.error("No data found.")
                    st.session_state['single_result'] = None
                    st.session_state['single_search_executed'] = True

    # عرض نتيجة البحث الفردي
    if st.session_state['single_search_executed']:
        if st.session_state['single_result']:
            result_df = pd.DataFrame([st.session_state['single_result']])

            # إذا كانت النتيجة تحتوي على Card Number، عرضها كجدول مع رابط للبحث العميق
            if st.session_state['single_result']['Card Number'] != 'N/A' and st.session_state['single_result']['Card Number'] != 'Not Found':
                card_num_display = st.session_state['single_result']['Card Number']

                # عرض الجدول الأصلي (إعادة use_container_width لتجنب الانهيار)
                st.dataframe(result_df, use_container_width=True) 
                
                # إنشاء زر للبحث العميق
                if st.button(f"🔍 Deep Search Card {card_num_display}", key=f"deep_search_{card_num_display}"):
                    st.session_state['deep_single_running'] = True
                    st.session_state['deep_single_card'] = card_num_display
                    st.rerun()
                
                # تنفيذ البحث العميق
                if st.session_state['deep_single_running'] and not st.session_state['deep_single_result']:
                    card_to_search = st.session_state['single_result']['Card Number']
                    if card_to_search == st.session_state['deep_single_card']:
                        with st.spinner(f"Deep searching card {card_to_search}..."):
                            deep_res = deep_extract_by_card(card_to_search)
                            if deep_res:
                                st.session_state['deep_single_result'] = deep_res
                                # تحديث نتيجة البحث الفردي
                                updated_res = st.session_state['single_result'].copy()
                                updated_res['Job Description'] = deep_res.get('Designation', 'Not Available')
                                updated_res['Name'] = deep_res.get('Name', 'Not Available')
                                updated_res['Est Name'] = deep_res.get('Est Name', 'Not Available')
                                updated_res['Company Code'] = deep_res.get('Company Code', 'Not Available')
                                st.session_state['single_result'] = updated_res
                                st.success(f"Deep search completed for card {card_to_search}.")
                            else:
                                st.error(f"Deep search failed for card {card_to_search}.")
                                # إضافة الحقول الفارغة
                                updated_res = st.session_state['single_result'].copy()
                                updated_res['Name'] = 'Not Available'
                                updated_res['Est Name'] = 'Not Available'
                                updated_res['Company Code'] = 'Not Available'
                                st.session_state['single_result'] = updated_res
                            st.session_state['deep_single_running'] = False
                            st.rerun()
                
                # عرض النتيجة المحدثة بعد انتهاء البحث العميق
                if st.session_state['deep_single_result']:
                    updated_df = pd.DataFrame([st.session_state['single_result']])
                    st.dataframe(updated_df, use_container_width=True)
                    # زر تحميل النتيجة المحدثة
                    csv = updated_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Single Result (CSV)",
                        data=csv,
                        file_name=f"single_result_{st.session_state['single_result']['Card Number']}.csv",
                        mime='text/csv'
                    )
            else:
                # إذا لم يكن هناك Card Number، عرض النتيجة العادية
                st.dataframe(result_df, use_container_width=True)
        else:
            st.info("Please enter search criteria and click 'Search Now'.")
    else:
        st.info("Please enter search criteria and click 'Search Now'.")


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
            st.session_state.deep_current_index = 0
            st.session_state.deep_search_started = False
            st.rerun()

        # مساحات العرض الحية
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_area = st.empty()
        live_table_area = st.empty()
        deep_status_area = st.empty()
        deep_progress_bar = st.empty()

        actual_success = 0
        # تنفيذ البحث الأولي
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
            try:
                dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except:
                dob = str(row.get('Date of Birth', ''))

            status_text.info(f"Processing {i+1}/{len(df)}: {p_num}")
            res = extract_data(p_num, nat, dob)

            if res:
                actual_success += 1
                # تأكد من وجود الحقول الجديدة
                res.setdefault('Name', 'N/A')
                res.setdefault('Est Name', 'N/A')
                res.setdefault('Company Code', 'N/A')
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
                    "Name": "N/A",
                    "Est Name": "N/A",
                    "Company Code": "N/A"
                })

            # تحديث الجدول الحي
            elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            time_str = format_time(elapsed_seconds)
            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** `{time_str}`")
            current_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = current_df.style.map(color_status, subset=['Status'])
            # إعادة use_container_width هنا أيضاً
            live_table_area.dataframe(styled_df, use_container_width=True)

        # عند اكتمال البحث الأولي
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success(f"Batch Initial Search Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
            final_df_initial = pd.DataFrame(st.session_state.batch_results)
            # زر تحميل أولي
            csv_initial = final_df_initial.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Initial Batch Results (CSV)",
                csv_initial,
                "initial_batch_results.csv",
                mime='text/csv'
            )

            # زر البحث العميق
            if st.button("Deep Search (Search cards on inquiry.mohre.gov.ae)") and not st.session_state['deep_search_started']:
                st.session_state.deep_run_state = 'running'
                st.session_state.deep_current_index = 0
                st.session_state.deep_search_started = True

            # تنفيذ البحث العميق إذا بدأ
            if st.session_state.deep_run_state == 'running':
                deep_total = sum(1 for r in st.session_state.batch_results if r.get('Status') == 'Found' and r.get('Card Number') not in [None, 'N/A', 'Not Found', ''])
                if deep_total == 0:
                    st.info("No 'Found' records with valid Card Number to Deep Search.")
                    st.session_state.deep_run_state = 'stopped'
                    st.session_state.deep_search_started = False
                else:
                    deep_idx = 0
                    deep_success = 0
                    deep_progress_bar.progress(0)
                    deep_status_area.info("Starting Deep Search for Found records...")

                    # استمرار البحث من آخر نقطة
                    while st.session_state.deep_current_index < len(st.session_state.batch_results) and st.session_state.deep_run_state == 'running':
                        rec = st.session_state.batch_results[st.session_state.deep_current_index]
                        if rec.get('Status') != 'Found':
                            st.session_state.deep_current_index += 1
                            continue
                        
                        card = rec.get('Card Number')
                        if not card or card in ['N/A', 'Not Found']:
                            st.session_state.deep_current_index += 1
                            continue

                        deep_status_area.info(f"Deep Searching {deep_idx+1}/{deep_total}: {card}")
                        
                        # نفذ البحث العميق
                        deep_res = deep_extract_by_card(card)
                        if deep_res:
                            deep_success += 1
                            # استبدل Job Description بقيمة Designation
                            designation = deep_res.get('Designation', 'Not Available')
                            st.session_state.batch_results[st.session_state.deep_current_index]['Job Description'] = designation
                            # أضف الحقول الجديدة
                            st.session_state.batch_results[st.session_state.deep_current_index]['Name'] = deep_res.get('Name', 'Not Available')
                            st.session_state.batch_results[st.session_state.deep_current_index]['Est Name'] = deep_res.get('Est Name', 'Not Available')
                            st.session_state.batch_results[st.session_state.deep_current_index]['Company Code'] = deep_res.get('Company Code', 'Not Available')
                        else:
                            # ضع حقول فارغة أو Not Found
                            st.session_state.batch_results[st.session_state.deep_current_index]['Name'] = 'Not Available'
                            st.session_state.batch_results[st.session_state.deep_current_index]['Est Name'] = 'Not Available'
                            st.session_state.batch_results[st.session_state.deep_current_index]['Company Code'] = 'Not Available'

                        deep_idx += 1
                        st.session_state.deep_current_index += 1
                        st.session_state.deep_progress = deep_idx / deep_total
                        deep_progress_bar.progress(min(1.0, st.session_state.deep_progress))

                        # حدث عرض الجدول الأولي مباشرةً
                        current_df = pd.DataFrame(st.session_state.batch_results)
                        styled_df = current_df.style.map(color_status, subset=['Status'])
                        live_table_area.dataframe(styled_df, use_container_width=True)

                    if st.session_state.deep_current_index >= len(st.session_state.batch_results):
                        st.success(f"Deep Search Completed: {deep_success}/{deep_total} succeeded")
                        st.session_state.deep_run_state = 'stopped'
                        st.session_state.deep_search_started = False
                        
                        # زر تحميل الملف النهائي بعد الـ Deep Search
                        final_df = pd.DataFrame(st.session_state.batch_results)
                        csv_final = final_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Final Full Report (CSV)",
                            csv_final,
                            "full_results_with_deep.csv",
                            mime='text/csv'
                        )
