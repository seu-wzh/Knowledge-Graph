import re
import sys
import time
import yaml
import random
from selenium import webdriver
from selenium.webdriver import EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class WikiCrawler(object):

    def __init__(self, verbose:bool=False) -> None:
        options = EdgeOptions()
        options.add_argument('--start-maximized' if verbose else '--headless')
        self.driver = webdriver.Edge(options)
        self.action = ActionChains(self.driver)
        self.url = 'https://baike.baidu.com/'
        self.patten = re.compile('^.*（(.*)），')
        self.driver.get(self.url)
        time.sleep(random.uniform(0.5, 1.5))

    def crawl_wiki_data(self, medicine:str) -> str:
        inputbox = self.driver.find_element(By.CLASS_NAME, 'searchInput')
        inputbox.send_keys(medicine, Keys.ENTER)
        time.sleep(random.uniform(0.5, 1.5))
        if 'none' in self.driver.current_url:
            self.driver.get(self.url)
            time.sleep(random.uniform(0.5, 1.5))
            return None
        try:
            sentence = self.driver.find_element(By.CLASS_NAME, 'lemmaSummary_lWfxV').text
            title = self.driver.find_element(By.CLASS_NAME, 'lemmaTitle_EXGUR').text
            if title != medicine:
                alias = title
            else:
                alias = self.patten.search(sentence)
                alias = alias.group(1) if alias else None
        except:
            alias = None
        finally:
            inputbox = self.driver.find_element(By.CLASS_NAME, 'searchInput')
            inputbox.send_keys(Keys.CONTROL, 'a', Keys.BACKSPACE)
            return alias

if __name__ == '__main__':
    with open(sys.argv[1]) as stream:
        config = yaml.load(stream, yaml.Loader)
    with open(config['dict']) as f:
        medicine = f.read().splitlines()
    crawler = WikiCrawler()
    try:
        with open(config['alias'], mode='w') as f:
            for name in medicine:
                alias = crawler.crawl_wiki_data(name)
                if alias is not None:
                    f.write(f'{name},{alias}\n')
    except:
        input('something went wrong, press enter to continue:')