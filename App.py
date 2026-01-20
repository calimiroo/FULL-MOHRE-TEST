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
import atexit

# --- إعداد السجل ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- إعداد الصفحة ---
st.set_page_config(page_title="MOHRE Portal", layout="wide")
st.title("HAMADA TRACING SITE TEST")

# --- إدارة جلسة العمل (Session State) ---
# (تم إضافة driver و driver_init_time)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'driver' not in st.session_state:
    st.session_state['driver'] = None
if 'driver_init_time' not in st.session_state:
    st.session_state['driver_init_time'] = None
# (باقي المتغيرات كما هي)
if 'run_state' not in st.session_state:
    st.session_state['run_state'] = 'stopped'
if 'batch_results' not in st.session_state:
    st.session_state['batch_results'] = []
# ...

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

# --- التعديل الجذري: إدارة الـ driver ---
def init_driver():
    """
    Initializes a Chrome driver with optimized options and stores it in the session state.
    """
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    # ... (باقي الخيارات من المحاولة السابقة)
    
    logger.info("Initializing a new Chrome driver...")
    driver = uc.Chrome(options=options, use_subprocess=True)
    st.session_state['driver'] = driver
    st.session_state['driver_init_time'] = time.time()
    logger.info("Driver initialized and stored in session state.")
    return driver

def get_or_init_driver():
    """
    Returns the existing driver from the session state or initializes a new one.
    It also handles recreation if the driver has crashed.
    """
    driver = st.session_state.get('driver')
    
    # إذا كان هناك driver، تحقق من أنه لا يزال يعمل
    if driver:
        try:
            # محاولة بسيطة للتأكد من أن الجلسة لا تزال نشطة
            _ = driver.window_handles
            # إعادة إنشاء الـ driver كل 10 دقائق لمنع تراكم المشاكل
            if time.time() - st.session_state.get('driver_init_time', 0) > 600:
                logger.info("Driver has been active for over 10 minutes. Re-initializing.")
                quit_driver()
                return init_driver()
            return driver
        except WebDriverException:
            logger.warning("Driver seems to have crashed. Re-initializing.")
            quit_driver() # تنظيف الـ driver القديم
            return init_driver()
            
    # إذا لم يكن هناك driver، قم بإنشاء واحد جديد
    return init_driver()

def quit_driver():
    """Safely quits the driver and removes it from the session state."""
    driver = st.session_state.get('driver')
    if driver:
        logger.info("Quitting the driver.")
        try:
            driver.quit()
        except Exception as e:
            logger.error(f"Error while quitting driver: {e}")
        st.session_state['driver'] = None
        st.session_state['driver_init_time'] = None

# تسجيل دالة التنظيف ليتم استدعاؤها عند خروج التطبيق
atexit.register(quit_driver)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- دوال الاستخراج (معدلة لتستخدم الـ driver المشترك) ---
def extract_data(driver, passport, nationality, dob_str):
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en" )
        # ... (باقي الكود كما هو، ولكن بدون get_driver() أو driver.quit())
        time.sleep(4)
        driver.find_element(By.ID, "txtPassportNumber").send_keys(passport)
        # ... (أكمل باقي الكود هنا)
        return # result_dict
    except Exception as e:
        logger.error(f"Error in extract_data for passport {passport}: {e}")
        # لا تقم بإغلاق الـ driver هنا، قد يكون بالإمكان إعادة استخدامه
        raise # رفع الخطأ ليتم التعامل معه في الحلقة الرئيسية

def deep_extract_by_card(driver, card_number):
    try:
        driver.get("https://inquiry.mohre.gov.ae/" )
        # ... (باقي الكود كما هو، ولكن بدون get_driver() أو driver.quit())
        wait = WebDriverWait(driver, 25)
        # ... (أكمل باقي الكود هنا)
        return # result_dict
    except Exception as e:
        logger.error(f"Error in deep_extract_by_card for card {card_number}: {e}")
        raise

# --- واجهة المستخدم (مع تعديلات على منطق الأزرار) ---
tab1, tab2 = st.tabs(["Single Search", "Upload Excel File"])

with tab1:
    st.subheader("Single Person Search")
    # ... (عناصر الإدخال كما هي)
    
    if st.button("Search Now"):
        if p_in and n_in != "Select Nationality" and d_in:
            with st.spinner("Initializing browser and searching..."):
                try:
                    # --- التعديل: احصل على الـ driver هنا ---
                    current_driver = get_or_init_driver()
                    res = extract_data(current_driver, p_in, n_in, d_in.strftime("%d/%m/%Y"))
                    # ... (باقي منطق عرض النتائج)
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    # حاول إغلاق الـ driver المتعطل
                    quit_driver()

# ... (يجب تطبيق نفس المنطق على باقي أجزاء الكود، مثل البحث العميق والبحث المجمع)
# ... (هذا مجرد مثال توضيحي لكيفية البدء)
