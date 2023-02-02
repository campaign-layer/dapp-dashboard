# replit bounties fetch

import time

import pandas as pd

from urllib import request
from bs4 import BeautifulSoup
from selenium import webdriver

SCROLL_PAUSE_TIME = 2.0

driver = webdriver.Firefox()
driver.get("https://replit.com/bounties")

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")
for i in range(1, 101):
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1000);")
    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)
    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    # if new_height == last_height:
    #     break
    last_height = new_height
    print(last_height, new_height)

html_source = driver.page_source
with open('replit_bounties_all_raw_html.txt', 'w') as f:
	f.write(html_source)