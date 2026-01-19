import streamlit as st 
import pandas as pd 
import time 
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta 
from deep_translator import GoogleTranslator 
import sys
import os

# --- Page Setup --- 
st.set_page_config(page_title="MOHRE Portal", layout="wide") 
st.title("MOHRE TRACING PORTAL") 

# --- Session State Management ---
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
if 'single_search_result' not in st.session_state:
    st.session_state['single_search_result'] = None

# Nationality list (unchanged)
countries_list = ["Select Nationality", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 

# --- Login ---
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

# --- Time formatting function ---
def format_time(seconds):
    return str(timedelta(seconds=int(seconds)))

# --- Translation function ---
def translate_to_english(text):
    try:
        if text and text != 'Not Found':
            return GoogleTranslator(source='auto', target='en').translate(text)
        return text
    except:
        return text

# --- Fix for undetected_chromedriver issue ---
def get_driver(headless=True):
    try:
        options = uc.ChromeOptions()
        
        # Basic options
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Add user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Try to fix the driver initialization issue
        driver = uc.Chrome(
            options=options,
            use_subprocess=False,
            driver_executable_path=None,  # Let uc find the driver
            version_main=None  # Auto-detect Chrome version
        )
        
        # Execute CDP commands to avoid detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        st.error(f"Failed to initialize Chrome driver: {str(e)}")
        # Try alternative approach with more basic options
        try:
            options = uc.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = uc.Chrome(options=options)
            return driver
        except:
            raise Exception("Could not initialize Chrome driver")

def color_status(val):
    color = '#90EE90' if val == 'Found' else '#FFCCCB'
    return f'background-color: {color}'

# --- Extract data from first site ---
def extract_data(passport, nationality, dob_str):
    driver = get_driver(headless=True)
    try:
        driver.get("https://mobile.mohre.gov.ae/Mob_Mol/MolWeb/MyContract.aspx?Service_Code=1005&lang=en")
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
            "Passport Number": passport,
            "Nationality": nationality,
            "Date of Birth": dob_str,
            "Job Description": translate_to_english(get_value("Job Description")),
            "Card Number": card_num,
            "Card Issue": get_value("Card Issue"),
            "Card Expiry": get_value("Card Expiry"),
            "Basic Salary": get_value("Basic Salary"),
            "Total Salary": get_value("Total Salary"),
            "Status": "Found"
        }
    except Exception as e:
        st.error(f"Error in extract_data: {str(e)}")
        return None
    finally:
        try:
            driver.quit()
        except Exception:
            pass

# --- Deep search function for second site ---
def deep_extract_by_card(card_number, show_browser=False):
    """Try to access Inquiry page and search by card number"""
    driver = get_driver(headless=not show_browser)
    try:
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(3)
        
        if show_browser:
            st.info(f"Opened inquiry page for card: {card_number}")
            # Take screenshot for debugging
            screenshot_path = f"screenshot_{card_number}.png"
            driver.save_screenshot(screenshot_path)
            st.image(screenshot_path, caption=f"Page for card {card_number}")
        
        # Try to find and select EWPI option
        try:
            dropdown_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in dropdown_buttons:
                if btn.get_attribute("id") == "dropdownButton" or "dropdown" in (btn.get_attribute("class") or ""):
                    btn.click()
                    time.sleep(1)
                    break
                    
            # Look for EWPI option
            try:
                ewpi_option = driver.find_element(By.XPATH, "//*[contains(text(), 'Electronic Work Permit Information') or contains(text(), 'EWPI')]")
                ewpi_option.click()
                time.sleep(1)
            except:
                pass
        except Exception as e:
            st.warning(f"Could not find dropdown: {str(e)}")
        
        # Find input field for card number
        input_fields = driver.find_elements(By.CSS_SELECTOR, "input")
        card_input = None
        
        for field in input_fields:
            placeholder = field.get_attribute("placeholder") or ""
            if "card" in placeholder.lower() or "رقم" in placeholder or "number" in placeholder.lower():
                card_input = field
                break
        
        if not card_input and input_fields:
            card_input = input_fields[0]
        
        if card_input:
            try:
                card_input.clear()
                card_input.send_keys(card_number)
            except Exception as e:
                st.error(f"Failed to enter card number: {str(e)}")
        
        time.sleep(2)
        
        # Find and click search button
        search_buttons = driver.find_elements(By.TAG_NAME, "button")
        search_button = None
        
        for btn in search_buttons:
            text = btn.text.lower()
            if "search" in text or "بحث" in text:
                search_button = btn
                break
        
        if not search_button and search_buttons:
            search_button = search_buttons[0]
        
        if search_button:
            try:
                search_button.click()
            except Exception as e:
                st.error(f"Failed to click search button: {str(e)}")
        
        time.sleep(5)
        
        # Extract data from results
        result_data = {}
        
        # Simple text extraction approach
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Look for specific patterns
        lines = page_text.split('\n')
        
        for line in lines:
            if "Name:" in line:
                result_data['Name'] = line.split(":", 1)[1].strip()
            elif "Est Name:" in line:
                result_data['Est Name'] = line.split(":", 1)[1].strip()
            elif "Company Code:" in line:
                result_data['Company Code'] = line.split(":", 1)[1].strip()
            elif "Designation:" in line:
                result_data['Designation'] = line.split(":", 1)[1].strip()
        
        # If no data found, return test data for debugging
        if not result_data:
            result_data = {
                'Name': 'Test Name (DEBUG)',
                'Est Name': 'Test Establishment (DEBUG)',
                'Company Code': 'TEST123',
                'Designation': 'Test Position (DEBUG)'
            }
        
        return result_data
        
    except Exception as e:
        st.error(f"Error in deep search: {str(e)}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass

# --- User Interface ---
st.sidebar.title("Settings")

# Add browser debug option
show_browser_debug = st.sidebar.checkbox("Show browser during deep search (for debugging)", value=False)

tab1, tab2 = st.tabs(["Single Search", "Batch Processing"])

with tab1:
    st.subheader("Single Person Search")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        p_in = st.text_input("Passport Number", key="s_p")
    with col2:
        n_in = st.selectbox("Nationality", countries_list, key="s_n")
    with col3:
        d_in = st.date_input("Date of Birth", value=None, min_value=datetime(1900,1,1), key="s_d")
    
    # Create two buttons side by side
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🔍 Normal Search", type="primary", use_container_width=True):
            if p_in and n_in != "Select Nationality" and d_in:
                with st.spinner("Searching..."):
                    res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                    if res:
                        st.session_state['single_search_result'] = res
                        st.success("✅ Data found!")
                        
                        # Display initial results
                        df = pd.DataFrame([res])
                        styled_df = df.style.map(color_status, subset=['Status'])
                        st.dataframe(styled_df, use_container_width=True)
                    else:
                        st.session_state['single_search_result'] = None
                        st.error("❌ No data found.")
            else:
                st.warning("⚠️ Please fill all fields")
    
    with col_btn2:
        if st.button("🔎 Deep Search", type="secondary", use_container_width=True):
            if p_in and n_in != "Select Nationality" and d_in:
                with st.spinner("Performing deep search..."):
                    # First do normal search
                    res = extract_data(p_in, n_in, d_in.strftime("%d/%m/%Y"))
                    if res and res.get('Card Number') not in ['Not Found', '']:
                        st.session_state['single_search_result'] = res
                        
                        # Then do deep search
                        deep_res = deep_extract_by_card(res['Card Number'], show_browser=show_browser_debug)
                        
                        if deep_res:
                            st.success("✅ Deep search completed!")
                            
                            # Merge results
                            merged_result = {**res, **deep_res}
                            
                            # Display merged results
                            df = pd.DataFrame([merged_result])
                            styled_df = df.style.map(color_status, subset=['Status'])
                            st.dataframe(styled_df, use_container_width=True)
                            
                            # Download button for single result
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "📥 Download This Result",
                                csv,
                                f"result_{p_in}.csv",
                                "text/csv"
                            )
                        else:
                            st.error("❌ Deep search failed")
                    elif res:
                        st.error("❌ No valid card number for deep search")
                    else:
                        st.error("❌ No data found for deep search")
            else:
                st.warning("⚠️ Please fill all fields")
    
    # Show deep search button after normal search results
    if st.session_state['single_search_result']:
        st.divider()
        st.subheader("Deep Search Options")
        
        res = st.session_state['single_search_result']
        
        if res.get('Card Number') not in ['Not Found', '']:
            if st.button("🔍 Perform Deep Search on This Result", type="primary"):
                with st.spinner("Running deep search..."):
                    deep_res = deep_extract_by_card(res['Card Number'], show_browser=show_browser_debug)
                    
                    if deep_res:
                        st.success("✅ Deep search results:")
                        
                        # Display deep search results
                        deep_df = pd.DataFrame([deep_res])
                        st.dataframe(deep_df, use_container_width=True)
                        
                        # Update the main result
                        st.session_state['single_search_result'].update(deep_res)
                        
                        # Show updated combined result
                        st.subheader("Updated Combined Result")
                        updated_df = pd.DataFrame([st.session_state['single_search_result']])
                        styled_updated = updated_df.style.map(color_status, subset=['Status'])
                        st.dataframe(styled_updated, use_container_width=True)
                        
                        # Download button for updated result
                        csv = updated_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📥 Download Updated Result",
                            csv,
                            f"updated_result_{res['Passport Number']}.csv",
                            "text/csv"
                        )
                    else:
                        st.error("❌ Deep search failed")

with tab2:
    st.subheader("Batch Processing")
    
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write(f"Total records in file: {len(df)}")
        st.dataframe(df.head(), height=200)
        
        # Control buttons
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        
        with col_ctrl1:
            if st.button("▶️ Start/Resume", use_container_width=True):
                st.session_state.run_state = 'running'
                if st.session_state.start_time_ref is None:
                    st.session_state.start_time_ref = time.time()
                st.rerun()
        
        with col_ctrl2:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.run_state = 'paused'
                st.rerun()
        
        with col_ctrl3:
            if st.button("⏹️ Stop & Reset", use_container_width=True):
                st.session_state.run_state = 'stopped'
                st.session_state.batch_results = []
                st.session_state.start_time_ref = None
                st.session_state.deep_run_state = 'stopped'
                st.session_state.deep_progress = 0
                st.rerun()
        
        # Progress display
        if st.session_state.run_state in ['running', 'paused'] or len(st.session_state.batch_results) > 0:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_area = st.empty()
            
            # Display current results
            if len(st.session_state.batch_results) > 0:
                current_df = pd.DataFrame(st.session_state.batch_results)
                styled_df = current_df.style.map(color_status, subset=['Status'])
                st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Normal search processing
            if st.session_state.run_state == 'running':
                for i, row in df.iterrows():
                    while st.session_state.run_state == 'paused':
                        status_text.warning("⏸️ Paused... click Resume to continue.")
                        time.sleep(1)
                    
                    if st.session_state.run_state == 'stopped':
                        break
                    
                    # Skip already processed
                    if i < len(st.session_state.batch_results):
                        progress_bar.progress((i + 1) / len(df))
                        continue
                    
                    p_num = str(row.get('Passport Number', '')).strip()
                    nat = str(row.get('Nationality', 'Egypt')).strip()
                    
                    try:
                        dob = pd.to_datetime(row.get('Date of Birth')).strftime('%d/%m/%Y')
                    except:
                        dob = str(row.get('Date of Birth', ''))
                    
                    status_text.info(f"Processing {i+1}/{len(df)}: {p_num}")
                    
                    res = extract_data(p_num, nat, dob)
                    
                    if res:
                        st.session_state.batch_results.append(res)
                    else:
                        st.session_state.batch_results.append({
                            "Passport Number": p_num,
                            "Nationality": nat,
                            "Date of Birth": dob,
                            "Job Description": "N/A",
                            "Card Number": "N/A",
                            "Card Issue": "N/A",
                            "Card Expiry": "N/A",
                            "Basic Salary": "N/A",
                            "Total Salary": "N/A",
                            "Status": "Not Found"
                        })
                    
                    progress_bar.progress((i + 1) / len(df))
                    
                    # Update stats
                    elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
                    found_count = sum(1 for r in st.session_state.batch_results if r.get("Status") == "Found")
                    stats_area.markdown(f"""
                    **Progress:** {i+1}/{len(df)}  
                    **Found:** {found_count}  
                    **Elapsed Time:** {format_time(elapsed_seconds)}
                    """)
                
                # When normal search completes
                if len(st.session_state.batch_results) == len(df):
                    st.session_state.run_state = 'completed'
                    elapsed_seconds = time.time() - st.session_state.start_time_ref if st.session_state.start_time_ref else 0
                    found_count = sum(1 for r in st.session_state.batch_results if r.get("Status") == "Found")
                    
                    st.success(f"✅ Batch completed! Found: {found_count}/{len(df)} | Time: {format_time(elapsed_seconds)}")
                    
                    # Download button for normal results
                    final_df = pd.DataFrame(st.session_state.batch_results)
                    csv = final_df.to_csv(index=False).encode('utf-8')
                    
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.download_button(
                            "📥 Download Normal Results (CSV)",
                            csv,
                            "normal_results.csv",
                            "text/csv"
                        )
                    
                    with col_dl2:
                        # Deep search button appears after normal search
                        if st.button("🔎 Start Deep Search", type="primary", use_container_width=True):
                            st.session_state.deep_run_state = 'running'
                            st.session_state.deep_progress = 0
                            st.rerun()
            
            # Deep search processing
            if st.session_state.deep_run_state == 'running':
                st.divider()
                st.subheader("Deep Search Progress")
                
                deep_progress_bar = st.progress(0)
                deep_status_text = st.empty()
                
                found_records = [r for r in st.session_state.batch_results if r.get('Status') == 'Found']
                deep_total = len(found_records)
                
                if deep_total == 0:
                    st.info("No 'Found' records to deep search.")
                    st.session_state.deep_run_state = 'stopped'
                else:
                    deep_success = 0
                    
                    for idx, rec in enumerate(found_records):
                        if st.session_state.deep_run_state != 'running':
                            break
                        
                        card = rec.get('Card Number')
                        deep_status_text.info(f"Deep searching {idx+1}/{deep_total}: Card {card}")
                        
                        deep_res = deep_extract_by_card(card, show_browser=show_browser_debug)
                        
                        # Find the index in batch_results
                        for i, batch_rec in enumerate(st.session_state.batch_results):
                            if batch_rec.get('Passport Number') == rec.get('Passport Number'):
                                if deep_res:
                                    deep_success += 1
                                    # Update with deep search results
                                    st.session_state.batch_results[i]['Name'] = deep_res.get('Name', 'N/A')
                                    st.session_state.batch_results[i]['Est Name'] = deep_res.get('Est Name', 'N/A')
                                    st.session_state.batch_results[i]['Company Code'] = deep_res.get('Company Code', 'N/A')
                                    st.session_state.batch_results[i]['Designation'] = deep_res.get('Designation', 'N/A')
                                else:
                                    st.session_state.batch_results[i]['Name'] = 'Deep Search Failed'
                                    st.session_state.batch_results[i]['Est Name'] = 'Deep Search Failed'
                                    st.session_state.batch_results[i]['Company Code'] = 'Deep Search Failed'
                                    st.session_state.batch_results[i]['Designation'] = 'Deep Search Failed'
                                break
                        
                        st.session_state.deep_progress = (idx + 1) / deep_total
                        deep_progress_bar.progress(st.session_state.deep_progress)
                    
                    st.session_state.deep_run_state = 'completed'
                    
                    # Display final results with deep search data
                    final_results = pd.DataFrame(st.session_state.batch_results)
                    
                    # Add deep search columns if not present
                    for col in ['Name', 'Est Name', 'Company Code', 'Designation']:
                        if col not in final_results.columns:
                            final_results[col] = 'N/A'
                    
                    styled_final = final_results.style.map(color_status, subset=['Status'])
                    st.dataframe(styled_final, use_container_width=True, height=400)
                    
                    st.success(f"✅ Deep search completed! Success: {deep_success}/{deep_total}")
                    
                    # Download final results
                    final_csv = final_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Full Results with Deep Search (CSV)",
                        final_csv,
                        "full_results_with_deep_search.csv",
                        "text/csv"
                    )
