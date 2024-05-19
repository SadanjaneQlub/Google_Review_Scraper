# Imports
import time
import pandas as pd
import numpy as np
import json
from tqdm.auto import tqdm
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from bs4 import BeautifulSoup as Soup
import csv
import requests

options = webdriver.ChromeOptions()
options.add_argument("start-maximized") # start the window maximized
options.add_argument("--ignore-certificate-errors")

#pre built location list 
location_df = pd.read_csv('google_place_ids_clean.csv')

#Calling google maps API
#Google Place API(New) Headers
headers = {"Content-Type": "application/json",
           "X-Goog-Api-Key":"#", #API Key 
           "X-Goog-FieldMask": "id,displayName,googleMapsUri" #attributes from the API
          #  "X-Goog-FieldMask": "*"
          }

restaurants_list = []

k = 0

# for i in tqdm(location_df['google_place_id']):
for index, row in tqdm(location_df.iterrows(), total=len(location_df)):
    google_place_id = row['google_place_id']
    restaurant_unique = row['restaurant_unique']
    # end_point = f'https://places.googleapis.com/v1/places/{i}'
    end_point = f'https://places.googleapis.com/v1/places/{google_place_id}'
    response = requests.get(url = end_point , headers = headers)

    #If API call failed
    if response.status_code!=200:
        print("API call unsuccessful: Error",response.status_code,"-",response.reason , f"for G-Id - {i}" )
        continue

    try:
      site_response = json.loads(response.content)
    except:
      print('failed')
      continue #If this process failed. Continue from the begining
        
    restaurant_dictionary = {
            'Google_Place_ID': site_response.get('id'),
            'Name' : site_response['displayName']['text'],
            'Unique' : restaurant_unique,
            'URi' : site_response.get('googleMapsUri')
        }
    restaurants_list.append(restaurant_dictionary)
    # break

    k = k+1
    if k == 3:
        break
    
restaurant_df = pd.DataFrame.from_dict(restaurants_list)   

def find_review(text):
    start_identifier = '<span class="wiI7pd">'
    end_identifier = '</span>'
    search_start = text.find(start_identifier) + len(start_identifier)
    search_end = text.find(end_identifier, search_start)
    return text[search_start:search_end]

def find_date(text):
    start_identifier = '<span class="rsqaWe">'
    end_identifier = '</span>'
    search_start = text.find(start_identifier) + len(start_identifier)
    search_end = text.find(end_identifier, search_start)
    return text[search_start:search_end]

def find_author(text):
    start_identifier = 'aria-label="'
    end_identifier = '"'
    search_start = text.find(start_identifier) + len(start_identifier)
    search_end = text.find(end_identifier, search_start)
    return text[search_start:search_end]

initial_load_time = 2
scroll_pause_time = 3
restaurants_review_list = []

chrome_path = 'chromedriver.exe'
service = Service(chrome_path)
driver = webdriver.Chrome(service=service)

# Set URL, initial_load_time and scroll_pause_time
# for i in tqdm(restaurant_df['URi']):
for index, row in tqdm(restaurant_df.iterrows(), total=len(restaurant_df)):
    
    url = row['URi']
    name = row['Name']
    unique = row['Unique']
    
    driver.get(url)
    time.sleep(initial_load_time)

    button = driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[3]/div/div/button[2]/div[2]')
    button.click()

    ###################################
    review_pane = driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]')  # Adjust selector if needed
    screen_height = driver.execute_script("return arguments[0].scrollHeight", review_pane)
    print(screen_height)

    # Scroll down
    i = 1
    while True:
        time.sleep(scroll_pause_time)
        driver.execute_script("arguments[0].scrollTo(0, " + str(screen_height) + " * " + str(i) + ");", review_pane)
        i += 1
        time.sleep(scroll_pause_time)
        scroll_height = driver.execute_script("return arguments[0].scrollHeight", review_pane)
        if screen_height * i > scroll_height:
            break

    ###################################
        
     # Create a beautiful soup object that parses the html and has useful methods for reading the text
    soup = Soup(driver.page_source, 'html.parser')
    driver.quit()
    type(soup)  
    
    a_tag_class = 'jftiEf'  #class with content
    
    restaurants_html = [str(x) for x in soup.find_all(class_ = a_tag_class)]

    
    for restaurant in restaurants_html:

        author = find_author(restaurant)
        review = find_review(restaurant)
        createdAt = find_date(restaurant)
        
        restaurant_dictionary = {
            'Res_Name' : name,
            'Res_Unique' : unique,
            'author': author,
            'review' : review,
            'createdAt': createdAt 
        }
        restaurants_review_list.append(restaurant_dictionary)
    
restaurant_df_final = pd.DataFrame.from_dict(restaurants_review_list)
restaurant_df_final