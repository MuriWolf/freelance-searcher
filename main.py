from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from dataclasses import dataclass
import sys
import string
import secrets

@dataclass
class Empresa:
    nome: str
    industria: str
    telefone: str

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 0.5)

argc = len(sys.argv)

URL: str

# the reason that is exist is: I want to find out if the commerce has a own website, these ones doesnt tell that, so this list serves to ignore them.
IGNORE_WEBSITES: list[str] = [
    'agenciacorreios.com.br',
    'econodata.com.br',
    'solutudo.com.br',
    'instagram.com',
    'facebook.com',
    'tiktok.com',
    'x.com',
    'cnpj.linkana.com',
    'cnpj.info',
    'linkedin.com',
    'shopee.com',
    'waze.com',
    'listamais.com'
]

def setup():
    driver.get(URL)

def teardown(driver):
    driver.quit()

def find_and_verify_phone_number():
    response = { "valid": False, "number": None }
    phone_number = None

    try:
        phone_number = wait.until(EC.visibility_of_element_located((By.XPATH, "//span[contains(@aria-label,'Ligar para')]"))).text
        is_number_valid = re.match("^\(\d{2}\) 9\d{4}-\d{4}$", phone_number)
        response["number"] = phone_number

        if (is_number_valid):
            response["valid"] = True

    except:
        print("(PHONE NOT FOUND ERROR)")
    
    if (not response['valid'] and phone_number is not None): print(f"(PHONE VALIDATION ERROR): {phone_number}")

   
    return response

# This has a big problem, after some pages, this area doesnt load anymore (infinite loading). Refreshing page doesnt fix it.
def find_and_verify_web_links():
    try:
        related_websites = wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//*[@class='Iukrse Ba6aoe']/div[1]/a")))
        related_websites_links = [item.get_attribute('href') for item in related_websites]

        for link in related_websites_links:
            matching = [ignore_website for ignore_website in IGNORE_WEBSITES if ignore_website in link]
            if len(matching) == 0:
                print(f"(WEBSITES VALIDATION ERROR) business already has website or its not registered on list of ignore websites: {link}")
                return False
    except:
            print("(NO RELATED WEBSITES FOUND OR TIMED OUT)")
    
    return True

def has_business_website():
    try:
        website = wait.until(EC.visibility_of_element_located((By.XPATH, "//span[text()='Site']")))
        if (website):
            print("(BUSINESS ALREADY HAS WEBSITE)")
            return True
    except:
        return False 

def get_business_name():
    try:
        return wait.until(EC.visibility_of_element_located((By.XPATH, '//div/div[1]/div/g-sticky-content-container/div/block-component/div/div[1]/div/div/div/div[1]/div/div/div[2]/div/div[1]/div/div/h2/span'))).text
    except:
        return None

def get_business_industry():
    try:
        return wait.until(EC.visibility_of_element_located((By.XPATH, '//div/div[1]/div/g-sticky-content-container/div/block-component/div/div[1]/div/div/div/div[1]/div/div/div[2]/div/div[2]/div[2]/div/span'))).text
    except:
        return '' 

def get_all_pages(): 
    return wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//div[contains(@aria-label, 'Paginação dos resultados locais')]/table/tbody/tr/td/a")))

def get_all_businesess_from_current_page():
    try:
        return wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//*[@class='rlfl__tls rl_tls']/*[@id]")))
    except:
        None

def filter_business() -> Empresa | None:
    response_verify_phone = find_and_verify_phone_number()
    if (not response_verify_phone["valid"]): return None 

    if (has_business_website() is True): return None 

    business_name = get_business_name()
    if (business_name is None): return None
    business_industry = get_business_industry()
    business_phone = response_verify_phone["number"]

    return Empresa(nome=business_name, industria=business_industry, telefone=business_phone) 

def get_file_name():
    random_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return 'results-' + random_str + '.csv'

def initialize_results_file() -> str:
    file_name = get_file_name()
    print("\n" + file_name)
    with open('results.csv', 'w') as f:
        f.write("Nome, Industria, Telefone \n")

    return file_name
def write_results_file(file_name: str, businesses: list[Empresa]):
    with open(file_name, 'a') as f:
        for business in businesses:
            f.write(f'"{business.nome}","{business.industria}","{business.telefone}"\n')

def main():
    setup()
   
    filtered_businesses: list[Empresa] = []

    pages = get_all_pages()
    pages_count = len(pages) 

    for i in range(0, pages_count):
        print(f"Current page: {i + 1}\n")
        current_url = URL
        if (i > 0):
            current_url = current_url + f";start:{i * 20}"
            driver.get(current_url)

        time.sleep(2.25)
    
        business_current_page_list = get_all_businesess_from_current_page()

        if business_current_page_list is None:
            break

        for current_business in business_current_page_list:
            current_business.click()
            time.sleep(1.5)

            filtered_business = filter_business()
            if (filtered_business is not None):
                filtered_businesses.append(filtered_business) 


    file_results = initialize_results_file()  
    write_results_file(file_results, filtered_businesses)    

if (argc != 2):
    exit(1)
else:
    URL = sys.argv[1]
    main()
    teardown(driver)

