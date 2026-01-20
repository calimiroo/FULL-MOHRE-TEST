import streamlit as st
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
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
# (لا تغيير هنا)
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
# ... (باقي متغيرات الجلسة كما هي)

# --- قائمة الجنسيات (بدون تغيير) ---
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

# --- تسجيل الدخول (بدون تغيير) ---
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

# --- دوال مساعدة (مع تعديل get_driver) ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

# --- التعديل: دالة get_driver مع خيارات محسنة ---
def get_driver():
    """
    Initializes a Chrome driver with options optimized for stability
    in a resource-constrained environment like Streamlit Cloud.
    """
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--proxy-server="direct://"')
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-infobars')
    options.add_argument('--ignore-certificate-errors')
    
    # تعطيل تحميل الصور لتقليل استهلاك الذاكرة
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # استخدام مسار محدد لبيانات المستخدم لتجنب التعارضات
    options.add_argument('--user-data-dir=/tmp/chrome-user-data')

    try:
        logger.info("Initializing Chrome driver...")
        driver = uc.Chrome(options=options, use_subprocess=True)
        logger.info("Driver initialized successfully.")
        return driver
    except Exception as e:
        logger.critical(f"Failed to initialize driver: {e}")
        # محاولة تنظيف أي عمليات عالقة
        import os
        os.system("pkill -f 'undetected_chromedriver'")
        raise e # رفع الخطأ لإيقاف العملية

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- دوال الاستخراج (مع تعديلات طفيفة) ---
def extract_data(passport, nationality, dob_str):
    driver = None
    try:
        driver = get_driver()
        # (باقي الكود كما هو)
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en" )
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
            "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num, "Card Issue": get_value("Card Issue"), "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"), "Status": "Found"
        }
    except Exception as e:
        logger.error(f"Error in extract_data for passport {passport}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def deep_extract_by_card(card_number):
    driver = None
    for attempt in range(2): # تقليل عدد المحاولات إلى 2 لتجنب استهلاك الوقت
        try:
            driver = get_driver()
            driver.get("https://inquiry.mohre.gov.ae/" )
            wait = WebDriverWait(driver, 25) # زيادة وقت الانتظار قليلاً

            # (باقي الكود كما هو في المحاولة السابقة)
            dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "dropdownButton")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_btn)
            dropdown_btn.click()
            time.sleep(1)

            wait.until(EC.presence_of_element_located((By.ID, "dropdownList")))
            ewpi_option = driver.find_element(By.CSS_SELECTOR, "li[value='EWPI']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ewpi_option)
            driver.execute_script("arguments[0].click();", ewpi_option)
            time.sleep(1)

            card_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Card') or contains(@placeholder, 'Work Permit')]")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_input)
            driver.execute_script("arguments[0].value = '';", card_input)
            driver.execute_script("arguments[0].value = arguments[1];", card_input, card_number)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", card_input)
            time.sleep(0.5)

            # ... (باقي الكود لاستخراج البيانات)
            
            # إذا نجحت العملية، قم بإرجاع النتيجة
            # ...
            
            if driver:
                driver.quit()
            # return result_dict
            # الكود الكامل لاستخراج البيانات هنا...
            # (تم حذفه للاختصار، لكنه موجود في الكود الذي أرسلته سابقًا)

        except WebDriverException as e:
            logger.error(f"Attempt {attempt + 1} failed for card {card_number} with WebDriverException: {e.msg}")
            if "Message: ''" in e.msg or "session deleted" in e.msg:
                logger.critical("Browser crashed! Trying to clean up and retry...")
                if driver:
                    driver.quit()
                time.sleep(5) # انتظار أطول بعد التعطل
                continue # انتقل إلى المحاولة التالية
            else:
                if driver:
                    driver.quit()
                return None # فشل لسبب آخر
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for card {card_number} with general error: {e}")
            if driver:
                driver.quit()
            time.sleep(3)
    
    logger.error(f"All attempts failed for card {card_number}.")
    return None

# --- واجهة المستخدم (بدون تغيير) ---
# (الكود المتبقي يبقى كما هو)
# ...
