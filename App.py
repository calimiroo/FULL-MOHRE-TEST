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
st.set_page_config(page_title="MOHRE Inquiry System", layout="wide")

# --- دالة تشغيل المتصفح (إعدادات السيرفر السحابي) ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # إعدادات التخفي لتجاوز حماية الموقع
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # تحديد مسار المتصفح في نظام Debian الخاص بـ Streamlit
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # حذف علامة "webdriver" التي تكتشفها المواقع
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# --- واجهة المستخدم ---
st.title("🔎 نظام الاستعلام عن تصاريح العمل (MOHRE)")

if "results_list" not in st.session_state:
    st.session_state.results_list = []

# مدخلات البحث
col1, col2 = st.columns(2)
with col1:
    work_permit_no = st.text_input("رقم تصريح العمل / المعاملة", "")
with col2:
    person_birth_year = st.text_input("سنة الميلاد (مثال: 1990)", "")

# --- عملية البحث ---
if st.button("بدء البحث والتحقق 🚀", type="primary"):
    if not work_permit_no:
        st.error("يرجى إدخال رقم المعاملة أولاً")
    else:
        with st.spinner("جاري الاتصال بالموقع واستخراج البيانات..."):
            driver = None
            try:
                driver = get_driver()
                # رابط صفحة الاستعلام المباشر
                driver.get("https://inquiry.mohre.gov.ae/") 
                
                wait = WebDriverWait(driver, 20)
                
                # 1. إدخال البيانات (استخدام Selector عام يتوافق مع الموقع)
                # ملاحظة: الموقع يستخدم id='txtWorkPermitNo' أو مشابه
                permit_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
                permit_input.send_keys(work_permit_no)
                
                # 2. الضغط على زر البحث
                search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                search_button.click()
                
                # 3. حل مشكلة "Not Found" بالانتظار حتى ظهور النتيجة فعلياً
                time.sleep(5) # انتظار إضافي لضمان تحميل الـ AJAX
                
                try:
                    # محاولة جلب الاسم والبيانات بعد التحميل
                    # نستخدم CSS Selector مرن يبحث عن أي نص يحتوي على اسم العامل أو المنشأة
                    name = driver.find_element(By.XPATH, "//*[contains(@id, 'Name')]").text
                    company = driver.find_element(By.XPATH, "//*[contains(@id, 'Company') or contains(@id, 'Est')]").text
                    salary = driver.find_element(By.XPATH, "//*[contains(@id, 'Salary')]").text
                    status = "Found ✅"
                except:
                    name = "Not Found"
                    company = "Not Found"
                    salary = "N/A"
                    status = "Not Found ❌"
                    # التقاط صورة للخطأ للتشخيص
                    driver.save_screenshot("debug.png")

                # إضافة النتيجة للقائمة
                st.session_state.results_list.append({
                    "رقم المعاملة": work_permit_no,
                    "الاسم": name,
                    "المنشأة": company,
                    "الراتب": salary,
                    "الحالة": status
                })
                
            except Exception as e:
                st.error(f"خطأ في الاتصال: {str(e)}")
            finally:
                if driver:
                    driver.quit()

# --- عرض النتائج في جدول ملون ---
if st.session_state.results_list:
    df = pd.DataFrame(st.session_state.results_list)
    
    def color_status(val):
        color = '#d4edda' if 'Found ✅' in val else '#f8d7da'
        return f'background-color: {color}'

    st.subheader("النتائج الحالية")
    st.table(df.style.applymap(color_status, subset=['الحالة']))
    
    if st.button("مسح النتائج"):
        st.session_state.results_list = []
        st.rerun()

    # خيار تحميل ملف Excel
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("تحميل التقرير CSV", data=csv, file_name="mohre_results.csv", mime="text/csv")

if "debug.png" in locals() or "debug.png" in [f for f in ["debug.png"] if __import__('os').path.exists(f)]:
    with st.expander("معاينة الخطأ (Screenshot)"):
        st.image("debug.png")
