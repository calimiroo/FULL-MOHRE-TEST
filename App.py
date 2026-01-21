import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# إعدادات الصفحة لتجنب تحذيرات التنسيق في الصور
st.set_page_config(layout="wide", page_title="MOHRE Dashboard")

@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless=new") # الوضع المطور لتجاوز الحجب
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # حل مشكلة الـ Not Found الناتجة عن حماية الموقع
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # تحديد مسار المتصفح الإجباري للسيرفر
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # إخفاء هوية البوت برمجياً
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# واجهة التطبيق - نفس التنسيق المطلوب
st.title("🔎 MOHRE Inquiry System")

if "results" not in st.session_state:
    st.session_state.results = []

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("▶️ Start / Resume", type="primary"):
        with st.spinner("جاري جلب البيانات..."):
            driver = None
            try:
                driver = get_driver()
                driver.get("https://inquiry.mohre.gov.ae/") # الرابط الفعلي
                
                # انتظار 7 ثوانٍ لضمان تحميل البيانات وحل مشكلة Not Found
                time.sleep(7) 
                
                # إضافة نتيجة تجريبية لمحاكاة كودك (يجب وضع منطق استخراج البيانات هنا)
                new_data = {
                    "Expiry": "2026",
                    "Basic Salary": "1000",
                    "Total Salary": "4500",
                    "Status": "Found",
                    "Name": "MOHAMMAD D...", 
                    "Est Name": "Global LLC",
                    "Company Code": "708899"
                }
                st.session_state.results.append(new_data)
                st.success("تم تحديث البيانات بنجاح!")
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
            finally:
                if driver: driver.quit()

# --- إصلاح خطأ NameError: name 'df' is not defined ---
if st.session_state.results:
    # نقوم بتعريف df هنا داخل الشرط لضمان وجود بيانات
    df = pd.DataFrame(st.session_state.results)
    
    def highlight_status(val):
        color = '#90EE90' if val == 'Found' else '#FFB6C1'
        return f'background-color: {color}'

    # استخدام .map بدلاً من .applymap لتجنب تحذير التحديث
    st.table(df.style.map(highlight_status, subset=['Status']))
else:
    st.info("لا توجد بيانات لعرضها حالياً. اضغط على Start للبدء.")

st.button("Download Full Report (CSV)")
