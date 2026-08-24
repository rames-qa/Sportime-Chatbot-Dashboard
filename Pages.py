import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

@pytest.fixture
def driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

def test_login_page_navigation(driver):
    wait = WebDriverWait(driver, 15)
    driver.get("https://sttest.aptussoft.com/Member/Aptus/Main")

    # 1. Verify Header
    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'SPORTIME Member')]"))
    )
    assert header.is_displayed(), "Header text is not displayed."

    # 2. Toggle Mobile Login via JS Click (handles animations/overlays)
    mobile_btn = wait.until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@aria-label,'Login with Mobile') or contains(text(),'Mobile')]"))
    )
    driver.execute_script("arguments[0].click();", mobile_btn)

    # 3. Toggle Back to Email Login via JS Click
    email_btn = wait.until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@aria-label,'Login with Email') or contains(text(),'Email')]"))
    )
    driver.execute_script("arguments[0].click();", email_btn)

    # 4. Click Password Login Link
    pwd_login_link = wait.until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Login with email and password')]"))
    )
    driver.execute_script("arguments[0].click();", pwd_login_link)
    