from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://probuildstats.com/"

options = Options()
options.add_argument("--headless")

DRIVER_PATH = './chromedriver'
service = Service(executable_path=DRIVER_PATH)


def click_each_link(links):
    driver = webdriver.Chrome(service=service, options=options)
    for link in links:
        driver.get(link.get_attribute("href"))
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".match-card")))
    driver.quit()

# Get all games from the main page
def get_game_links():
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".match-card")))
    game_links = driver.find_elements(By.CSS_SELECTOR, ".match-card")
    driver.quit()
    return game_links



def main():
    links = get_game_links()
    click_each_link(links)
    

if __name__ == '__main__':
    main()