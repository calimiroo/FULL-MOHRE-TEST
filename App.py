import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from deep_translator import GoogleTranslator

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="MOHRE Portal Professional", layout="wide")
st.title("MOHRE DATA TRACING SYSTEM")

# --- 2. إدارة حالة الجلسة (Session State) لضمان استقرار البيانات ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'data_result' not in st.session_state:
    st.session_state['data_result'] = None

# قائمة الجنسيات الكاملة
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- 3. نظام حماية الدخول ---
if not st.session_state['authenticated']:
    with st.form("login_form"):
        st.subheader("🔒 نظام الوصول المحمي")
        pwd_input = st.text_input("أدخل كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if pwd_input == "Bilkish":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("كلمة المرور خاطئة!")
    st.stop()

# --- 4. الوظائف المساعدة ---
def get_driver():
    """إعداد متصفح Chrome للعمل في وضع السيرفر (Headless)"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def translate_text(text):
    """ترجمة النصوص من العربية للإنجليزية"""
    try:
        if text and text not in ['Not Found', '']:
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

# --- 5. منطق البحث الأول (التعاقد) ---
def first_stage_search(passport, nationality, dob):
    driver = get_driver()
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
        wait = WebDriverWait(driver, 10)
        
        # إدخال البيانات
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        driver.find_element(By.ID, "CtrlNationality_txtDescription").click()
        time.sleep(1)
        
        # البحث عن الجنسية في القائمة المنسدلة
        search_box = driver.find_element(By.CSS_SELECTOR, "#ajaxSearchBoxModal .form-control")
        search_box.send_keys(nationality)
        time.sleep(1)
        items = driver.find_elements(By.CSS_SELECTOR, "#ajaxSearchBoxModal .items li a")
        if items: items[0].click()

        # إدخال تاريخ الميلاد
        dob_input = driver.find_element(By.ID, "txtBirthDate")
        driver.execute_script("arguments[0].removeAttribute('readonly');", dob_input)
        dob_input.clear()
        dob_input.send_keys(dob)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", dob_input)
        
        driver.find_element(By.ID, "btnSubmit").click()
        time.sleep(4)

        # استخراج النتائج
        def fetch(label):
            try:
                xpath = f"//span[contains(text(), '{label}')]/following::span[1] | //label[contains(text(), '{label}')]/following-sibling::div"
                return driver.find_element(By.XPATH, xpath).text.strip()
            except: return 'Not Found'

        card_no = fetch("Card Number")
        if card_no == 'Not Found': return None

        return {
            "Passport": passport, "Nationality": nationality, "DOB": dob,
            "Card Number": card_no,
            "Job": translate_text(fetch("Job Description")),
            "Issue Date": fetch("Card Issue"), "Expiry Date": fetch("Card Expiry"),
            "Salary": fetch("Total Salary"),
            "Name": "---", "Company": "---", "Status": "Contract Found"
        }
    finally:
        driver.quit()

# --- 6. منطق البحث العميق (الاستعلام عن بيانات العامل) ---
def deep_stage_search(card_number):
    driver = get_driver()
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        time.sleep(3)

        # المسار المطلوب: Work Permit -> Electronic Work Permit Information
        # 1. فتح القائمة
        driver.find_element(By.ID, "dropdownButton").click()
        time.sleep(1)
        
        # 2. اختيار القسم الرئيسي Work Permit
        options = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
        for opt in options:
            if 'Work Permit' in opt.text:
                opt.click()
                break
        time.sleep(2)

        # 3. اختيار الخدمة الفرعية EWPI
        sub_options = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
        for sub in sub_options:
            if 'Electronic Work Permit Information' in sub.text or 'EWPI' in sub.get_attribute('value'):
                sub.click()
                break
        time.sleep(2)

        # 4. إدخال رقم البطاقة وتجاوز الكابتشا
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        for inp in inputs:
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            if "captcha" not in placeholder and "verification" not in placeholder:
                inp.clear()
                inp.send_keys(card_number)
                break
        
        # السكريبت الخاص بالكابتشا
        captcha_script = """
        try {
            const code = [...document.querySelectorAll('div,span,b,label')].find(e => /^\\d{4}$/.test(e.innerText.trim())).innerText.trim();
            const field = [...document.querySelectorAll('input')].find(e => e.placeholder && (e.placeholder.includes('التحقق') || e.placeholder.includes('Verification')));
            if(code && field) { field.value = code; field.dispatchEvent(new Event('input', {bubbles:true})); }
        } catch(e) {}
        """
        driver.execute_script(captcha_script)
        time.sleep(1)
        
        # 5. الضغط على بحث
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)

        # 6. استخراج البيانات التفصيلية
        def get_val(lbl):
            try: return driver.find_element(By.XPATH, f"//*[contains(text(), '{lbl}')]/following::span[1]").text.strip()
            except: return 'Not Found'

        return {
            "Name": get_val("Name"),
            "Company": get_val("Est Name") if get_val("Est Name") != 'Not Found' else get_val("Establishment Name"),
            "Job": get_val("Designation") if get_val("Designation") != 'Not Found' else 'Updated'
        }
    except: return None
    finally:
        driver.quit()

# --- 7. واجهة المستخدم (Streamlit UI) ---
st.info("قم بإدخال البيانات الأساسية للبحث عن رقم البطاقة أولاً.")

c1, c2, c3 = st.columns(3)
passport = c1.text_input("رقم الجواز (Passport)")
nationality = c2.selectbox("الجنسية", countries_list)
dob = c3.date_input("تاريخ الميلاد", value=None, min_value=datetime(1950,1,1))

if st.button("البحث الأولي (Phase 1)", type="primary"):
    if passport and nationality != "Select Nationality" and dob:
        with st.spinner("جاري استخراج رقم البطاقة من وزارة الموارد البشرية..."):
            res = first_stage_search(passport, nationality, dob.strftime("%d/%m/%Y"))
            if res:
                st.session_state['data_result'] = res
                st.success("تم العثور على بيانات التعاقد!")
            else:
                st.error("لم يتم العثور على بيانات لهذا الجواز.")

# عرض النتيجة وتفعيل البحث العميق عبر رقم البطاقة
if st.session_state['data_result']:
    res = st.session_state['data_result']
    
    st.write("### نتيجة البحث:")
    # عرض الجدول
    df = pd.DataFrame([res])
    st.table(df)

    # جعل رقم البطاقة هو المحرك للبحث العميق
    card_number = res['Card Number']
    st.markdown(f"---")
    st.write("💡 **لجلب الاسم والمنشأة، اضغط على زر رقم البطاقة أدناه:**")
    
    # الزر الذي طلبه العميل (بدون أزرار إضافية)
    if st.button(f"🆔 تشغيل البحث العميق للبطاقة: {card_number}", use_container_width=True):
        with st.spinner("جاري الدخول لبوابة الاستعلام وجلب بيانات المنشأة والاسم..."):
            deep_res = deep_stage_search(card_number)
            if deep_res:
                # تحديث البيانات الأصلية بالبيانات الجديدة
                res['Name'] = deep_res['Name']
                res['Company'] = deep_res['Company']
                if deep_res['Job'] != 'Not Found': res['Job'] = deep_res['Job']
                res['Status'] = "Deep Search Completed ✅"
                
                st.session_state['data_result'] = res
                st.success("تم تحديث كافة البيانات بنجاح!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("فشل البحث العميق. قد يكون بسبب الكابتشا أو الموقع، يرجى المحاولة مرة أخرى.")

# إضافة خيار التنزيل
if st.session_state['data_result']:
    csv = pd.DataFrame([st.session_state['data_result']]).to_csv(index=False).encode('utf-8-sig')
    st.download_button("تحميل النتيجة (CSV)", data=csv, file_name="mohre_result.csv", mime="text/csv")
