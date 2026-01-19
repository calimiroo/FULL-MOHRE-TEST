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
st.title("HAMADA TRACING SITE TEST (Smart Interactive)")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None  # لتخزين نتيجة البحث الفردي

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

# --- دالة الترجمة ---
def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

# --- إعداد المتصفح ---
# هام: إذا كنت تشغل الكود على سيرفر streamlit cloud، يجب أن يكون headless=True دائماً
def get_driver(show_browser=False):
    options = uc.ChromeOptions()
    if not show_browser:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    return uc.Chrome(options=options, headless=not show_browser, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- البحث الأول (المرحلة 1) ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver(show_browser=False) # نجعله مخفي للسرعة في المرحلة الأولى
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        time.sleep(3)
        
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
        time.sleep(5)

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

        # تجهيز النتيجة
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
            "Name": "", # فارغ حالياً
            "Est Name": "",
            "Company Code": ""
        }
    except Exception:
        return None
    finally:
        try: driver.quit()
        except: pass

# --- البحث العميق (المرحلة 2) ---
def deep_extract_by_card(card_number):
    # هنا نجعل show_browser=True إذا كنت تعمل على Localhost لكي ترى المتصفح
    # إذا كنت على Streamlit Cloud سيتم تجاهل الظهور وتعمل في الخلفية لتجنب الاخطاء
    driver = get_driver(show_browser=True) 
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        time.sleep(3)

        # 1. اختيار الخدمة
        try:
            btn = driver.find_element(By.ID, "dropdownButton")
            btn.click()
            time.sleep(1)
            lis = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
            for li in lis:
                if 'EWPI' in li.get_attribute('value') or 'Work Permit' in li.text:
                    li.click()
                    break
        except: pass
        time.sleep(1)

        # 2. إدخال البطاقة
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for inp in inputs:
                if "captcha" not in (inp.get_attribute("name") or "").lower():
                    inp.clear()
                    inp.send_keys(card_number)
                    break
        except: pass
        time.sleep(1)

        # 3. حل الكابتشا (Script)
        try:
            js_fill = "try{const c=[...document.querySelectorAll('div,span,b')].find(e=>/^\\d{4}$/.test(e.innerText.trim()));const i=[...document.querySelectorAll('input')].find(e=>e.placeholder&&e.placeholder.includes('التحقق'));if(c&&i){i.value=c.innerText.trim();i.dispatchEvent(new Event('input',{bubbles:true}));}}catch(e){}"
            driver.execute_script(js_fill)
        except: pass

        # 4. بحث
        time.sleep(1)
        try:
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except: pass
        
        time.sleep(5) # انتظار النتيجة

        # 5. استخراج البيانات
        def get_txt(lbl):
            try:
                return driver.find_element(By.XPATH, f"//*[contains(text(), '{lbl}')]/following::span[1]").text.strip()
            except:
                return 'Not Found'

        return {
            'Name': get_txt('Name'),
            'Est Name': get_txt('Est Name') if get_txt('Est Name') != 'Not Found' else get_txt('Establishment Name'),
            'Company Code': get_txt('Company Code'),
            'Designation': get_txt('Designation')
        }
    except Exception as e:
        return None
    finally:
        try: driver.quit()
        except: pass

# --- واجهة المستخدم ---

tab1, tab2 = st.tabs(["Single Search", "Batch Upload"])

with tab1:
    st.subheader("Single Person Search")
    c1, c2, c3 = st.columns(3)
    p_in = c1.text_input("Passport Number", key="s_p")
    n_in = c2.selectbox("Nationality", countries_list, key="s_n")
    d_in = c3.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    # زر البحث الرئيسي
    if st.button("Search Now", type="primary"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Searching Phase 1..."):
                res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                if res:
                    st.session_state['single_result'] = res
                    st.success("Contract Found!")
                else:
                    st.session_state['single_result'] = None
                    st.error("No data found.")
    
    # عرض النتيجة والتحكم في البحث العميق
    if st.session_state['single_result']:
        res = st.session_state['single_result']
        
        # عرض الجدول فوراً
        st.write("### Result:")
        df_show = pd.DataFrame([res])
        st.table(df_show)

        # التحقق من وجود رقم بطاقة لتفعيل الزر
        card_num = res.get('Card Number')
        if card_num and card_num != 'Not Found':
            st.markdown("---")
            st.info("💡 **Deep Search Available:** Click the card number below to fetch Name & Company details.")
            
            # زر يظهر كأنه رقم البطاقة
            col_btn, col_msg = st.columns([1, 4])
            # إذا ضغط المستخدم على هذا الزر، نقوم بالبحث العميق
            if col_btn.button(f"🔍 Deep Search Card: {card_num}"):
                with st.spinner(f"Opening browser to search card {card_num}..."):
                    deep_res = deep_extract_by_card(card_num)
                    
                    if deep_res:
                        # تحديث البيانات في الذاكرة
                        st.session_state['single_result']['Name'] = deep_res.get('Name')
                        st.session_state['single_result']['Est Name'] = deep_res.get('Est Name')
                        st.session_state['single_result']['Company Code'] = deep_res.get('Company Code')
                        if deep_res.get('Designation') != 'Not Found':
                             st.session_state['single_result']['Job Description'] = deep_res.get('Designation')
                        
                        st.success("Deep Search Completed! Table Updated.")
                        time.sleep(1)
                        st.rerun() # إعادة تحميل الصفحة لعرض الجدول المحدث
                    else:
                        st.error("Deep search failed or captcha issue.")

# (تم اختصار كود Batch Tab لأنه لم يتغير وللتركيز على طلبك)
with tab2:
    st.info("Batch search functionality remains here (same as previous code).")
