from io import IncrementalNewlineDecoder
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from constant import *
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import yaml
import time
import os
import shutil
import glob
from pyvirtualdisplay import Display
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
'''
bestbuy = 0
lowes = 1
almo = 2
costco = 3
'''
URLS_INDEX = 0

bestbuy_page_begin = 7314+1
bestbuy_page_end = 7402

lowes_page_begin = 6458+1
lowes_page_end = 6505

almo_page_begin = 4823+1
almo_page_end = 4845

costco_page_begin = 18877+1
costco_page_end = 19226

item_running = []
item_without_money = []
item_cancel = []
text_not_found = []

def manifest_download(driver, path):
    os.chdir(path)
    button = driver.find_element(By.ID, "manifest-download-btn-top")
    button.click()
def move_manifest(folder_path, market, id):
    path = r"C:/Users/lsy/Downloads/"
    extension = '\*csv'
    os.chdir(path)
    files = glob.glob(path+extension)
    result = max(files, key=os.path.getctime) 
    name = market+"_"+str(id)+".csv"
    os.rename(result, name)
    shutil.move(path+name, folder_path)

def driver_login(driver):
    conf = yaml.safe_load(open('C:/Users/lsy/Desktop/WebApps/B_Stock_Auction/login.yml'))
    username = conf['user']['email']
    password = conf['user']['password']
    driver.get(login_URLS[URLS_INDEX])
    time.sleep(2)
    driver.find_element("id", 'loginId').send_keys(username)
    driver.find_element("id", 'password').send_keys(password)
    driver.find_element("xpath","//button[@type='submit']").click()
    time.sleep(1)

def getDate(soup):
    return soup.find('span', id="auction_end_time").getText()

def createFolder(id, market):
    path = r"C:/Users/lsy/Desktop/WebApps/B_Stock_Auction/"+market+"_"+str(id)+"/"
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    return path

def reverse(s):
    str = ""
    for i in s:
        str = i + str
    str = str.strip()
    return str

def getTitle(soup):
    try:
        try:
            title = soup.find('h1', itemprop="name").getText()
        except:
            try:
                title = soup.find('div', class_="product-name").getText()
            except Exception as e:
                print("error in getTitle")
                print(e)
                return "none"
        if title.find("$") == -1:
            return "noMoney"
        if  URLS_INDEX == 3:
            open = "("
            close = ")"
            start = title.index(open)
            end = title.index(close)
            global manifest
            manifest = title[start+1:end]
        state = ""
        city = ""
        price = ""
        condition = ""
        units = ""
        type = ""
        title = title.lower()
        title = title.replace(", msrp", "")
        title = title.replace(", ext. retail", "")
        title = title.replace(", retail", "")
        title = title.replace("retail", "")
        newtitle = ""
        invalid = False
        
        for idx, val in enumerate(title):
            if val == '(':
                invalid = True
            elif val == ')':
                invalid = False
            if not invalid:
                newtitle += val
        newtitle = newtitle.replace(")", "")
        if newtitle.find("units"):
            newtitle = newtitle.replace("units", "").strip()
        elif newtitle.find("unit"):
            newtitle = newtitle.replace("unit", "").strip()
        elif newtitle.find("sets"):
            newtitle = newtitle.replace("sets", "").strip()
        elif newtitle.find("set"):
            newtitle = newtitle.replace("set", "").strip()
        newtitle = newtitle.replace(", ,", ",")
        newtitle = newtitle.replace("  ", " ")
        newtitle = newtitle.replace(" ","") 
        comma_counter = 0
        for c in reversed(newtitle):
            if comma_counter == 2 and c == '$':
                comma_counter += 1
                continue
            if c == ',':
                if comma_counter == 0 and len(state) != 0:
                    comma_counter += 1
                elif comma_counter == 1 and len(city) != 0:
                    comma_counter += 1
                elif comma_counter == 3 and len(condition) != 0:
                    comma_counter += 1
                elif comma_counter == 4 and len(units) != 0:
                    comma_counter += 1
            if comma_counter == 0:
                state += c
            elif comma_counter == 1:
                city += c
            elif comma_counter == 2:
                price += c
            elif comma_counter == 3:
                condition += c
            elif comma_counter == 4:
                units += c
            elif comma_counter == 5:
                type += c
        state = reverse(state)
        city = reverse(city)
        price = reverse(price)
        condition = reverse(condition)
        units = reverse(units)
        type = reverse(type)
        if URLS_INDEX == 2:
            temp = units
            units = condition
            condition = temp
        condition = condition.replace(",","")
        city = city.replace(",","")
        price = price.replace(",","")
        units = units.replace(",","")
        machine = type.replace(",","")
        kitchen = ['refrigerators','microwave','dishwashers', 'range','cooktop','freezers']
        laundry = ['washers', 'dryers', 'pedestals', 'stackable', 'styler','washTower']
        iskitchen = False
        isLaundry = False
        for k in kitchen:
            if machine.find(k) != -1:
                iskitchen = True
                break
        for l in laundry:
            if machine.find(l) != -1:
                isLaundry = True
                break
        if not iskitchen and not isLaundry:
            return "none"
        if isLaundry and iskitchen:
            return [state, city, price, units, "Mixed"]
        if isLaundry:
            return [state, city, price, units, "Laundry"]
        return [state, city, price, units, "Kitchen"]
    except Exception as e:
        print("error in getTitle")
    return []

def create_column_title(column_titles):
    d = {}
    for title in column_titles:
        d[title] = []
    return d
    
def auction_time_name(soup):
    return soup.find('span', id="auction_time_remaining").getText().strip()

def scriptDetail(soup, d, page):
    names = soup.find_all('script')
    if not names:
        text_not_found.append(page)
        return
    for i in range(25):
        string = str(names[len(names) - i - 1])
        if string.find('mixpanel.track') != -1:
            break;
    key = string.split('mixpanel.track')[1]
    elem = key.split(",")
    for ele in elem:
        try:
            ele = ele.strip()
            half = ele.split(":")
            for index in range(len(half)):
                text = half[index].replace('"', "")
                if text in titles:
                    name = half[1].strip()
                    name = name.replace('"',"")
                    d[text].append(name)
                    break
        except Exception as e:
            print(e)
            print("scriptDetail")
    return d

def get_pictures(soup, path):
    ul = soup.find('ul', {"class":"product-image-thumbs"})
    index = 0
    os.chdir(path)
    try:
        for li in ul.find_all('li'):
            imgLink = li.find('a')
            png_name = str(index)+".jpg"
            imgLink = imgLink.find('img')
            print("img link: " + imgLink['src'])
            r = requests.get(imgLink['src'])
            with open(png_name,"wb") as f:
                f.write(r.content)
            index += 1
    except Exception as e:
        print("index error: " + str(e) + str(index))
    return index

def move_picture(path, pic_len):
    for i in range(pic_len):
        png_name = str(i)+".jpg"
        old_dir = "C:/Users/lsy/Desktop/WebApps/B_Stock_Auction/"+png_name
        shutil.move(old_dir, path)

def get_webdriver():
    """Get whatever webdriver is availiable in the system.
    webdriver_manager and selenium are currently being used for this.
    Supported browsers:[Firefox, Chrome, Opera, Microsoft Edge, Internet Expolorer]
    Returns:
            a webdriver that can be used for scraping. Returns None if we don't find a supported webdriver.

    """
    chromdriverPath = 'C:/Users/lsy/Downloads/chromedriver_win32/chromedriver.exe'
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    s=Service(chromdriverPath)
    try:
        # driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=options)
        driver = webdriver.Chrome(service=s, options = options)
    except Exception:
        try:
            driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        except Exception:
            driver = None
    return driver

def start_crawling(page_begin, page_end, market):
    d = create_column_title(titles) 

    
    driver = get_webdriver()
    driver_login(driver)
    delay_wait = 5
    for page in range(page_begin, page_end):
        url = inventory_URLS[URLS_INDEX]+ str(page)
        try:
            driver.get(url)
            driver.implicitly_wait(delay_wait)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            auction_time_remain = auction_time_name(soup)
            if  auction_time_remain == "Auction canceled":
                item_cancel.append(page)
                continue
            elif auction_time_name(soup) != "Auction ended":
                item_running.append(page)
                continue
            titleName = getTitle(soup)
            if titleName == "none":
                item_cancel.append(page)
                continue
            elif titleName == "noMoney":
                item_without_money.append(page)
                continue
            folder_path = createFolder(page, market)
            os.chdir(folder_path)
            manifest_found = True
            if URLS_INDEX != 3:
                try:
                    manifest_download(driver, folder_path)
                except Exception as e:
                    manifest_found = False
                    print("No manifest Download available")
            else:
                file_path = file_path_1 + manifest + file_path_2    
                driver.get(file_path)
            get_pictures(soup, folder_path)
            time.sleep(2)
            if manifest_found: 
                move_manifest(folder_path, market, page)
            found = False
            WH = ""
            global states
            for state in states:
                if found == True:
                    break
                for i in range(len(states[state])):
                    if states[state][i] == titleName[0]:
                        WH = state
                        found = True
                        break
            d["warehouse"].append(WH)
            d["id"].append(page)  
            d["date"].append(getDate(soup))
            scriptDetail(soup, d, page)
            d["type"].append(titleName[-1])  
            d["city"].append(titleName[1])
            d["value_price"].append(titleName[2])
            d["units"].append(titleName[3])
            d["percentage"].append(str(round(float(d["current_price"][-1])/float(d["value_price"][-1]),4)))
        except Exception as e:
            print(str(page) + ". " + str(e)  + ". start_crawling")
    driver.close()
    return d

def run_file(page_start, page_end):
    
    os.chdir("C:/Users/lsy/Desktop/WebApps/B_Stock_Auction/")
    if URLS_INDEX == 0:
        market = "BESTBUY"
    elif URLS_INDEX == 1:
        market = "LOWES"
    elif URLS_INDEX == 2:
        market = "ALMO"
    elif URLS_INDEX == 3:
        market = "COSTCO"
    data = start_crawling(page_start, page_end, market)
    df = pd.DataFrame.from_dict(data, orient = 'index')
    df = df.transpose()
    file_csv = market + "_" + str(page_start) + "_" + str(page_end) +".csv"
    os.chdir("C:/Users/lsy/Desktop/WebApps/B_Stock_Auction/")
    df.to_csv(file_csv, index = False)
    

URLS_INDEX = 0
item_running = []
item_without_money = []
item_cancel = []
text_not_found = []
run_file(bestbuy_page_begin, bestbuy_page_end)
print("Running items: ", item_running)
print("No $ items: ", item_without_money)
print("Cancel items: ", item_cancel)
print("page broke: ", text_not_found)

item_running = []
item_without_money = []
item_cancel = []
text_not_found = []
URLS_INDEX = 1
run_file(lowes_page_begin, lowes_page_end)
print("Running items: ", item_running)
print("No $ items: ", item_without_money)
print("Cancel items: ", item_cancel)
print("page broke: ", text_not_found)

item_running = []
item_without_money = []
item_cancel = []
text_not_found = []
URLS_INDEX = 2
run_file(almo_page_begin, almo_page_end)
print("Running items: ", item_running)
print("No $ items: ", item_without_money)
print("Cancel items: ", item_cancel)
print("page broke: ", text_not_found)

item_running = []
item_without_money = []
item_cancel = []
text_not_found = []
URLS_INDEX = 3
run_file(costco_page_begin, costco_page_end)
print("Running items: ", item_running)
print("No $ items: ", item_without_money)
print("Cancel items: ", item_cancel)
print("page broke: ", text_not_found)