import sys
import requests
import json
import put_database as pdb
from bs4 import BeautifulSoup
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

# Get all products link from searchLink with keyword on page #
# amount : current products link fetched
def getProductLink(searchLink, keyword, page, amount):
    url = searchLink + str(page) + '&search%5Bhashtag%5D=&search%5Bkeywords%5D=' + keyword 
    browser.get(url)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    urls = []
    for x in soup.findAll('a', {'class' : 'product__name' }):
        link = x.get('href')[0:x.get('href').rfind('?')]
        if (link not in urls ):
            urls.append(link)
            amount += 1
            if amount==sys.argv[2]:
                break
    if amount==sys.argv[2]: # If limit exceeded
        return urls
    elif (soup.find('a', {'class' : 'next_page'})): # If next search page exist
        return urls + getProductLink(searchLink, keyword, page+1, amount)
    else:
        return urls

# Get product data from an url
def getProductData(url):
    try:
        browser.get(url)
        soup = BeautifulSoup(browser.page_source, 'html.parser')

        # Get products name, id, and description
        name = soup.find('h1', {'class' : 'c-product-detail__name'}).get_text()
        desc_div = soup.find('div', {'class' : 'qa-pd-description'})
        desc = desc_div.find('p').get_text()
        desc = desc.encode('ascii', 'ignore')
        price = soup.find('div', {'class' : 'c-product-detail-price'})['data-reduced-price']
        product_id = soup.find('input', {'name':'item[product_id]'})['value']
        try:
            sold = int(soup.find('dd', {'class' : 'qa-pd-sold-value'}).get_text())
        except:
            sold = 0

        # Get seller name, id, link, and location
        try:
            if soup.find('div', {'class' : 'u-txt--small u-txt--small-upcase u-mrgn-bottom--2'}).get_text() != "Pelapak":
                seller_id = soup.find('div', {'class' : 'js-product-detail'})['data-seller-id']
                seller = soup.find('a', {'class' : 'qa-seller-name'})['title']
                seller_link = soup.find('a', {'class' : 'qa-seller-name'})['href']
                seller_username = seller_link[seller_link.rfind('/')+1:]
                seller_location = soup.find('span', {'class' : 'qa-seller-location'}).find('a').get_text()
            else:
                seller_id = soup.find('div', {'class' : 'js-product-detail'})['data-seller-id']
                soup_links=soup.findAll('h2')

                for n in soup_links :
                    seller = soup.find('a', {'class' : 'u-txt--base u-txt--upcase u-fg--black u-txt--bold'}).get_text()            
                    seller_link = soup.find('a', {'class' : 'u-txt--base u-txt--upcase u-fg--black u-txt--bold'})['href']
                seller_username = seller_link[seller_link.rfind('/')+1:]
                seller_location = soup.find('span').find('a',{'class' : 'u-fg--ash-dark'}).get_text()
        except:
            seller_id = soup.find('div', {'class' : 'js-product-detail'})['data-id']
            soup_links=soup.findAll('h2')

            for n in soup_links :
                seller = soup.find('a', {'class' : 'c-user-identification__name qa-seller-name'}).get_text()            
                seller_link = soup.find('a', {'class' : 'c-user-identification__name qa-seller-name'})['href']
            seller_username = seller_link[seller_link.rfind('/')+1:]
            seller_location = soup.find('span',{'class' : 'c-user-identification-location__txt qa-seller-location'}).find('a').get_text()

        # Take screenshot on the page and save it
        image = product_id + '.png'
        img_dir = '/var/www/html/dev/screenshots/bukalapak/products/' + image
        image = '["' + image + '"]'
        browser.save_screenshot(img_dir)

        try:
            print("input name "+ sys.argv[6] )
            records = pdb.get_log(sys.argv[6])
            for row in records:
                print('test')
                input_name = row[10]
                log_id = sys.argv[6]
            print("input success")
        except :
            input_name =  ""
            log_id = 0

        productData = {
            'keyword' : sys.argv[1],
            'source' : 'bukalapak' ,
            'product_name' : name,
            'product_id' : product_id,
            'url' : url,
            'store_id' : seller_id,
            'store_name' : seller,
            'store_link' : mainlink + seller_link,
            'owner_id' : seller_id,
            'owner_name' : seller,
            'owner_username' : seller_username,
            'owner_link' : mainlink + seller_link,
            'address' : seller_location,
            'desc' : desc,
            'image' : image,
            'deputy' : deputi,
            'bagian' : bagian,
            'contact' : '',
            'price' : price,
            'sold' : sold,
            'input_name' : input_name,
            'log_id' : log_id
        }
        return productData
    except:
        return None

# Get all products data from list of urls
# Return list of productData
def getAllProductData(urls):
    productDatas = []
    for url in urls:
        productData = getProductData(url)
        if (productData is not None):
            productDatas.append(productData)
    return productDatas

# Get all store data from list of productData
def getAllStoreData(productDatas):
    storeIdlist = []
    storeDatas = []
    for product in productDatas :
        if product['store_id'] not in storeIdlist:
            browser.get(product['owner_link'])
            try:
                element = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.c-tab__content__body.u-pad-h--4.u-bg--sand-light.merchant-page__note"))
                )
                soup = BeautifulSoup(browser.page_source, 'html.parser')
                desc_all = soup.find('div', class_ = 'c-tab__content__body u-pad-h--4 u-bg--sand-light merchant-page__note')
                
                p_all = desc_all.find_all('p')
        
                desc = ''
                x = 1
                for d in p_all:
                    desc = desc + d.get_text()
                    if(x < len(p_all)):
                        desc = desc + ' '

                desc = desc.encode('ascii', 'ignore')
            except TimeoutException as e:
                # print('hello '+e)
                desc = ''
                # browser.quit()
            
            # Take screenshot on the page and save it
            image = product['store_id'] + '.png'
            store_dir = '/var/www/html/dev/screenshots/bukalapak/stores/' + image
            owner_dir = '/var/www/html/dev/screenshots/bukalapak/owners/' + image
            image = '["' + image + '"]'
            browser.save_screenshot(store_dir)
            browser.save_screenshot(owner_dir)

            storeData = {
                'source' : 'bukalapak',
                'owner_id' : product['owner_id'],
                'owner_name' : product['owner_name'],
                'owner_username' : product['owner_username'],
                'owner_link' : product['owner_link'],
                'store_id' : product['store_id'],
                'store_name' : product['store_name'],
                'store_link' : product['store_link'],
                'address' : product['address'],
                'desc' : desc,
                'image' : image,
                'contact' : ''
            }
            storeDatas.append(storeData)
            storeIdlist.append(product['store_id'])

    return storeDatas
#&search_source=omnisearch_organic&source=navbar&utf8=%E2%9C%93
link = 'https://www.bukalapak.com/products/s?from=omnisearch&page='
mainlink = 'https://www.bukalapak.com'

if (len(sys.argv) < 3) :
    print('USAGE : .py "<keyword>" <Max Amount> <deputy> <bagian unit> <crawl_id>')
    exit()

sys.argv[2] = int(sys.argv[2])

deputi = sys.argv[3]

bagian = sys.argv[4]

options = Options()
#options.headless = True
options.add_argument('--no-sandbox')
browser = webdriver.Chrome(executable_path="/home/oetomo/pGrabber/chromedriver",options=options)

# try:
print("test masuk")
urls = getProductLink(link, sys.argv[1],1, 0)
productDatas = getAllProductData(urls)
storeDatas = getAllStoreData(productDatas)

print(productDatas)

browser.quit()
