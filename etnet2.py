from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from multiprocessing import Pool
from bs4 import BeautifulSoup
import threading
from os import getpid

cDriverPath = r'/Users/chunho/Documents/GitHub/HKET-Program-Exercise/chromedriver'
stockPath = 'stock_list.txt'
url = 'http://www.etnet.com.hk/www/tc/stocks/realtime/quote.php?code='
threadLocal = threading.local()

def getDriver():
	print("getDriver", getpid())
	#driver = getattr(threadLocal, 'driver', None)
	#if driver == None:
	chrome_options = Options()
	#chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-gpu')
	driver = webdriver.Chrome(cDriverPath, options=chrome_options)
	#setattr(threadLocal, 'driver', driver)
	print("Got", getpid())
	return driver

def pageLoading(record):
	print("PageLoading", getpid(), record[0])
	pageUrl = url + record[0]
	stockNumber = int(record[0])
	driver = getDriver()
	print(pageUrl)
	driver.get(pageUrl)
	print("Page Get", stockNumber)
	refreshButton = driver.find_element_by_id("StkQuoteRefresh")
	refresh_button.click()
	print("Page Refreshed", stockNumber)
	sauce = bs(chrome.page_source)
	result = scarping(sauce, stockNumber)
	return result

def scarping(sauce, number):
	print(number)
	overViewTags = sauce.find("div", {"id":"StkDetailMainBox"})
	price = overViewTags.find("span", {"class":"Price"}).text.strip()
	changeSet = overViewTags.find("span", {"class":"Change"}).text.split() 
	change = changeSet[0]
	changePercent = changeSet[1][1:-1]
	overViewNumbers = [tag.text for tag in overViewTags.find_all("span", {"class":"Number"})]
	high = overViewNumbers[0]
	volumn = overViewNumbers[1]
	mktCap = overViewNumbers[4]
	low = overViewNumbers[5]
	turnover = overViewNumbers[6]
	breakDownTags = sauce.find("div", {"id":"StkList"})
	breakDownNumbers = [tag.text for tag in breakDownTags.find_all("li", {"class":"value"})]
	yearHigh = breakDownNumbers[11]
	yearLow = breakDownNumbers[13]
	boardLot = breakDownNumbers[12]
	peRatio = breakDownNumbers[18].split('/')[0]
	eps = breakDownNumbers[22].split()[1]
	precentYld = breakDownNumbers[20].split('/')[0]
	return [number, price, high, low, change, changePercent, volumn, turnover, peRatio, boardLot, mktCap, eps, precentYld, yearHigh, yearLow]

if __name__ == "__main__":
	stockFile = open(stockPath, 'r', encoding = 'utf-8')
	stockRecords = []
	for line in stockFile:
		stockRecords.append(line.strip('\n').split(','))
	result = Pool(5).map(pageLoading, stockRecords[:100])
	for items in result:
		print(items)