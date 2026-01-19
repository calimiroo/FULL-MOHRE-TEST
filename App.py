import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import os

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST (Server Mode with Screenshots)")

# --- إدارة جلسة العمل (Session State) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None

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

def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

# --- إعداد المتصفح (تم إجباره على Headless لمنع الخطأ) ---
def get_driver():
    options = uc.ChromeOptions()
    # إجباري للسيرفرات السحابية
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080') # حجم شاشة كبير لضمان ظهور العناصر
    return uc.Chrome(options=options, headless=True, use_subprocess=False)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- البحث الأول ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver()
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
        if card_num == 'Not Found': return None

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
            "Name": "", "Est Name": "", "Company Code": ""
        }
    except Exception:
        return None
    finally:
        try: driver.quit()
        except: pass

# --- البحث العميق (مع عرض الصور) ---
def deep_extract_by_card_debug(card_number):
    driver = get_driver()
    debug_images = [] # لتخزين الصور وعرضها لاحقاً
    
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        # صورة 1: الصفحة الرئيسية
        driver.save_screenshot("step1_home.png")
        debug_images.append(("Home Page Loaded", "step1_home.png"))

        # 1. محاولة اختيار الخدمة
        try:
            btn = driver.find_element(By.ID, "dropdownButton")
            btn.click()
            time.sleep(1)
            # محاولة البحث عن الخيار
            lis = driver.find_elements(By.CSS_SELECTOR, "#dropdownList li")
            found_option = False
            for li in lis:
                if 'EWPI' in li.get_attribute('value') or 'Work Permit' in li.text:
                    li.click()
                    found_option = True
                    break
            if not found_option and lis:
                lis[1].click() # اختيار افتراضي
        except Exception as e:
            debug_images.append((f"Error Selecting Service: {str(e)}", None))

        time.sleep(1)

        # 2. إدخال البطاقة
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for inp in inputs:
                nm = (inp.get_attribute("name") or "").lower()
                if "captcha" not in nm and "verification" not in (inp.get_attribute("placeholder") or "").lower():
                    inp.clear()
                    inp.send_keys(card_number)
                    break
        except: pass
        
        # صورة 2: بعد إدخال البيانات
        driver.save_screenshot("step2_filled.png")
        debug_images.append(("Data Filled", "step2_filled.png"))

        # 3. الكابتشا
        try:
            js_fill = "try{const c=[...document.querySelectorAll('div,span,b')].find(e=>/^\\d{4}$/.test(e.innerText.trim()));const i=[...document.querySelectorAll('input')].find(e=>e.placeholder&&e.placeholder.includes('التحقق'));if(c&&i){i.value=c.innerText.trim();i.dispatchEvent(new Event('input',{bubbles:true}));}}catch(e){}"
            driver.execute_script(js_fill)
        except: pass

        time.sleep(1)

        # 4. الضغط على بحث
        try:
            search_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            search_btn.click()
        except:
             # محاولة بديلة للزر
             try:
                 driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'بحث')]").click()
             except: pass
        
        time.sleep(5) 

        # صورة 3: النتيجة النهائية
        driver.save_screenshot("step3_result.png")
        debug_images.append(("Search Result Page", "step3_result.png"))

        # 5. استخراج البيانات
        def get_txt(lbl):
            try:
                # محاولة قراءة النص مباشرة
                return driver.find_element(By.XPATH, f"//*[contains(text(), '{lbl}')]/following::span[1]").text.strip()
            except:
                # محاولة القراءة من هيكل الصفحة النصي كخيار بديل
                try:
                    page = driver.find_element(By.TAG_NAME, "body").text
                    for line in page.split('\n'):
                        if lbl in line:
                            return line.split(':')[-1].strip()
                except: pass
                return 'Not Found'

        data = {
            'Name': get_txt('Name'),
            'Est Name': get_txt('Est Name'),
            'Company Code': get_txt('Company Code'),
            'Designation': get_txt('Designation')
        }
        
        if data['Est Name'] == 'Not Found': data['Est Name'] = get_txt('Establishment Name')

        return data, debug_images

    except Exception as e:
        return None, debug_images
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
    
    if st.session_state['single_result']:
        res = st.session_state['single_result']
        st.write("### Result:")
        st.table(pd.DataFrame([res]))

        card_num = res.get('Card Number')
        if card_num and card_num != 'Not Found':
            st.markdown("---")
            st.info(f"💡 **Deep Search:** Click below to check Card `{card_num}` on Inquiry Portal.")
            
            if st.button(f"🔍 Deep Search Card: {card_num}"):
                with st.spinner(f"Connecting to MOHRE Inquiry (This might take 10s)..."):
                    # استدعاء دالة البحث مع الصور
                    deep_res, images = deep_extract_by_card_debug(card_num)
                    
                    # عرض الصور للتشخيص (Debugging)
                    st.write("#### 📸 Live Server Screenshots (Debug):")
                    img_cols = st.columns(len(images))
                    for idx, (title, img_path) in enumerate(images):
                        with img_cols[idx]:
                            if img_path and os.path.exists(img_path):
                                st.image(img_path, caption=title, use_column_width=True)
                            else:
                                st.warning(f"No image for {title}")

                    if deep_res:
                        st.session_state['single_result'].update(deep_res)
                        if deep_res.get('Designation') != 'Not Found':
                             st.session_state['single_result']['Job Description'] = deep_res.get('Designation')
                        
                        st.success("Deep Search Completed! Data Updated.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Deep search failed. Check the screenshots above to see why.")

with tab2:
    st.info("Batch search functionality is available here.")
