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
import json # مطلوب لـ postMessage

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
    except Exception:
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
        wait = WebDriverWait(driver, 10)

        # 1) اختر "Electronic Work Permit Information" باستخدام القيمة
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
        dropdown_btn.click()
        time.sleep(0.5)
        # انتظر حتى تصبح القائمة مرئية
        wait.until(EC.presence_of_element_located((By.ID, "dropdownList")))

        # ابحث عن العنصر باستخدام القيمة 'EWPI'
        ewpi_option = driver.find_element(By.CSS_SELECTOR, f"li[value='EWPI']")
        ewpi_option.click()
        time.sleep(1)

        # 2) أدخل رقم البطاقة
        card_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        card_input.clear()
        card_input.send_keys(card_number)
        time.sleep(0.5)

        # 3) تجاوز الكابتشا باستخدام السكربت
        js_fill_captcha = r"""
        try{
            const tryFill=()=>{
                const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));
                const input=Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"));
                if(code&&input){
                    input.value=code;
                    input.dispatchEvent(new Event('input',{bubbles:true}));
                }
                else{
                    setTimeout(tryFill,500);
                }
            };
            tryFill();
        }catch(e){
            console.error('Error filling captcha:',e);
        }
        """
        driver.execute_script(js_fill_captcha)
        time.sleep(1)

        # 4) اضغط زر البحث
        search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], button, #btnSearch, #searchBtn, input[type='submit']")))
        search_btn.click()

        # 5) انتظر النتائج
        # انتظر حتى يظهر محتوى الصفحة بعد البحث
        wait.until(lambda d: "Name" in d.page_source or "Card Number" in d.page_source)

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
            except:
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
        print(f"Error in deep_extract_by_card for card {card_number}: {e}")
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
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res:
                    st.session_state['single_result'] = res
                    st.session_state['deep_single_running'] = False
                    st.session_state['deep_single_card'] = None
                    st.session_state['deep_single_result'] = {}
                else:
                    st.error("No data found.")
                    st.session_state['single_result'] = None

    # عرض نتيجة البحث الفردي
    if st.session_state['single_result']:
        result_df = pd.DataFrame([st.session_state['single_result']])
        
        # إذا كانت النتيجة تحتوي على Card Number، عرضها كجدول قابل للتحديث
        if st.session_state['single_result']['Card Number'] != 'N/A':
            # إنشاء رابط وهمي لرقم البطاقة
            card_num_display = st.session_state['single_result']['Card Number']
            # استخدم HTML لعرض الرابط
            card_link_html = f'<a href="#" id="card_link_{card_num_display}" style="color: blue; text-decoration: underline;">{card_num_display}</a>'
            display_df = result_df.copy()
            display_df.loc[0, 'Card Number'] = card_link_html
            
            # عرض الجدول مع الرابط
            st.dataframe(display_df, unsafe_allow_html=True, use_container_width=True)
            
            # إضافة HTML وJavaScript للتعامل مع النقر على الرابط
            js_code = f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                var link = document.getElementById('card_link_{card_num_display}');
                if(link) {{
                    link.onclick = function(e) {{
                        e.preventDefault(); // منع الانتقال إلى رابط فارغ
                        window.parent.postMessage({{
                            type: 'deep_search_single',
                            card_number: '{card_num_display}'
                        }}, '*');
                        return false;
                    }};
                }}
            }});
            </script>
            """
            st.components.v1.html(js_code, height=0)
            
            # التحقق من النقر على الرابط (من خلال postMessage)
            query_params = st.experimental_get_query_params()
            if 'trigger_deep_search' in query_params:
                 card_clicked = query_params['trigger_deep_search'][0]
                 if card_clicked == card_num_display and not st.session_state['deep_single_running']:
                     st.session_state['deep_single_running'] = True
                     st.session_state['deep_single_card'] = card_clicked
                     st.experimental_set_query_params() # مسح الرابط من عنوان URL
                     st.rerun()
            
            # التحقق من النقر من خلال postMessage
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
                st.download_button(
                    label="Download Single Result (CSV)",
                    data=updated_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"single_result_{st.session_state['single_result']['Card Number']}.csv",
                    mime='text/csv'
                )
        else:
            # إذا لم يكن هناك Card Number، عرض النتيجة العادية
            st.dataframe(result_df, use_container_width=True)

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
            st.download_button(
                "Download Initial Batch Results (CSV)",
                final_df_initial.to_csv(index=False).encode('utf-8'),
                "initial_batch_results.csv",
                mime='text/csv'
            )

            # زر البحث العميق
            if st.button("Deep Search (Search cards on inquiry.mohre.gov.ae)") and st.session_state.deep_run_state != 'running':
                st.session_state.deep_run_state = 'running'
                st.session_state.deep_current_index = 0

            # تنفيذ البحث العميق إذا بدأ
            if st.session_state.deep_run_state == 'running':
                deep_total = sum(1 for r in st.session_state.batch_results if r.get('Status') == 'Found' and r.get('Card Number') not in [None, 'N/A', 'Not Found', ''])
                if deep_total == 0:
                    st.info("No 'Found' records with valid Card Number to Deep Search.")
                    st.session_state.deep_run_state = 'stopped'
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
                        
                        # زر تحميل الملف النهائي بعد الـ Deep Search
                        final_df = pd.DataFrame(st.session_state.batch_results)
                        st.download_button(
                            "Download Final Full Report (CSV)",
                            final_df.to_csv(index=False).encode('utf-8'),
                            "full_results_with_deep.csv",
                            mime='text/csv'
                        )

# نهاية الملف
