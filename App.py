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

# --- وظائف الاستخراج والترجمة (مثل الكود الأصلي مع بعض التحسينات الطفيفة) ---
def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text


def get_driver():
    options = uc.ChromeOptions()
    # احرص على الحفاظ على الخيارات كما هي
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)


def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'


# --- استخراج بيانات من الموقع الأول (الموجود في كودك الأصلي) ---
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
            # ملاحظة: بعد Deep Search سنستبدل Job Description بقيمة Designation من الموقع الثاني
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
# تبحث فقط للأشخاص اللي طلع لهم "Found" في البحث الأول

def deep_extract_by_card(card_number):
    """تحاول الوصول لصفحة Inquiry وتبحث برقم البطاقة وتستخرج Name, Est Name, Company Code, Designation"""
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 10)
        time.sleep(2)

        # 1) افتح الدروب داون واختر EWPI أو "Electronic Work Permit Information"
        try:
            # حاول الضغط على البوتون الذي يظهر القيم ثم العثور على العنصر المناسب
            btn = driver.find_element(By.ID, "dropdownButton")
            btn.click()
            time.sleep(0.5)
            # حاول إيجاد العنصر بواسطة value أو النص
            lis = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
            picked = False
            for li in lis:
                try:
                    if 'Electronic Work Permit Information' in li.text or li.get_attribute('value') == 'EWPI':
                        li.click()
                        picked = True
                        break
                except:
                    continue
            if not picked:
                # حاول اختيار عن طريق البحث في النصوص
                for li in lis:
                    if 'Work Permit' in li.text:
                        li.click()
                        break
        except Exception:
            pass

        time.sleep(1)

        # 2) أدخل رقم البطاقة في حقل النص المناسب (نجرب عدد من السليكتورات الشائعة)
        possible_inputs = []
        try:
            possible_inputs.extend(driver.find_elements(By.CSS_SELECTOR, "input[type='text']"))
        except:
            pass
        card_input = None
        for inp in possible_inputs:
            try:
                ph = inp.get_attribute('placeholder') or ''
                name = inp.get_attribute('name') or ''
                if 'card' in name.lower() or 'card' in ph.lower() or 'work permit' in ph.lower() or 'permit' in ph.lower() or 'التحقق' not in ph:
                    card_input = inp
                    break
            except:
                continue
        if card_input is None and possible_inputs:
            card_input = possible_inputs[0]

        if card_input is not None:
            try:
                card_input.clear()
                card_input.send_keys(card_number)
            except Exception:
                pass

        time.sleep(0.5)

        # 3) محاولة تجاوز/ملء الكابتشا باستخدام السكربت المقدم (ندمج محتواه هنا)
        try:
            js_fill_captcha = r"""
            try{
                const tryFill=()=>{
                    const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));
                    const input=Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"));
                    if(code&&input){input.value=code;input.dispatchEvent(new Event('input',{bubbles:true}));}
                    else{setTimeout(tryFill,500);} };
                tryFill();
            }catch(e){console.error('Error:',e);}            
            """
            # ننفذ السكربت في صفحة الموزع
            driver.execute_script(js_fill_captcha)
        except Exception:
            pass

        time.sleep(1)

        # 4) اضغط زر البحث (نجرب سيلكتورات متعددة)
        clicked_search = False
        search_selectors = ["button[type='submit']", "button", "#btnSearch", "#searchBtn", "input[type='submit']"]
        for sel in search_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    txt = (e.text or '').strip().lower()
                    if txt in ['', 'search', 'بحث', 'view details', 'view'] or 'search' in txt or 'بحث' in txt or e.get_attribute('type')=='submit':
                        try:
                            e.click()
                            clicked_search = True
                            break
                        except:
                            continue
                if clicked_search:
                    break
            except:
                continue

        # كخيار احتياطي: محاولة الضغط على أي زر كبير ظاهر
        if not clicked_search:
            try:
                big_btns = driver.find_elements(By.TAG_NAME, 'button')
                for b in big_btns:
                    try:
                        if b.is_displayed():
                            b.click()
                            clicked_search = True
                            break
                    except:
                        continue
            except:
                pass

        # 5) انتظر النتائج
        time.sleep(4)

        def get_value_page(label):
            try:
                xpath = f"//strong[contains(text(), '{label}')]/following::text()[1] | //label[contains(text(), '{label}')]/following-sibling::div | //span[contains(text(), '{label}')]/following::span[1]"
                # نقوم بمحاولة جلب النص عبر طرق بسيطة
                elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{label}')]")
                for el in elems:
                    try:
                        # الحصول على العنصر التالي النصي أو العنصر التالي
                        nxt = el.find_element(By.XPATH, './following::span[1]')
                        txt = nxt.text.strip()
                        if txt:
                            return txt
                    except:
                        continue
                # fallback: البحث عن عناصر داخل الصفحة
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                # محاولة استخراج سطور قريبة من الكلمة
                for line in page_text.split('\n'):
                    if label in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[1].strip()
                return 'Not Found'
            except:
                return 'Not Found'

        # نسحب القيم المتوقعة
        name = get_value_page('Name')
        est_name = get_value_page('Est Name')
        if est_name == 'Not Found':
            est_name = get_value_page('Est Name:')
            if est_name == 'Not Found':
                est_name = get_value_page('Est Name'.strip())
        company_code = get_value_page('Company Code')
        designation = get_value_page('Designation')

        # تنسيق النتيجة
        return {
            'Name': name if name else 'Not Found',
            'Est Name': est_name if est_name else 'Not Found',
            'Company Code': company_code if company_code else 'Not Found',
            'Designation': designation if designation else 'Not Found'
        }
    except Exception as e:
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
                    st.table(pd.DataFrame([res]))
                else:
                    st.error("No data found.")

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

        # مساحات العرض الحية: نعرض جدول النتائج الأولي دائمًا
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

            # تخطي ما تمت معالجته
            if i < len(st.session_state.batch_results):
                if st.session_state.batch_results[i].get("Status") == "Found":
                    actual_success += 1
                # عرض الجدول الحالي
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

            # حساب الوقت الكلي بصيغة ساعات:دقائق:ثواني
            elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
            time_str = format_time(elapsed_seconds)

            progress_bar.progress((i + 1) / len(df))
            stats_area.markdown(f"✅ **Actual Success (Found):** {actual_success} | ⏱️ **Total Time:** `{time_str}`")

            current_df = pd.DataFrame(st.session_state.batch_results)
            # نعرض الجدول الأولي هنا دائمًا (حتى أثناء الـ Deep Search)
            styled_df = current_df.style.map(color_status, subset=['Status'])
            live_table_area.dataframe(styled_df, use_container_width=True)

        # عند اكتمال الـ batch الأولي
        if st.session_state.run_state == 'running' and len(st.session_state.batch_results) == len(df):
            st.success(f"Batch Completed! Total Time: {format_time(time.time() - st.session_state.start_time_ref)}")
            final_df = pd.DataFrame(st.session_state.batch_results)
            # أضف أعمدة Deep Search كأعمدة فارغة إن لم تكن موجودة
            for col in ['Name', 'Est Name', 'Company Code']:
                if col not in final_df.columns:
                    final_df[col] = ''
            # زر تحميل أولي
            st.download_button("Download Full Report (CSV)", final_df.to_csv(index=False).encode('utf-8'), "full_results.csv")

            # زر البحث العميق - يظهر بعد اكتمال الـ batch
            if st.button("Deep Search (Search cards on inquiry.mohre.gov.ae)"):
                st.session_state.deep_run_state = 'running'
                st.session_state.deep_progress = 0

            # تنفيذ البحث العميق إذا بدأ
            if st.session_state.deep_run_state == 'running':
                deep_total = sum(1 for r in st.session_state.batch_results if r.get('Status') == 'Found' and r.get('Card Number') not in [None, 'N/A', 'Not Found', ''])
                if deep_total == 0:
                    st.info("No 'Found' records with valid Card Number to Deep Search.")
                    st.session_state.deep_run_state = 'stopped'
                else:
                    deep_idx = 0
                    deep_success = 0
                    deep_progress_bar = st.progress(0)
                    deep_status_area.info("Starting Deep Search for Found records...")
                    # نمر على كل نتائج الباتش ونبحث فقط عن Found
                    for idx, rec in enumerate(st.session_state.batch_results):
                        if st.session_state.deep_run_state != 'running':
                            break
                        if rec.get('Status') != 'Found':
                            continue
                        card = rec.get('Card Number')
                        if not card or card in ['N/A', 'Not Found']:
                            continue

                        deep_status_area.info(f"Deep Searching {deep_idx+1}/{deep_total}: {card}")
                        # نفذ البحث العميق
                        deep_res = deep_extract_by_card(card)
                        if deep_res:
                            deep_success += 1
                            # استبدل Job Description بقيمة Designation كما طلبت
                            designation = deep_res.get('Designation', 'Not Found')
                            st.session_state.batch_results[idx]['Job Description'] = designation
                            # أضف الحقول الجديدة
                            st.session_state.batch_results[idx]['Name'] = deep_res.get('Name', '')
                            st.session_state.batch_results[idx]['Est Name'] = deep_res.get('Est Name', '')
                            st.session_state.batch_results[idx]['Company Code'] = deep_res.get('Company Code', '')
                        else:
                            # ضع حقول فارغة أو Not Found
                            st.session_state.batch_results[idx]['Name'] = 'Not Found'
                            st.session_state.batch_results[idx]['Est Name'] = 'Not Found'
                            st.session_state.batch_results[idx]['Company Code'] = 'Not Found'

                        deep_idx += 1
                        st.session_state.deep_progress = deep_idx / deep_total
                        deep_progress_bar.progress(min(1.0, st.session_state.deep_progress))

                        # حدث عرض الجدول الأولي مباشرةً (لا يختفي)
                        current_df = pd.DataFrame(st.session_state.batch_results)
                        styled_df = current_df.style.map(color_status, subset=['Status'])
                        live_table_area.dataframe(styled_df, use_container_width=True)

                    st.success(f"Deep Search Completed: {deep_success}/{deep_total} succeeded")
                    # زر تحميل الملف النهائي بعد الـ Deep Search
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    st.download_button("Download Final Full Report (CSV)", final_df.to_csv(index=False).encode('utf-8'), "full_results_with_deep.csv")
                    st.session_state.deep_run_state = 'stopped'


# نهاية الملف
