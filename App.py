import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST (Deep Search Enabled)")

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

# --- تعديل: خيار لإظهار المتصفح (Headless = False) ---
def get_driver(show_browser=False):
    options = uc.ChromeOptions()
    if not show_browser:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized') # تكبير الشاشة عند الظهور
    
    # تمرير headless بناءً على الطلب
    return uc.Chrome(options=options, headless=not show_browser, use_subprocess=False)


def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'


# --- الموقع الأول (يبقى Headless عادةً للسرعة، إلا لو أردت تغييره) ---
def extract_data(passport, nationality, dob_str):
    # نستخدم headless=True هنا للسرعة، ويمكن تغييره لـ False للمراقبة
    driver = get_driver(show_browser=False) 
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
        time.sleep(6) # وقت انتظار لتحميل النتيجة

        def get_value(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                val = driver.find_element(By.XPATH, xpath).text.strip()
                return val if val else 'Not Found'
            except:
                return 'Not Found'

        card_num = get_value("Card Number")
        
        # إذا لم نجد رقم البطاقة، يعني فشل البحث
        if card_num == 'Not Found':
            return None

        return {
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")), # قيمة مؤقتة
            "Card Number": card_num,
            "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"),
            "Status": "Found",
            # حقول فارغة للبحث العميق
            "Name": "",
            "Est Name": "",
            "Company Code": ""
        }
    except Exception:
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


# --- الموقع الثاني (Deep Search) - تم تفعيل ظهور المتصفح ---
def deep_extract_by_card(card_number):
    # هنا نجعل show_browser=True لكي ترى المتصفح وتعرف المشكلة
    driver = get_driver(show_browser=True)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        time.sleep(3)

        # 1. اختيار الخدمة من القائمة
        try:
            btn = driver.find_element(By.ID, "dropdownButton")
            btn.click()
            time.sleep(1)
            
            # محاولة النقر على الخيار الصحيح
            found_option = False
            lis = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
            for li in lis:
                txt = li.text.lower()
                val = li.get_attribute('value')
                if 'work permit' in txt or 'electronic' in txt or val == 'EWPI':
                    li.click()
                    found_option = True
                    break
            
            if not found_option:
                # محاولة احتياطية
                if lis: lis[1].click() # نختار العنصر الثاني افتراضياً لو فشل البحث
                
        except Exception as e:
            pass

        time.sleep(1)

        # 2. إدخال رقم البطاقة
        try:
            # البحث عن أي حقل إدخال يقبل النص (عادة هو حقل البطاقة)
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            card_input = None
            for inp in inputs:
                ph = (inp.get_attribute("placeholder") or "").lower()
                nm = (inp.get_attribute("name") or "").lower()
                # استبعاد حقل الكابتشا
                if "captcha" not in nm and "verification" not in ph and "التحقق" not in ph:
                    card_input = inp
                    break
            
            if card_input:
                card_input.clear()
                card_input.send_keys(card_number)
            else:
                # إذا لم نجده، نجرب أول حقل نصي
                if inputs:
                    inputs[0].send_keys(card_number)
                    
        except Exception:
            pass

        time.sleep(1)

        # 3. محاولة حل الكابتشا تلقائياً
        try:
            js_fill_captcha = r"""
            try{
                const code=Array.from(document.querySelectorAll('div,span,b,strong'))
                    .map(el=>el.innerText.trim())
                    .find(txt=>/^\d{4}$/.test(txt));
                const input=Array.from(document.querySelectorAll('input'))
                    .find(i=>i.placeholder && (i.placeholder.includes("التحقق") || i.placeholder.toLowerCase().includes("captcha") || i.name.includes("Captcha")));
                
                if(code && input){
                    input.value = code;
                    input.dispatchEvent(new Event('input', {bubbles:true}));
                    return "Solved: " + code;
                }
            }catch(e){return "Error";}
            """
            driver.execute_script(js_fill_captcha)
        except:
            pass

        # 4. الضغط على زر البحث
        time.sleep(1)
        try:
            search_btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button")
            clicked = False
            for btn in search_btns:
                txt = btn.text.lower()
                if 'search' in txt or 'بحث' in txt:
                    btn.click()
                    clicked = True
                    break
            if not clicked and search_btns:
                # اضغط آخر زر (غالباً هو البحث)
                search_btns[-1].click()
        except:
            pass

        # 5. انتظار النتيجة واستخراج البيانات
        time.sleep(5) # امنح الصفحة وقتاً للتحميل بعد الضغط

        def get_page_text(label):
            # دالة قوية للبحث عن النص بجوار التسمية
            try:
                # محاولة XPATH مباشرة
                res = driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following::span[1]").text
                if res: return res.strip()
            except:
                pass
            
            # محاولة قراءة النص الكامل للصفحة وتقسيمه
            try:
                body_txt = driver.find_element(By.TAG_NAME, "body").text
                for line in body_txt.split('\n'):
                    if label in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[-1].strip()
            except:
                pass
            
            return 'Not Found'

        name = get_page_text('Name')
        est_name = get_page_text('Est Name')
        if est_name == 'Not Found': est_name = get_page_text('Establishment Name')
        company_code = get_page_text('Company Code')
        designation = get_page_text('Designation')

        return {
            'Name': name,
            'Est Name': est_name,
            'Company Code': company_code,
            'Designation': designation
        }

    except Exception as e:
        print(f"Error in deep search: {e}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


# --- واجهة المستخدم ---

tab1, tab2 = st.tabs(["Single Search (With Deep Search)", "Upload Excel File"])

# === تعديل قسم البحث الفردي ===
with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            status_container = st.empty()
            
            # الخطوة 1: البحث الأولي
            status_container.info("Step 1: Searching for Contract (Headless)...")
            res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
            
            if res:
                # الخطوة 2: البحث العميق إذا وجدنا رقم البطاقة
                card_num = res.get('Card Number')
                if card_num and card_num != 'Not Found':
                    status_container.info(f"Contract Found! Step 2: Deep Search for Card {card_num} (Browser will open)...")
                    
                    # استدعاء البحث العميق (سيظهر المتصفح الآن)
                    deep_res = deep_extract_by_card(card_num)
                    
                    if deep_res:
                        # تحديث البيانات
                        res['Name'] = deep_res.get('Name', 'Not Found')
                        res['Est Name'] = deep_res.get('Est Name', 'Not Found')
                        res['Company Code'] = deep_res.get('Company Code', 'Not Found')
                        # تحديث الوظيفة من الموقع الثاني كما طلبت
                        desig = deep_res.get('Designation', 'Not Found')
                        if desig != 'Not Found':
                            res['Job Description'] = desig
                    else:
                        status_container.warning("Deep Search returned no data, showing basic info only.")
                
                status_container.success("Done!")
                st.table(pd.DataFrame([res]))
            else:
                status_container.error("No data found in MOHRE system.")


# === قسم ملف الإكسل (Batch) ===
with tab2:
    st.subheader("Batch Processing Control")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records: {len(df)}")
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
            st.rerun()

        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_area = st.empty()
        live_table_area = st.empty()
        deep_status_area = st.empty()
        deep_progress_bar = st.empty()

        actual_success = 0

        # معالجة الملف (المرحلة الأولى)
        for i, row in df.iterrows():
            while st.session_state.run_state == 'paused':
                status_text.warning("Paused...")
                time.sleep(1)
            if st.session_state.run_state == 'stopped':
                break

            if i < len(st.session_state.batch_results):
                if st.session_state.batch_results[i].get("Status") == "Found":
                    actual_success += 1
                
                # عرض النتائج الحالية
                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                live_table_area.dataframe(styled_df, use_container_width=True)
                progress_bar.progress((i + 1) / len(df))
                continue

            p_num = str(row.get('Passport Number', '')).strip()
            nat = str(row.get('Nationality', 'Egypt')).strip()
            try:
                dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
            except:
                dob = str(row.get('Date of Birth', ''))

            status_text.info(f"Processing {i+1}/{len(df)}: {p_num}")
            
            # بحث المرحلة الأولى
            res = extract_data(p_num, nat, dob)

            if res:
                actual_success += 1
                st.session_state.batch_results.append(res)
            else:
                st.session_state.batch_results.append({
                    "Passport Number": p_num, "Nationality": nat, "Date of Birth": dob,
                    "Status": "Not Found", "Card Number": "N/A"
                })

            elapsed = time.time() - (st.session_state.start_time_ref or time.time())
            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ Found: {actual_success} | ⏱️ Time: `{format_time(elapsed)}`")

            current_df = pd.DataFrame(st.session_state.batch_results)
            styled_df = current_df.style.map(color_status, subset=['Status'])
            live_table_area.dataframe(styled_df, use_container_width=True)

        # زر البحث العميق للملف الكامل
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success("Batch Phase 1 Completed.")
            
            # تحضير الملف للتحميل
            final_df = pd.DataFrame(st.session_state.batch_results)
            st.download_button("Download Report (Phase 1)", final_df.to_csv(index=False).encode('utf-8'), "phase1_results.csv")

            if st.button("Start Deep Search (Browser Visible)"):
                st.session_state.deep_run_state = 'running'

            if st.session_state.deep_run_state == 'running':
                deep_candidates = [
                    (idx, r) for idx, r in enumerate(st.session_state.batch_results) 
                    if r.get('Status') == 'Found' and r.get('Card Number') not in [None, 'N/A', 'Not Found']
                ]
                
                deep_total = len(deep_candidates)
                deep_progress_bar = st.progress(0)
                
                for step, (idx, rec) in enumerate(deep_candidates):
                    if st.session_state.deep_run_state != 'running': break
                    
                    card = rec.get('Card Number')
                    deep_status_area.info(f"Deep Search {step+1}/{deep_total}: {card}")
                    
                    # استدعاء دالة البحث العميق (المتصفح سيظهر)
                    deep_res = deep_extract_by_card(card)
                    
                    if deep_res:
                        st.session_state.batch_results[idx].update(deep_res)
                        # تحديث الوصف الوظيفي
                        if deep_res.get('Designation') != 'Not Found':
                            st.session_state.batch_results[idx]['Job Description'] = deep_res.get('Designation')
                    else:
                        st.session_state.batch_results[idx]['Name'] = 'Not Found'

                    deep_progress_bar.progress((step + 1) / deep_total)
                    
                    # تحديث الجدول الحي
                    current_df = pd.DataFrame(st.session_state.batch_results)
                    styled_df = current_df.style.map(color_status, subset=['Status'])
                    live_table_area.dataframe(styled_df, use_container_width=True)

                st.success("Deep Search Completed!")
                final_df_deep = pd.DataFrame(st.session_state.batch_results)
                st.download_button("Download Final Report", final_df_deep.to_csv(index=False).encode('utf-8'), "final_complete_results.csv")
                st.session_state.deep_run_state = 'stopped'
