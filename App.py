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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
if 'single_result' not in st.session_state:
    st.session_state['single_result'] = None
if 'deep_single_running' not in st.session_state:
    st.session_state['deep_single_running'] = False
if 'deep_single_card' not in st.session_state:
    st.session_state['deep_single_card'] = None
if 'deep_single_result' not in st.session_state:
    st.session_state['deep_single_result'] = {}
if 'deep_current_index' not in st.session_state:
    st.session_state['deep_current_index'] = 0
if 'single_search_executed' not in st.session_state:
    st.session_state['single_search_executed'] = False
if 'deep_search_started' not in st.session_state:
    st.session_state['deep_search_started'] = False

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

# --- دوال مساعدة ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

def translate_to_english(text):
    try:
        if text and text not in ['Not Found', 'N/A']:
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except Exception:
        return text

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    return uc.Chrome(options=options, use_subprocess=True)

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- دوال الاستخراج ---
def extract_data(passport, nationality, dob_str):
    driver = None
    for attempt in range(3):
        try:
            driver = get_driver()
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
                except Exception:
                    return 'Not Found'

            card_num = get_value("Card Number")
            if card_num == 'Not Found':
                if driver: driver.quit()
                return None

            result = {
                "Passport Number": passport, "Nationality": nationality, "Date of Birth": dob_str,
                "Job Description": translate_to_english(get_value("Job Description")),
                "Card Number": card_num, "Card Issue": get_value("Card Issue"), "Card Expiry": get_value("Card Expiry"),
                "Basic Salary": get_value("Basic Salary"), "Total Salary": get_value("Total Salary"), "Status": "Found"
            }
            if driver: driver.quit()
            return result
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for passport {passport}: {e}")
            if driver: driver.quit()
            time.sleep(3)
    return None

def deep_extract_by_card(card_number):
    driver = None
    for attempt in range(3):
        try:
            driver = get_driver()
            driver.get("https://inquiry.mohre.gov.ae/" )
            wait = WebDriverWait(driver, 20)

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

            # (الكود المتبقي للدالة كما هو)
            # ...

            # إذا نجحت العملية، قم بإرجاع النتيجة
            # ...
            
            if driver: driver.quit()
            # return result_dict
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for card {card_number}: {e}")
            if driver: driver.quit()
            time.sleep(3)
    return None

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
                    st.session_state['single_result'] = res
                    st.session_state['deep_single_running'] = False
                    st.session_state['deep_single_card'] = None
                    st.session_state['deep_single_result'] = {}
                    st.session_state['single_search_executed'] = True
                else:
                    st.error("No data found or an error occurred after 3 attempts.")
                    st.session_state['single_result'] = None
                    st.session_state['single_search_executed'] = True
                st.rerun()

    if st.session_state['single_search_executed']:
        if st.session_state['single_result']:
            result_df = pd.DataFrame([st.session_state['single_result']])
            st.dataframe(result_df, use_container_width=True)

            if st.session_state['single_result']['Card Number'] not in ['N/A', 'Not Found']:
                card_num_display = st.session_state['single_result']['Card Number']
                if st.button(f"🔍 Deep Search Card {card_num_display}", key=f"deep_search_{card_num_display}"):
                    st.session_state['deep_single_running'] = True
                    st.session_state['deep_single_card'] = card_num_display
                    st.rerun()
        else:
            st.info("Search completed with no results, or an error occurred.")

    if st.session_state['deep_single_running'] and not st.session_state['deep_single_result']:
        card_to_search = st.session_state['deep_single_card']
        with st.spinner(f"Deep searching card {card_to_search}..."):
            deep_res = deep_extract_by_card(card_to_search)
            if deep_res:
                st.session_state['deep_single_result'] = deep_res
                updated_res = st.session_state['single_result'].copy()
                updated_res.update({
                    'Job Description': deep_res.get('Designation', 'Not Found'),
                    'Name': deep_res.get('Name', 'Not Found'),
                    'Est Name': deep_res.get('Est Name', 'Not Found'),
                    'Company Code': deep_res.get('Company Code', 'Not Found')
                })
                st.session_state['single_result'] = updated_res
                st.success(f"Deep search completed for card {card_to_search}.")
            else:
                st.error(f"Deep search failed for card {card_to_search} after 3 attempts.")
                updated_res = st.session_state['single_result'].copy()
                updated_res.update({'Name': 'Not Found', 'Est Name': 'Not Found', 'Company Code': 'Not Found'})
                st.session_state['single_result'] = updated_res
            st.session_state['deep_single_running'] = False
            st.rerun()

    if st.session_state.get('deep_single_result'):
        st.subheader("Deep Search Result")
        updated_df = pd.DataFrame([st.session_state['single_result']])
        st.dataframe(updated_df, use_container_width=True)
        csv = updated_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Single Result (CSV)", csv, f"single_result_{st.session_state['single_result']['Card Number']}.csv", 'text/csv')

with tab2:
    # (الكود الخاص بالتاب الثاني يبقى كما هو)
    st.subheader("Batch Processing Control")
    # ...
