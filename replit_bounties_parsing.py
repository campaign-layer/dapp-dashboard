# replit bounties parsing

import json
import pandas as pd
from bs4 import BeautifulSoup

raw_data_file = 'replit_bounties_all_raw_html.txt'
json_file = 'replit_bounties_info.json'
csv_file = 'replit_bounties_info.csv'

item_html = ['li', {'class':'1obxggb'}]
title_html = ['h3', {"class":"css-1kgy7vt"}]
desc_html = ['span', {"class":"css-o4584k"}]
# can define more fields here to grab them

with open(raw_data_file, 'r') as file:
    full_html = file.read()

soup = BeautifulSoup(full_html, 'html.parser')
result = soup.find_all(item_html[0], item_html[1])

items = []
for r in result:
	item = {}
	item['title'] = r.find(title_html[0], title_html[1]).text
	item['description'] = r.find(desc_html[0], desc_html[1]).text
	# can add other fields here once you define the html of the field above
	items.append(item)

with open(json_file, 'w') as f:
	json.dumps(items, f)

df = pd.read_json(json_file)
df.to_csv(csv_file, index=None)