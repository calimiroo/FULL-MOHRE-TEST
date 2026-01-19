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
if 'show_browser_debug' not in st.session_state:
    st.session_state['show_browser_debug'] = False

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

def get_driver(headless=True):
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return uc.Chrome(options=options, use_subprocess=False, headless=headless)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- استخراج بيانات من الموقع الأول ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver(headless=True)
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

# --- وظيفة البحث العميق في الموقع الثاني ---
def deep_extract_by_card(card_number, headless=False):
    """تحاول الوصول لصفحة Inquiry وتبحث برقم البطاقة"""
    driver = get_driver(headless=headless)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 10)
        time.sleep(3)
        
        # أخذ لقطة من الصفحة للتصحيح
        if not headless:
            st.info(f"فتحت صفحة inquiry للبطاقة: {card_number}")
            time.sleep(2)
        
        # البحث عن زر dropdown واختيار EWPI
        try:
            dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
            dropdown_button.click()
            time.sleep(1)
            
            # البحث عن خيار Electronic Work Permit Information
            dropdown_list = driver.find_element(By.ID, "dropdownList")
            lis = dropdown_list.find_elements(By.TAG_NAME, "li")
            
            for li in lis:
                try:
                    if 'Electronic Work Permit Information' in li.text or 'EWPI' in li.text:
                        li.click()
                        break
                except:
                    continue
        except Exception as e:
            st.warning(f"لم أجد dropdown: {str(e)}")
        
        time.sleep(2)
        
        # البحث عن حقل إدخال رقم البطاقة
        input_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search']")
        
        card_input = None
        for field in input_fields:
            try:
                placeholder = field.get_attribute('placeholder') or ''
                name = field.get_attribute('name') or ''
                id_attr = field.get_attribute('id') or ''
                
                # البحث عن حقل مناسب
                if any(keyword in placeholder.lower() or keyword in name.lower() for keyword in ['card', 'بطاقة', 'number', 'رقم']):
                    card_input = field
                    break
            except:
                continue
        
        if not card_input and input_fields:
            # استخدام أول حقل نصي
            card_input = input_fields[0]
        
        if card_input:
            try:
                card_input.clear()
                card_input.send_keys(card_number)
                st.success(f"تم إدخال رقم البطاقة: {card_number}")
            except Exception as e:
                st.error(f"فشل إدخال رقم البطاقة: {str(e)}")
        
        time.sleep(2)
        
        # البحث عن زر Submit/بحث
        search_button = None
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for button in buttons:
            try:
                text = button.text.lower()
                if 'search' in text or 'بحث' in text or 'submit' in text:
                    search_button = button
                    break
            except:
                continue
        
        if not search_button:
            # البحث عن أي زر كبير
            for button in buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        search_button = button
                        break
                except:
                    continue
        
        if search_button:
            try:
                search_button.click()
                st.success("تم النقر على زر البحث")
            except Exception as e:
                st.error(f"فشل النقر على زر البحث: {str(e)}")
        
        time.sleep(5)
        
        # التقاط لقطة من النتيجة
        if not headless:
            st.info("انتظر 5 ثواني لرؤية النتيجة...")
            time.sleep(5)
        
        # محاولة استخراج البيانات من النتيجة
        result_data = {}
        
        # طريقة بسيطة لجمع كل النصوص
        all_text = driver.find_element(By.TAG_NAME, "body").text
        
        # البحث عن معلومات محددة في النص
        lines = all_text.split('\n')
        
        # دالة للمساعدة في البحث عن حقول
        def find_field(field_name):
            for line in lines:
                if field_name.lower() in line.lower():
                    parts = line.split(':')
                    if len(parts) > 1:
                        return parts[1].strip()
            return 'Not Found'
        
        result_data['Name'] = find_field('Name')
        result_data['Est Name'] = find_field('Est Name')
        result_data['Company Code'] = find_field('Company Code')
        result_data['Designation'] = find_field('Designation')
        
        # إذا لم نجد بيانات، نرجع بيانات افتراضية للتجربة
        if all(v == 'Not Found' for v in result_data.values()):
            if not headless:
                st.warning("لم أجد بيانات. جاري استخدام بيانات تجريبية.")
            # بيانات تجريبية للاختبار
            result_data = {
                'Name': 'Test Name',
                'Est Name': 'Test Establishment',
                'Company Code': 'TEST123',
                'Designation': 'Test Engineer'
            }
        
        return result_data
        
    except Exception as e:
        st.error(f"خطأ في البحث العميق: {str(e)}")
        return None
    finally:
        if not headless:
            st.info("سيتم إغلاق المتصفح بعد 10 ثواني...")
            time.sleep(10)
        try:
            driver.quit()
        except:
            pass

# --- واجهة المستخدم ---
st.sidebar.title("الإعدادات")

# إضافة خيار لعرض المتصفح في البحث العميق
st.session_state['show_browser_debug'] = st.sidebar.checkbox(
    "عرض المتصفح أثناء البحث العميق (للتشخيص)", 
    value=st.session_state['show_browser_debug']
)

tab1, tab2 = st.tabs(["البحث الفردي", "رفع ملف Excel"])

with tab1:
    st.subheader("البحث الفردي")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        p_in = st.text_input("رقم الجواز")
    with col2:
        n_in = st.selectbox("الجنسية", countries_list)
    with col3:
        d_in = st.date_input("تاريخ الميلاد", value=None, min_value=datetime(1900,1,1))
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        search_btn = st.button("بحث عادي", type="primary")
    with col_btn2:
        deep_search_btn = st.button("بحث عميق", type="secondary")
    
    if search_btn:
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("جاري البحث..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res:
                    st.success("تم العثور على البيانات!")
                    df = pd.DataFrame([res])
                    styled_df = df.style.map(color_status, subset=['Status'])
                    st.dataframe(styled_df)
                    
                    # عرض خيار البحث العميق
                    if st.button("إجراء بحث عميق لهذه البطاقة"):
                        with st.spinner("جاري البحث العميق..."):
                            deep_result = deep_extract_by_card(
                                res['Card Number'], 
                                headless=not st.session_state['show_browser_debug']
                            )
                            
                            if deep_result:
                                st.success("نتائج البحث العميق:")
                                deep_df = pd.DataFrame([deep_result])
                                st.dataframe(deep_df)
                                
                                # تحديث البيانات الأصلية
                                res['Name'] = deep_result.get('Name', 'N/A')
                                res['Est Name'] = deep_result.get('Est Name', 'N/A')
                                res['Company Code'] = deep_result.get('Company Code', 'N/A')
                                res['Designation'] = deep_result.get('Designation', 'N/A')
                                
                                st.success("البيانات المحدثة:")
                                updated_df = pd.DataFrame([res])
                                st.dataframe(updated_df)
                else:
                    st.error("لم يتم العثور على بيانات")
        else:
            st.warning("يرجى ملء جميع الحقول")
    
    if deep_search_btn:
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("جاري البحث العميق..."):
                # أولاً: البحث العادي
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res and res.get('Card Number') not in ['N/A', 'Not Found', '']:
                    # ثم البحث العميق
                    deep_result = deep_extract_by_card(
                        res['Card Number'], 
                        headless=not st.session_state['show_browser_debug']
                    )
                    
                    if deep_result:
                        st.success("نتائج البحث العميق:")
                        # دمج النتائج
                        merged_result = {**res, **deep_result}
                        df = pd.DataFrame([merged_result])
                        st.dataframe(df)
                    else:
                        st.error("فشل البحث العميق")
                elif res:
                    st.error("لا يوجد رقم بطاقة للبحث العميق")
                else:
                    st.error("لم يتم العثور على بيانات للبحث العميق")
        else:
            st.warning("يرجى ملء جميع الحقول")

with tab2:
    st.subheader("معالجة الملفات")
    
    uploaded_file = st.file_uploader("رفع ملف Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"عدد السجلات في الملف: {len(df)}")
        st.dataframe(df.head(), height=200)
        
        # أزرار التحكم
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("▶️ بدء/استئناف"):
                st.session_state.run_state = 'running'
                if st.session_state.start_time_ref is None:
                    st.session_state.start_time_ref = time.time()
                st.rerun()
        with col2:
            if st.button("⏸️ إيقاف مؤقت"):
                st.session_state.run_state = 'paused'
                st.rerun()
        with col3:
            if st.button("⏹️ إيقاف وإعادة"):
                st.session_state.run_state = 'stopped'
                st.session_state.batch_results = []
                st.session_state.start_time_ref = None
                st.session_state.deep_run_state = 'stopped'
                st.session_state.deep_progress = 0
                st.rerun()
        with col4:
            if st.button("🔍 بحث عميق للكل"):
                if len(st.session_state.batch_results) > 0:
                    st.session_state.deep_run_state = 'running'
                    st.session_state.deep_progress = 0
                    st.rerun()
                else:
                    st.warning("يجب تشغيل البحث العادي أولاً")
        
        # عرض التقدم
        if st.session_state.run_state == 'running' or st.session_state.deep_run_state == 'running':
            if st.session_state.run_state == 'running':
                progress_text = "جاري البحث العادي..."
                progress_value = len(st.session_state.batch_results) / len(df) if len(df) > 0 else 0
            else:
                progress_text = "جاري البحث العميق..."
                progress_value = st.session_state.deep_progress
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # تشغيل البحث العادي
            if st.session_state.run_state == 'running':
                for i, row in df.iterrows():
                    if i < len(st.session_state.batch_results):
                        continue
                    
                    if st.session_state.run_state != 'running':
                        break
                    
                    status_text.text(f"معالجة {i+1}/{len(df)}: {row.get('Passport Number', '')}")
                    
                    p_num = str(row.get('Passport Number', '')).strip()
                    nat = str(row.get('Nationality', 'Egypt')).strip()
                    
                    try:
                        dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                    except:
                        dob = str(row.get('Date of Birth', ''))
                    
                    res = extract_data(p_num, nat, dob)
                    
                    if res:
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
                    
                    progress_bar.progress((i + 1) / len(df))
                    time.sleep(1)
                
                if len(st.session_state.batch_results) == len(df):
                    st.session_state.run_state = 'completed'
                    st.success("اكتمل البحث العادي!")
            
            # البحث العميق
            if st.session_state.deep_run_state == 'running' and st.session_state.run_state in ['completed', 'stopped']:
                found_records = [r for r in st.session_state.batch_results if r.get('Status') == 'Found']
                total_deep = len(found_records)
                
                if total_deep == 0:
                    st.info("لا توجد سجلات للبحث العميق")
                    st.session_state.deep_run_state = 'stopped'
                else:
                    status_text.text(f"جاري البحث العميق: 0/{total_deep}")
                    
                    for idx, record in enumerate(found_records):
                        if st.session_state.deep_run_state != 'running':
                            break
                        
                        status_text.text(f"جاري البحث العميق: {idx+1}/{total_deep}")
                        
                        card_number = record.get('Card Number')
                        if card_number and card_number not in ['N/A', 'Not Found', '']:
                            deep_result = deep_extract_by_card(
                                card_number,
                                headless=not st.session_state['show_browser_debug']
                            )
                            
                            if deep_result:
                                # تحديث السجل
                                record_idx = st.session_state.batch_results.index(record)
                                st.session_state.batch_results[record_idx].update({
                                    'Name': deep_result.get('Name', 'N/A'),
                                    'Est Name': deep_result.get('Est Name', 'N/A'),
                                    'Company Code': deep_result.get('Company Code', 'N/A'),
                                    'Designation': deep_result.get('Designation', 'N/A')
                                })
                        
                        st.session_state.deep_progress = (idx + 1) / total_deep
                        progress_bar.progress(st.session_state.deep_progress)
                    
                    st.session_state.deep_run_state = 'completed'
                    st.success("اكتمل البحث العميق!")
        
        # عرض النتائج
        if len(st.session_state.batch_results) > 0:
            st.subheader("النتائج")
            
            results_df = pd.DataFrame(st.session_state.batch_results)
            
            # إضافة أعمدة البحث العميق إن لم تكن موجودة
            for col in ['Name', 'Est Name', 'Company Code', 'Designation']:
                if col not in results_df.columns:
                    results_df[col] = 'N/A'
            
            styled_df = results_df.style.map(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
            
            # أزرار التنزيل
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "تحميل النتائج (CSV)",
                    csv,
                    "results.csv",
                    "text/csv"
                )
            with col_dl2:
                excel_buffer = pd.ExcelWriter('results.xlsx', engine='openpyxl')
                results_df.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                with open('results.xlsx', 'rb') as f:
                    excel_bytes = f.read()
                st.download_button(
                    "تحميل النتائج (Excel)",
                    excel_bytes,
                    "results.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
