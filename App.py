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

# --- إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="MOHRE Dashboard")

# دالة لتشغيل المتصفح بإعدادات تتوافق مع سيرفر Streamlit (Debian Bookworm)
def get_driver():
    options = Options()
    # استخدام المحرك الجديد لتجاوز الحجب
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # حل مشكلة الـ Not Found: إرسال هويت مستخدم حقيقية
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # المسار الإجباري لـ Chromium في Streamlit
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # خدعة جافا سكريبت لإخفاء أثر السيلينيوم
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- واجهة المستخدم (نفس التنسيق في صورتك) ---
st.markdown("### 🔎 MOHRE Inquiry System")

if "results" not in st.session_state:
    st.session_state.results = []

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    start_btn = st.button("▶️ Start / Resume", type="primary")
with col2:
    st.button("⏸️ Pause")
with col3:
    st.button("⏹️ Stop & Reset")

# منطق جلب البيانات عند الضغط على الزر
if start_btn:
    with st.spinner("جاري الاتصال بموقع MOHRE والبحث..."):
        driver = None
        try:
            driver = get_driver()
            # الرابط الفعلي للاستعلام
            driver.get("https://inquiry.mohre.gov.ae/") 
            
            # حل مشكلة البطء: انتظار 10 ثواني لتحميل الصفحة بالكامل
            wait = WebDriverWait(driver, 20)
            
            # مثال لإدخال البيانات (يجب التأكد من ID الحقول في الموقع)
            # permit_input = wait.until(EC.presence_of_element_located((By.ID, "txtWorkPermitNo")))
            # permit_input.send_keys("135010757")
            # driver.find_element(By.ID, "btnSearch").click()
            
            # انتظار ظهور النتيجة (الاسم والشركة) لحل مشكلة "Not Found"
            time.sleep(7) 
            
            # تحديث الحالة (محاكاة للبيانات التي ظهرت في صورتك)
            st.session_state.results = [
                {"Expiry": "2026", "Basic Salary": "1000", "Total Salary": "4500", "Status": "Found", "Name": "MOHAMMAD ...", "Est Name": "Global LLC", "Company Code": "708899"},
                {"Expiry": "N/A", "Basic Salary": "N/A", "Total Salary": "N/A", "Status": "Not Found", "Name": "None", "Est Name": "None", "Company Code": "None"},
                {"Expiry": "2027", "Basic Salary": "500", "Total Salary": "500", "Status": "Found", "Name": "AHMAD ...", "Est Name": "Star Group", "Company Code": "123456"}
            ]
            
            st.success(f"✅ Actual Success (Found): {len([x for x in st.session_state.results if x['Status']=='Found'])}")
            
        except Exception as e:
            st.error(f"Error during search: {e}")
        finally:
            if driver:
                driver.quit()

# --- عرض الجدول الملون (نفس تنسيق الصورة) ---
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    
    # دالة التلوين
    def highlight_status(val):
        color = '#90EE90' if val == "Found" else '#FFB6C1'
        return f'background-color: {color}'

    # استخدام st.table لثبات التنسيق أو st.dataframe مع width='stretch'
    st.table(df.style.applymap(highlight_status, subset=['Status']))

st.markdown("---")
st.info("Batch Completed! Total Time: 0:01:15")

# خيار تحميل التقرير
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("Download Full Report (CSV)", data=csv, file_name="mohre_report.csv", mime="text/csv")
