def deep_extract_by_card(card_number):
    """
    نسخة محسّنة للبحث العميق مع معالجة أفضل للكابتشا والعناصر الديناميكية
    """
    if not card_number or card_number in ['N/A', 'Not Found', 'Not Available']:
        logger.info(f"Card number is invalid ({card_number}), skipping deep search.")
        return {
            'Name': 'Invalid Card Number',
            'Est Name': 'Invalid Card Number',
            'Company Code': 'Invalid Card Number',
            'Designation': 'Invalid Card Number'
        }

    driver = None
    try:
        # استخدام Chrome عادي بدون headless للتعامل مع الكابتشا
        options = uc.ChromeOptions()
        # جرّب بدون headless للتجربة الأولى
        # options.add_argument('--headless')  
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        driver = uc.Chrome(options=options, use_subprocess=False)
        wait = WebDriverWait(driver, 30)
        
        # 1) الوصول للصفحة
        logger.info(f"Accessing inquiry.mohre.gov.ae for card: {card_number}")
        driver.get("https://inquiry.mohre.gov.ae/")
        time.sleep(5)  # انتظار تحميل الصفحة بالكامل
        
        # 2) التقاط screenshot للتشخيص
        driver.save_screenshot(f"/tmp/mohre_initial_{card_number}.png")
        logger.info("Initial page screenshot saved")
        
        # 3) البحث عن القائمة المنسدلة بطرق متعددة
        dropdown_clicked = False
        
        # المحاولة 1: باستخدام ID
        try:
            dropdown_btn = wait.until(EC.presence_of_element_located((By.ID, "dropdownButton")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", dropdown_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", dropdown_btn)
            dropdown_clicked = True
            logger.info("Dropdown clicked using ID")
        except Exception as e:
            logger.warning(f"Failed to click dropdown by ID: {e}")
        
        # المحاولة 2: باستخدام Class أو XPath
        if not dropdown_clicked:
            try:
                dropdown_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'dropdown') or contains(@id, 'dropdown')]")
                driver.execute_script("arguments[0].click();", dropdown_btn)
                dropdown_clicked = True
                logger.info("Dropdown clicked using XPath")
            except Exception as e:
                logger.warning(f"Failed to click dropdown by XPath: {e}")
        
        if not dropdown_clicked:
            logger.error("Could not find or click dropdown button")
            driver.save_screenshot(f"/tmp/mohre_error_{card_number}.png")
            return None
        
        time.sleep(2)
        
        # 4) اختيار "Electronic Work Permit Information"
        option_selected = False
        
        # المحاولة 1: باستخدام القيمة
        try:
            ewpi_option = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[value='EWPI']")))
            driver.execute_script("arguments[0].click();", ewpi_option)
            option_selected = True
            logger.info("EWPI option selected using value")
        except Exception as e:
            logger.warning(f"Failed to select EWPI by value: {e}")
        
        # المحاولة 2: باستخدام النص
        if not option_selected:
            try:
                ewpi_option = driver.find_element(By.XPATH, "//li[contains(text(), 'Electronic Work Permit') or contains(text(), 'Work Permit')]")
                driver.execute_script("arguments[0].click();", ewpi_option)
                option_selected = True
                logger.info("EWPI option selected using text")
            except Exception as e:
                logger.warning(f"Failed to select EWPI by text: {e}")
        
        # المحاولة 3: الضغط على أول خيار في القائمة
        if not option_selected:
            try:
                first_option = driver.find_element(By.CSS_SELECTOR, "#dropdownList li:first-child")
                driver.execute_script("arguments[0].click();", first_option)
                option_selected = True
                logger.info("First option in dropdown selected")
            except Exception as e:
                logger.warning(f"Failed to select first option: {e}")
        
        if not option_selected:
            logger.error("Could not select EWPI option")
            return None
        
        time.sleep(2)
        
        # 5) إدخال رقم البطاقة - محاولات متعددة
        input_filled = False
        
        # المحاولة 1: البحث باستخدام placeholder
        try:
            card_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@type='text' or @type='number']")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_input)
            driver.execute_script("arguments[0].value = '';", card_input)
            card_input.clear()
            card_input.send_keys(card_number)
            input_filled = True
            logger.info(f"Card number {card_number} entered")
        except Exception as e:
            logger.warning(f"Failed to enter card number: {e}")
        
        # المحاولة 2: إدخال مباشر بـ JavaScript
        if not input_filled:
            try:
                driver.execute_script(f"document.querySelector('input[type=\"text\"]').value = '{card_number}';")
                input_filled = True
                logger.info("Card number entered using JavaScript")
            except Exception as e:
                logger.warning(f"Failed to enter card using JS: {e}")
        
        if not input_filled:
            logger.error("Could not enter card number")
            return None
        
        time.sleep(1)
        driver.save_screenshot(f"/tmp/mohre_before_search_{card_number}.png")
        
        # 6) التعامل مع الكابتشا
        # هنا يجب إضافة توقف مؤقت إذا كان الموقع يحتوي على كابتشا يدوية
        logger.info("Waiting for CAPTCHA resolution (if any)...")
        time.sleep(5)  # وقت إضافي للكابتشا
        
        # محاولة حل الكابتشا تلقائياً (إذا كان من نوع reCAPTCHA)
        try:
            # البحث عن iframe الكابتشا
            captcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha') or contains(@src, 'captcha')]")
            if captcha_frames:
                logger.warning("reCAPTCHA detected - manual intervention required")
                # هنا يمكن إضافة انتظار طويل أو تنبيه المستخدم
                time.sleep(30)  # انتظار 30 ثانية للحل اليدوي
        except:
            pass
        
        # 7) الضغط على زر البحث
        search_clicked = False
        
        # المحاولة 1: باستخدام ID
        try:
            search_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnSearch")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", search_btn)
            search_clicked = True
            logger.info("Search button clicked using ID")
        except Exception as e:
            logger.warning(f"Failed to click search by ID: {e}")
        
        # المحاولة 2: باستخدام النص
        if not search_clicked:
            try:
                search_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'بحث') or @type='submit']")
                driver.execute_script("arguments[0].click();", search_btn)
                search_clicked = True
                logger.info("Search button clicked using text")
            except Exception as e:
                logger.warning(f"Failed to click search by text: {e}")
        
        if not search_clicked:
            logger.error("Could not click search button")
            return None
        
        # 8) انتظار النتائج
        logger.info("Waiting for search results...")
        time.sleep(8)  # انتظار أطول لتحميل النتائج
        
        driver.save_screenshot(f"/tmp/mohre_results_{card_number}.png")
        
        # 9) البحث عن النتائج بطرق متعددة
        result_found = False
        page_source = driver.page_source
        
        # فحص إذا كانت هناك رسالة "لا توجد نتائج"
        if any(text in page_source.lower() for text in ['no results', 'no data', 'not found', 'لا توجد نتائج']):
            logger.info(f"No results message found for card {card_number}")
            return {
                'Name': 'Not Available',
                'Est Name': 'Not Available',
                'Company Code': 'Not Available',
                'Designation': 'Not Available'
            }
        
        # البحث عن عناصر النتيجة
        try:
            # محاولة العثور على جدول النتائج أو div يحتوي على البيانات
            result_container = driver.find_element(By.XPATH, 
                "//*[contains(@class, 'result') or contains(@class, 'data') or contains(@id, 'result')]"
            )
            result_found = True
            logger.info("Result container found")
        except:
            # محاولة أخرى: البحث عن أي عنصر يحتوي على "Name" أو "الاسم"
            try:
                name_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'Name') or contains(text(), 'الاسم')]"
                )
                if name_elements:
                    result_found = True
                    logger.info(f"Found {len(name_elements)} name elements")
            except:
                pass
        
        if not result_found:
            logger.warning(f"No clear result structure found for card {card_number}")
            # محاولة استخراج من النص الكامل
            return extract_from_page_text(page_source)
        
        # 10) استخراج البيانات
        def get_value_improved(label, driver):
            """استخراج محسّن للقيم"""
            try:
                # الطريقة 1: البحث بالـ label والقيمة التالية
                xpath_patterns = [
                    f"//label[contains(text(), '{label}')]/following-sibling::*[1]",
                    f"//span[contains(text(), '{label}')]/following-sibling::*[1]",
                    f"//strong[contains(text(), '{label}')]/following-sibling::*[1]",
                    f"//td[contains(text(), '{label}')]/following-sibling::td[1]",
                    f"//*[contains(text(), '{label}:')]/following-sibling::*[1]"
                ]
                
                for pattern in xpath_patterns:
                    try:
                        elements = driver.find_elements(By.XPATH, pattern)
                        for elem in elements:
                            text = elem.text.strip()
                            if text and text != label:
                                logger.info(f"Found {label}: {text}")
                                return text
                    except:
                        continue
                
                # الطريقة 2: البحث في نص الصفحة
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if label in line:
                        # القيمة قد تكون في نفس السطر أو السطر التالي
                        if ':' in line:
                            value = line.split(':', 1)[1].strip()
                            if value:
                                return value
                        elif i + 1 < len(lines):
                            return lines[i + 1].strip()
                
                return 'Not Available'
            except Exception as e:
                logger.warning(f"Error extracting {label}: {e}")
                return 'Not Available'
        
        # استخراج البيانات المطلوبة
        name = get_value_improved('Name', driver)
        est_name = get_value_improved('Est Name', driver)
        if est_name == 'Not Available':
            est_name = get_value_improved('Establishment Name', driver)
        company_code = get_value_improved('Company Code', driver)
        designation = get_value_improved('Designation', driver)
        if designation == 'Not Available':
            designation = get_value_improved('Job Title', driver)
        
        result = {
            'Name': name if name else 'Not Available',
            'Est Name': est_name if est_name else 'Not Available',
            'Company Code': company_code if company_code else 'Not Available',
            'Designation': designation if designation else 'Not Available'
        }
        
        logger.info(f"Extraction result for {card_number}: {result}")
        return result
        
    except TimeoutException as e:
        logger.error(f"Timeout while processing card {card_number}: {e}")
        return {
            'Name': 'Timeout Error',
            'Est Name': 'Timeout Error',
            'Company Code': 'Timeout Error',
            'Designation': 'Timeout Error'
        }
    except Exception as e:
        logger.error(f"Error in deep_extract_by_card for card {card_number}: {e}", exc_info=True)
        return {
            'Name': 'Error',
            'Est Name': 'Error',
            'Company Code': 'Error',
            'Designation': 'Error'
        }
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass


def extract_from_page_text(page_source):
    """استخراج احتياطي من نص الصفحة"""
    try:
        # تحويل HTML إلى نص
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        text = soup.get_text()
        
        # البحث عن الأنماط
        import re
        name_match = re.search(r'Name[:\s]+([^\n]+)', text, re.IGNORECASE)
        est_match = re.search(r'Est(?:ablishment)?\s+Name[:\s]+([^\n]+)', text, re.IGNORECASE)
        code_match = re.search(r'Company\s+Code[:\s]+([^\n]+)', text, re.IGNORECASE)
        desig_match = re.search(r'Designation[:\s]+([^\n]+)', text, re.IGNORECASE)
        
        return {
            'Name': name_match.group(1).strip() if name_match else 'Not Available',
            'Est Name': est_match.group(1).strip() if est_match else 'Not Available',
            'Company Code': code_match.group(1).strip() if code_match else 'Not Available',
            'Designation': desig_match.group(1).strip() if desig_match else 'Not Available'
        }
    except Exception as e:
        logger.error(f"Error in extract_from_page_text: {e}")
        return {
            'Name': 'Not Available',
            'Est Name': 'Not Available',
            'Company Code': 'Not Available',
            'Designation': 'Not Available'
        }
