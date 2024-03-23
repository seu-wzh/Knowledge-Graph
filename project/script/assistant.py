import re
import sys
import time
import yaml
import random
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver import EdgeOptions
from selenium.webdriver.common.by import By

class AssistantCrawler(object):

    def __init__(self, verbose:bool=False) -> None:
        options = EdgeOptions()
        options.add_argument('--start-maximized' if verbose else '--headless')
        self.driver  = webdriver.Edge(options)
        self.burl    = 'https://drugs.dxy.cn'
        self.url     =  self.burl + '/pc/search?keyword={}'
        self.pattern = {'alias':      re.compile('^[^（]*（(.*)）\s'), 
                        'firm':       re.compile('厂商：<span>(.*)</span>'), 
                        'indication': re.compile('^适应症：(.*)')}

    def sign_in(self, usrname:str, password:str) -> None:
        self.driver.get(self.burl)
        time.sleep(random.uniform(1.5, 2.5))
        button = self.driver.find_element(By.XPATH, '//*[@id="J_header"]/div/div')
        button.click()
        time.sleep(random.uniform(1.5, 2.5))
        button = self.driver.find_element(By.XPATH, '//*[@id="user"]/div[1]/div[3]/label/input')
        button.click()
        time.sleep(random.uniform(1.5, 2.5))
        usrbox = self.driver.find_element(By.XPATH, '//*[@id="username"]')
        usrbox.send_keys(usrname)
        time.sleep(random.uniform(1.5, 2.5))
        passwd = self.driver.find_element(By.XPATH, '//*[@id="user"]/div[1]/div[1]/div[1]/div[2]/input')
        passwd.send_keys(password)
        time.sleep(random.uniform(1.5, 2.5))
        button = self.driver.find_element(By.XPATH, '//*[@id="user"]/div[1]/div[4]/button')
        button.click()
        input('please complete the authentication by yourself:')

    def extract_alias(self, medicine:str) -> str:
        try:
            self.driver.get(self.url.format(medicine))
            time.sleep(random.uniform(5.5, 7.5))
            block = self.driver.find_element(By.CLASS_NAME, 'DrugsPcItem_drugs-item__8pCiY')
            alias = block.find_element(By.CLASS_NAME, 'DrugsPcItem_drugs-item-name__nufpq')
            firm  = block.find_element(By.CLASS_NAME, 'DrugsPcItem_drugs-item-cnName__fZjeE')
            alias = self.pattern['alias'].search(alias.text).group(1)
            firm  = self.pattern['firm'].search(firm.get_attribute('outerHTML')).group(1)
            return None if ((medicine in alias) or (alias in firm)) else alias
        except:
            input('something goes wrong, please have a check:')
            return None

    def extract_indication(self, medicine:str) -> str:
        try:
            self.driver.get(self.url.format(medicine))
            time.sleep(random.uniform(7.5, 9.5))
            block = self.driver.find_element(By.CLASS_NAME, 'DrugsPcItem_drugs-item__8pCiY')
            hlink = block.find_element(By.CLASS_NAME, 'DrugsPcItem_link__yoWUS')
            hlink = hlink.get_attribute('href')
            self.driver.get(hlink)
            time.sleep(random.uniform(7.5, 9.5))
            sections = self.driver.find_elements(By.CLASS_NAME, 'page_item__3NVRC ')
            for section in sections:
                if section.get_attribute('data-menu-anchor') == '适应症':
                    indication = section.find_element(By.CLASS_NAME, 'page_content__zHHQZ')
                    break
            return indication.text
        except:
            input('something goes wrong, please have a check:')
            return None

if __name__ == '__main__':
    with open(sys.argv[1]) as stream:
        config = yaml.load(stream, yaml.Loader)
    crawler = AssistantCrawler(verbose=True)
    crawler.sign_in(config['usr'], config['passwd'])

    # with open(config['dict']) as f:
    #     medicine = f.read().splitlines()
    # alias_map = dict()
    # for mention in tqdm(medicine, desc='medicine', leave=False):
    #     alias = crawler.extract_alias(mention)
    #     if alias is not None:
    #         alias_map[mention] = alias
    # with open(config['alias'], 'w') as f:
    #     for mention, alias in alias_map.items():
    #         f.write(f'{mention},{alias}\n')

    with open(config['alias']) as f:
        medicine = f.read().splitlines()
    medicine = [entry.split(',')[0] for entry in medicine]
    indication = []
    for mention in tqdm(medicine, desc='medicine', leave=False):
        indication.append(crawler.extract_indication(mention))
    df = {'medicine': medicine, 'indication': indication}
    pd.DataFrame(df).to_excel(config['indication'])