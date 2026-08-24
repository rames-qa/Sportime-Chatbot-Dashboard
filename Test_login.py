import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

@pytest.fixture
def driver():
    service = Service(ChromeDriverManager().install())
    options = Options()

    # Disable Chrome Password Manager, Notifications, & Infobars
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.set_capability("unhandledPromptBehavior", "dismiss")

    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()

def kill_popup_dialogs(driver):
    """Purges ASP.NET / jQuery UI dialogs and overlays from the DOM."""
    driver.execute_script("""
        if (typeof $ !== 'undefined') {
            $('.ui-dialog, .modal, .popup, .sweet-alert').hide().remove();
            $('.ui-widget-overlay, .modal-backdrop').remove();
        }
        var elements = document.querySelectorAll('.ui-dialog, .modal, .popup, .ui-widget-overlay');
        elements.forEach(function(el) {
            if (el && el.parentNode) {
                el.parentNode.removeChild(el);
            }
        });
    """)

def test_sportime_e2e_login_and_dashboard(driver):
    wait = WebDriverWait(driver, 25)

    # 1. Load clean URL
    driver.get("https://sttest.aptussoft.com/Member/Aptus/Main")
    time.sleep(1)
    kill_popup_dialogs(driver)

    # 2. Check for header
    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'SPORTIME Member')]"))
    )
    assert header.is_displayed(), "Header text is not displayed."

    # 3. Dismiss any overlay buttons if present
    try:
        ok_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Ok')] | //span[contains(text(),'Ok')]")
        driver.execute_script("arguments[0].click();", ok_btn)
    except Exception:
        pass

    kill_popup_dialogs(driver)

    # 4. Input Credentials safely using JS Clear + Clickable Waits
    email_field = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@id='Email' or @type='email' or @name='Email']"))
    )
    driver.execute_script("arguments[0].value = '';", email_field)
    email_field.send_keys("sharanya@vedas.com")

    password_field = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@id='Password' or @type='password' or @name='Password']"))
    )
    driver.execute_script("arguments[0].value = '';", password_field)
    password_field.send_keys("1234")

    kill_popup_dialogs(driver)

    # 5. Submit Form via JS
    login_button = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[@type='submit' or contains(translate(normalize-space(.), 'LOG IN', 'log in'), 'log in') or @id='btnLogin']"
        ))
    )
    driver.execute_script("arguments[0].click();", login_button)

    # 6. Validate Dashboard Load
    # First, wait for post-login navigation/URL update
    wait.until(EC.url_changes("https://sttest.aptussoft.com/Member/Aptus/Main"))

    welcome_locator = (
        By.XPATH,
        "//*[contains(translate(normalize-space(.), 'WELCOME', 'welcome'), 'welcome') or contains(normalize-space(.), 'Web test') or contains(normalize-space(.), 'Dashboard')]"
    )
    welcome_text = wait.until(EC.presence_of_element_located(welcome_locator))
    assert welcome_text.is_displayed(), "Dashboard welcome text not visible."