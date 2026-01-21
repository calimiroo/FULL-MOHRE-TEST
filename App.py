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
st.set_page_config(page_title="MOHRE Deep Search", layout="wide")

# --- دالة تجهيز المتصفح مع التخفي (Stealth Mode) ---
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")  # تشغيل في الخلفية
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080") # حجم شاشة وهمي
    
    # 1. تمويه المتصفح ليبدو كمستخدم حقيقي
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    
    # 2. إخفاء علامات الأتمتة
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # مسار الكروم في سيرفرات Streamlit
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 3. تعديل خصائص Navigator بالجافاسكريبت لإخفاء Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# --- واجهة التطبيق ---
st.title("🔎 MOHRE Advanced Inquiry System")
st.markdown("---")

# مدخلات البيانات (يمكنك استبدالها برفع ملف CSV)
col1, col2 = st.columns(2)
with col1:
    card_no = st.text_input("رقم البطاقة / المعاملة", placeholder="أدخل الرقم هنا")
with col2:
    # انتبه لصيغة التاريخ المطلوبة في الموقع
    birth_date = st.text_input("تاريخ الميلاد", placeholder="DD/MM/YYYY")

if st.button("بدء البحث العميق 🚀", type="primary"):
    if not card_no or not birth_date:
        st.warning("يرجى إدخال البيانات المطلوبة.")
    else:
        status_area = st.empty()
        status_area.info("جاري تهيئة المتصفح والاتصال بالموقع...")
        
        driver = None
        try:
            driver = get_driver()
            
            # 1. الانتقال للموقع (تأكد من الرابط الصحيح)
            target_url = "https://inquiry.mohre.gov.ae/" # ⚠️ ضع الرابط الفعلي هنا
            driver.get(target_url)
            
            status_area.info("جاري إدخال البيانات...")

            # 2. الانتظار حتى تظهر حقول الإدخال (عدل الـ ID حسب الموقع الفعلي)
            wait = WebDriverWait(driver, 20) # انتظار لغاية 20 ثانية
            
            # مثال: التعامل مع الحقول (يجب عليك التأكد من الـ IDs من خلال Inspect Element)
            # input_card = wait.until(EC.presence_of_element_located((By.ID, "txtCardNumber")))
            # input_card.clear()
            # input_card.send_keys(card_no)
            
            # input_date = driver.find_element(By.ID, "txtBirthDate")
            # input_date.send_keys(birth_date)
            
            # الضغط على زر البحث
            # search_btn = driver.find_element(By.ID, "btnSearch")
            # search_btn.click()
            
            status_area.info("جاري تحليل النتائج...")

            # 3. انتظار النتائج - هنا السر في حل مشكلة Not Found
            # ننتظر ظهور العنصر الذي يحتوي على الاسم تحديداً
            try:
                # ⚠️ استبدل 'lblPersonNameEn' بالـ ID الحقيقي للاسم في الموقع
                name_element = wait.until(EC.visibility_of_element_located((By.ID, "lblPersonNameEn")))
                found_name = name_element.text
                
                # جلب باقي البيانات
                found_company = driver.find_element(By.ID, "lblCompanyName").text
                found_status = "Found ✅"
                
            except Exception as e:
                # في حالة الفشل، نلتقط صورة لنعرف السبب
                driver.save_screenshot("error_page.png")
                found_name = "Not Found"
                found_company = "Not Found"
                found_status = "Error/Timeout ❌"
                st.image("error_page.png", caption="لقطة شاشة عند حدوث الخطأ")

            # عرض النتائج
            st.success("اكتملت العملية!")
            
            result_data = {
                "Card Number": [card_no],
                "Name": [found_name],
                "Company": [found_company],
                "Status": [found_status]
            }
            st.table(pd.DataFrame(result_data))

        except Exception as e:
            st.error(f"حدث خطأ غير متوقع: {e}")
            if driver:
                driver.save_screenshot("crash_report.png")
                st.image("crash_report.png")
        
        finally:
            # لا تغلق المتصفح إذا كنت تستخدم cache_resource وتريد استخدامه مرة أخرى،
            # لكن لتوفير الذاكرة يفضل إغلاقه أو إعادة استخدامه بذكاء.
            # driver.quit() 
            pass
