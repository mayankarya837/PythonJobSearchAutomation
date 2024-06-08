import io
import logging
import os
import sys
import time
from datetime import datetime
from random import choice, randint
from string import ascii_uppercase, digits

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager as CM
from selenium.webdriver.common.action_chains import ActionChains

# Update your naukri username and password here before running
username = "xxxx"
password = "xxxx"

# Set login URL
NaukriURL = "https://www.naukri.com/nlogin/login"
logging.basicConfig(level=logging.INFO, filename="naukri.log", format="%(asctime)s : %(message)s")
os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_LOG_LEVEL"] = "0"


def log_msg(message):
    print(message)
    logging.info(message)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    lineNo = str(exc_tb.tb_lineno)
    msg = "%s : %s at Line %s." % (type(error), error, lineNo)
    print(msg)
    logging.error(msg)


def getObj(locatorType):
    map = {
        "ID": By.ID,
        "NAME": By.NAME,
        "XPATH": By.XPATH,
        "TAG": By.TAG_NAME,
        "CLASS": By.CLASS_NAME,
        "CSS": By.CSS_SELECTOR,
        "LINKTEXT": By.LINK_TEXT,
    }
    return map[locatorType.upper()]


def GetElement(driver, elementTag, locator="ID"):
    try:
        def _get_element(_tag, _locator):
            _by = getObj(_locator)
            if is_element_present(driver, _by, _tag):
                return WebDriverWait(driver, 15).until(
                    lambda d: driver.find_element(_by, _tag)
                )

        element = _get_element(elementTag, locator.upper())
        if element:
            return element
        else:
            log_msg("Element not found with %s : %s" % (locator, elementTag))
            return None
    except Exception as e:
        catch(e)
    return None


def is_element_present(driver, how, what):
    try:
        driver.find_element(by=how, value=what)
    except NoSuchElementException:
        return False
    return True


def WaitTillElementPresent(driver, elementTag, locator="ID", timeout=30):
    result = False
    driver.implicitly_wait(0)
    locator = locator.upper()

    for _ in range(timeout):
        time.sleep(0.99)
        try:
            if is_element_present(driver, getObj(locator), elementTag):
                result = True
                break
        except Exception as e:
            log_msg("Exception when WaitTillElementPresent : %s" % e)
            pass

    if not result:
        log_msg("Element not found with %s : %s" % (locator, elementTag))
    driver.implicitly_wait(3)
    return result


def tearDown(driver):
    try:
        driver.close()
        log_msg("Driver Closed Successfully")
    except Exception as e:
        catch(e)
        pass

    try:
        driver.quit()
        log_msg("Driver Quit Successfully")
    except Exception as e:
        catch(e)
        pass


def randomText():
    return "".join(choice(ascii_uppercase + digits) for _ in range(randint(1, 5)))


def LoadNaukri(headless):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("headless")

    driver = None
    try:
        driver = webdriver.Chrome(options, service=ChromeService(CM().install()))
    except:
        driver = webdriver.Chrome(options)
    log_msg("Google Chrome Launched!")

    driver.implicitly_wait(3)
    driver.get(NaukriURL)
    return driver


def naukriLogin(headless=False):
    status = False
    driver = None
    username_locator = "usernameField"
    password_locator = "passwordField"
    login_btn_locator = "//*[@type='submit' and normalize-space()='Login']"
    skip_locator = "//*[text() = 'SKIP AND CONTINUE']"

    try:
        driver = LoadNaukri(headless)

        if "naukri" in driver.title.lower():
            log_msg("Website Loaded Successfully.")

        emailFieldElement = None
        if is_element_present(driver, By.ID, username_locator):
            emailFieldElement = GetElement(driver, username_locator, locator="ID")
            time.sleep(1)
            passFieldElement = GetElement(driver, password_locator, locator="ID")
            time.sleep(1)
            loginButton = GetElement(driver, login_btn_locator, locator="XPATH")
        else:
            log_msg("None of the elements found to login.")

        if emailFieldElement is not None:
            emailFieldElement.clear()
            emailFieldElement.send_keys(username)
            time.sleep(1)
            passFieldElement.clear()
            passFieldElement.send_keys(password)
            time.sleep(1)
            loginButton.send_keys(Keys.ENTER)
            time.sleep(1)

            if WaitTillElementPresent(driver, skip_locator, "XPATH", 10):
                GetElement(driver, skip_locator, "XPATH").click()

            if WaitTillElementPresent(driver, "ff-inventory", locator="ID", timeout=40):
                CheckPoint = GetElement(driver, "ff-inventory", locator="ID")
                if CheckPoint:
                    log_msg("Naukri Login Successful")
                    status = True
                    return (status, driver)
                else:
                    log_msg("Unknown Login Error")
                    return (status, driver)
            else:
                log_msg("Unknown Login Error")
                return (status, driver)

    except Exception as e:
        catch(e)
    return (status, driver)


def search_jobs(driver, roles, job_age, max_experience):
    # search_url = f'https://www.naukri.com/{role.replace(" ", "-")}-jobs?experience=0-{max_experience}&jobPostType=RECENT'
   # Encode roles for the URL
    encoded_roles = '%20'.join([role.replace(' ', '%20') for role in roles])
    # Combine roles into the URL path
    roles_path = '-'.join([role.replace(' ', '-').lower() for role in roles])

    # Construct the search URL
    search_url = (f'https://www.naukri.com/{roles_path}-jobs'
                f'?k={encoded_roles}'
                f'&experience={max_experience}'
                f'&jobAge={job_age}'
                f'&nignbevent_src=jobsearchDeskGNB')
    # Navigate to the search URL
    driver.get(search_url)
    # Apply date filter
    try:
        filter_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "filter-sort")))
        filter_button.click()
        date_filter_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.styles_ss__menu__9TuCu a[data-id='filter-sort-f']")))
        date_filter_option.click()
    except Exception as e:
        print("An error occurred while applying the date filter:", e)   
    time.sleep(10000)


def apply_to_jobs(driver, roles,job_age, max_experience):
    jobs_applied = []
    companies_applied = set()
    successful_applications_count = 0  # Counter for successful applications  

    for page in range(1, 6):
        # search_url = f'https://www.naukri.com/{role.replace(" ", "-")}-jobs-{page}?experience=0-{max_experience}&jobPostType=RECENT'
        # driver.get(search_url)
        # job_links = [job.get_attribute('href') for job in driver.find_elements(By.CSS_SELECTOR, 'a.title')]

        # Encode roles for the URL
        encoded_roles = '%20'.join([role.replace(' ', '%20') for role in roles])
        # Combine roles into the URL path
        roles_path = '-'.join([role.replace(' ', '-').lower() for role in roles])

        # Construct the search URL
        search_url = (f'https://www.naukri.com/{roles_path}-jobs-{page}'
                    f'?k={encoded_roles}'
                    f'&experience={max_experience}'
                    f'&jobAge={job_age}'
                    f'&nignbevent_src=jobsearchDeskGNB'
                    f'&glbl_qcrc=1026')#used this code for search Devops Profile only
        # Navigate to the search URL
        driver.get(search_url)
        
        # Apply date filter
        try:
            filter_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "filter-sort")))
            filter_button.click()
            date_filter_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.styles_ss__menu__9TuCu a[data-id='filter-sort-f']")))
            date_filter_option.click()
            driver.get(search_url)
        except Exception as e:
            print("An error occurred while applying the date filter:", e) 
        print('url = '+ search_url)

        #Get job links on the current page
        job_links = [job.get_attribute('href') for job in driver.find_elements(By.CSS_SELECTOR, 'a.title')]
        for job_link in job_links:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(job_link)
            try:
                # Use XPath to locate the company name by its title attribute
                company_name_element = driver.find_element(By.XPATH, '//*[contains(@class, "styles_jd-header-comp-name__MvqAI")]//a[contains(@title, "Careers")]')
                if company_name_element:
                    company_name = company_name_element.get_attribute('title').split(' Careers')[0].strip()
                    # log_msg(f"Company name detected: {company_name}")  # Debug log for company name
                    if company_name in companies_applied:
                        log_msg(f"Already opened {company_name}. Skipping this job.")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue
                    else:
                        companies_applied.add(company_name)

                # Check for "Already Applied" status
                if is_element_present(driver, By.ID, 'already-applied'):
                    log_msg(f"Job already applied to {company_name}. Moving to the next job.")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue

                # Check for "Apply on company site" button
                elif is_element_present(driver, By.ID, 'company-site-button'):
                    log_msg(f"'External Site for {company_name} company'. Moving to the next job.")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue

                # Check for "Apply" button
                elif is_element_present(driver, By.ID, 'apply-button'):
                    apply_button = driver.find_element(By.ID, 'apply-button')
                    apply_button.click()
                    time.sleep(3)  # Wait for any possible dialog box to appear

                    # Check for the presence of the chatbot dialog box
                    if is_element_present(driver, By.CLASS_NAME, 'chatbot_MessageContainer'):
                        log_msg(f"Chatbot dialog box detected for {company_name}. Moving to the next job.")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                    # Check for the success message
                    if is_element_present(driver, By.CLASS_NAME, 'apply-message'):
                        success_message_element = driver.find_element(By.CLASS_NAME, 'apply-message')
                        if "You have successfully applied to" in success_message_element.text:
                            log_msg(f"Successfully applied to {company_name}.")
                            jobs_applied.append(job_link)
                            successful_applications_count += 1  # Increment the counter
                            log_msg(f"Total successful applications till now: {successful_applications_count} \n")


                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    if len(jobs_applied) >= 100:
                        log_msg(f"Total successful applications today: {successful_applications_count}")
                        return successful_applications_count

            except Exception as e:
                catch(e)
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue
    log_msg(f"Total successful applications today: {successful_applications_count}")
    return jobs_applied


def main():
    log_msg("-----Naukri.py Script Run Begin-----")
    driver = None
    role = ['DevOps Engineer','DevSecOps Engineer','Cloud security']
    max_experience = 5  # Example max experience
    job_age = 30  # Example job age in days
    try:
        status, driver = naukriLogin()
        if status:
            #search_jobs(driver, role, job_age, max_experience)
            jobs_applied = apply_to_jobs(driver, role, job_age, max_experience)
            log_msg(f'Applied to {len(jobs_applied)} jobs:')
            for job in jobs_applied:
                log_msg(job)

    except Exception as e:
        catch(e)

    finally:
        tearDown(driver)
    log_msg("-----Naukri.py Script Run Ended-----\n")


if __name__ == "__main__":
    main()