import streamlit as st 
import pandas as pd 
import time 
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
from datetime import datetime, timedelta 
from deep_translator import GoogleTranslator
import logging

# --- إعداد السجل ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# إضافة متغيرات جديدة لدعم التفاعل في البحث الفردي
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
    """تحاول الوصول لصفحة Inquiry وتبحث برقم البطاقة وتحصل على Name, Est Name, Company Code, Designation"""
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 20) # زيادة وقت الانتظار

        # 1) افتح القائمة المنسدلة واختر "Electronic Work Permit Information"
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        # التمرير إلى العنصر لجعله مرئيًا
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_btn)
        dropdown_btn.click()
        time.sleep(1)

        # انتظر حتى تصبح القائمة مرئية
        wait.until(EC.presence_of_element_located((By.ID, "dropdownList")))

        # ابحث عن العنصر باستخدام النص أو القيمة
        ewpi_option = None
        try:
            ewpi_option = driver.find_element(By.CSS_SELECTOR, "li[value='EWPI']")
        except:
            pass
        if not ewpi_option:
            try:
                ewpi_option = driver.find_element(By.XPATH, "//li[contains(text(), 'Electronic Work Permit Information')]")
            except:
                pass
        
        if ewpi_option:
            # التمرير إلى الخيار
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ewpi_option)
            # استخدام execute_script للنقر لأنه أكثر موثوقية
            driver.execute_script("arguments[0].click();", ewpi_option)
            time.sleep(1)
        else:
            logger.warning("Could not find 'Electronic Work Permit Information' option.")
            return None

        # 2) أدخل رقم البطاقة
        # حاول العثور على حقل الإدخال المناسب
        card_input = None
        try:
            # حاول العثور على حقل الإدخال باستخدام placeholder
            card_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Card') or contains(@placeholder, 'Work Permit')]")))
        except:
            pass
        if not card_input:
            try:
                # حاول العثور على أول حقل إدخال نص
                card_input = driver.find_element(By.TAG_NAME, "input")
            except:
                pass

        if card_input:
            # التمرير إلى الحقل
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_input)
            # مسح الحقل
            driver.execute_script("arguments[0].value = '';", card_input)
            # إدخال الرقم
            driver.execute_script(f"arguments[0].value = '{card_number}';", card_input)
            # تشغيل حدث الإدخال
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {{bubbles: true}}));", card_input)
            time.sleep(0.5)
        else:
            logger.warning("Could not find input field for card number.")
            return None

        # 3) تجاوز الكابتشا - تم حذف السكربت المعقد
        # بدلاً من ذلك، سنحاول فقط الانتظار قليلاً
        time.sleep(2)

        # 4) اضغط زر البحث
        search_btn = None
        try:
            search_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnSearch")))
        except:
            pass
        if not search_btn:
            try:
                search_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'بحث')]")
            except:
                pass
        if not search_btn:
            try:
                search_btn = driver.find_element(By.TAG_NAME, "button")
            except:
                pass

        if search_btn:
            # التمرير إلى الزر
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
            # استخدام execute_script للنقر
            driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(2) # انتظر رد فعل الزر
        else:
            logger.warning("Could not find search button.")
            return None

        # 5) انتظر ظهور نتائج البحث
        # انتظر حتى يظهر أحد عناصر النتيجة
        result_found = False
        for _ in range(5): # محاولة 5 مرات
            try:
                # ابحث عن اسم الموظف كمؤشر على وجود نتيجة
                name_element = driver.find_element(By.XPATH, "//strong[contains(text(), 'Name')] | //label[contains(text(), 'Name')]")
                if name_element:
                    result_found = True
                    break
            except:
                pass
            time.sleep(2)

        if not result_found:
            logger.warning(f"No results found for card {card_number}.")
            return None

        # 6) استخرج البيانات
        def get_value_page(label):
            try:
                # ابحث عن العنصر الذي يحتوي على النص المطلوب
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{label}')]")
                for el in elements:
                    # ابحث عن العنصر التالي مباشرةً (مثل span أو div)
                    try:
                        next_elem = el.find_element(By.XPATH, "./following::span[1]")
                        txt = next_elem.text.strip()
                        if txt:
                            return txt
                    except:
                        try:
                            next_elem = el.find_element(By.XPATH, "./following::div[1]")
                            txt = next_elem.text.strip()
                            if txt:
                                return txt
                        except:
                            continue
                # fallback: ابحث في نص الصفحة
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                lines = page_text.split('\n')
                for line in lines:
                    if label in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[1].strip()
                return 'Not Found'
            except Exception as e:
                logger.warning(f"Error getting value for '{label}': {e}")
                return 'Not Found'

        # اسحب القيم
        name = get_value_page('Name')
        est_name = get_value_page('Est Name')
        if est_name == 'Not Found':
            est_name = get_value_page('Est Name:')
        company_code = get_value_page('Company Code')
        designation = get_value_page('Designation')

        return {
            'Name': name if name else 'Not Found',
            'Est Name': est_name if est_name else 'Not Found',
            'Company Code': company_code if company_code else 'Not Found',
            'Designation': designation if designation else 'Not Found'
        }
    except Exception as e:
        logger.error(f"Error in deep_extract_by_card for card {card_number}: {e}")
        return None
    finally:
        try:
            driver.quit()
        except Exception:
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

                # عرض الجدول الأصلي
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
                                updated_res['Job Description'] = deep_res.get('Designation', 'Not Found')
                                updated_res['Name'] = deep_res.get('Name', 'Not Found')
                                updated_res['Est Name'] = deep_res.get('Est Name', 'Not Found')
                                updated_res['Company Code'] = deep_res.get('Company Code', 'Not Found')
                                st.session_state['single_result'] = updated_res
                                st.success(f"Deep search completed for card {card_to_search}.")
                            else:
                                st.error(f"Deep search failed for card {card_to_search}.")
                                # إضافة الحقول الفارغة
                                updated_res = st.session_state['single_result'].copy()
                                updated_res['Name'] = 'Not Found'
                                updated_res['Est Name'] = 'Not Found'
                                updated_res['Company Code'] = 'Not Found'
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
                    "Status": "Not Found"
                })

            # تحديث الجدول الحي
            elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            time_str = format_time(elapsed_seconds)
            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** `{time_str}`")
            current_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = current_df.style.map(color_status, subset=['Status'])
            live_table_area.dataframe(styled_df, use_container_width=True)

        # عند اكتمال البحث الأولي
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success(f"Batch Initial Search Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
            final_df_initial = pd.DataFrame(st.session_state.batch_results)
            # أضف أعمدة Deep Search كأعمدة فارغة إن لم تكن موجودة
            for col in ['Name', 'Est Name', 'Company Code']:
                if col not in final_df_initial.columns:
                    final_df_initial[col] = 'N/A'
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
                            designation = deep_res.get('Designation', 'Not Found')
                            st.session_state.batch_results[st.session_state.deep_current_index]['Job Description'] = designation
                            # أضف الحقول الجديدة
                            st.session_state.batch_results[st.session_state.deep_current_index]['Name'] = deep_res.get('Name', 'Not Found')
                            st.session_state.batch_results[st.session_state.deep_current_index]['Est Name'] = deep_res.get('Est Name', 'Not Found')
                            st.session_state.batch_results[st.session_state.deep_current_index]['Company Code'] = deep_res.get('Company Code', 'Not Found')
                        else:
                            # ضع حقول فارغة أو Not Found
                            st.session_state.batch_results[st.session_state.deep_current_index]['Name'] = 'Not Found'
                            st.session_state.batch_results[st.session_state.deep_current_index]['Est Name'] = 'Not Found'
                            st.session_state.batch_results[st.session_state.deep_current_index]['Company Code'] = 'Not Found'

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

# نهاية الملف
