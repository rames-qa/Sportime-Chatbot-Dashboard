
import time

import pytest

from selenium import webdriver

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC



def safe_fill_field(driver, wait, locators, value):

    """Tries multiple locators and falls back to JavaScript typing if send_keys fails."""

    element = None

    for loc in locators:

        try:

            element = wait.until(EC.presence_of_element_located((By.XPATH, loc)))

            if element:

                break

        except Exception:

            continue



    if not element:

        raise Exception(f"Unable to find input element matching locators: {locators}")



    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    time.sleep(0.5)



    try:

        element.clear()

        element.send_keys(value)

    except Exception:

        # JS Fallback if element is obscured or disabled

        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input')); arguments[0].dispatchEvent(new Event('change'));", element, value)



def test_sportime_e2e_login_and_dashboard(driver):

    wait = WebDriverWait(driver, 25)



    # --- STEP 1: LOAD PAGE & TOGGLE TABS ---

    driver.get("https://sttest.aptussoft.com/Member/Aptus/Main#")



    header = wait.until(

        EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'SPORTIME Member')]"))

    )

    assert header.is_displayed(), "Header text is missing."



    # Mobile Login Toggle

    mobile_btn = wait.until(

        EC.presence_of_element_located((

            By.XPATH,

            "//a[contains(translate(normalize-space(.), 'MOBILE', 'mobile'), 'mobile') or contains(@aria-label, 'Mobile')]"

        ))

    )

    driver.execute_script("arguments[0].click();", mobile_btn)

    time.sleep(0.5)



    # Email Login Toggle

    email_btn = wait.until(

        EC.presence_of_element_located((

            By.XPATH,

            "//a[contains(translate(normalize-space(.), 'EMAIL', 'email'), 'email') or contains(@aria-label, 'Email')]"

        ))

    )

    driver.execute_script("arguments[0].click();", email_btn)

    time.sleep(0.5)



    # Password Login Toggle

    pwd_login_link = wait.until(

        EC.presence_of_element_located((

            By.XPATH,

            "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'password') or contains(@href, 'password') or contains(@id, 'pwd')]"

        ))

    )

    driver.execute_script("arguments[0].click();", pwd_login_link)

    time.sleep(1)



    # --- STEP 2: ROBUST CREDENTIAL FILL ---

    email_locators = [

        "//input[@id='Email']",

        "//input[@type='email']",

        "//input[@name='Email']",

        "//input[contains(@placeholder, 'Email')]"

    ]

    safe_fill_field(driver, wait, email_locators, "sharanya@vedas.com")



    password_locators = [

        "//input[@id='Password']",

        "//input[@type='password']",

        "//input[@name='Password']",

        "//input[contains(@placeholder, 'Password')]"

    ]

    safe_fill_field(driver, wait, password_locators, "1234")



    # Submit Login

    login_button = wait.until(

        EC.presence_of_element_located((

            By.XPATH,

            "//button[@type='submit' or contains(translate(normalize-space(.), 'LOG IN', 'log in'), 'log in') or contains(., 'Sign In')]"

        ))

    )

    driver.execute_script("arguments[0].click();", login_button)



    # --- STEP 3: DASHBOARD LOAD VALIDATION ---

    welcome_text = wait.until(

        EC.presence_of_element_located((

            By.XPATH,

            "//*[contains(translate(text(), 'WELCOME', 'welcome'), 'welcome') or contains(text(),'Web test')]"

        ))

    )

    assert welcome_text.is_displayed(), "Welcome message missing on dashboard."



