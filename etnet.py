from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from multiprocessing.pool import ThreadPool
from bs4 import BeautifulSoup as bs
import threading
from os import getpid
from time import time, sleep, localtime, strftime

#global variables
cDriverPath = 'chromedriver.exe' #please change to apporiate version of chromedriver from https://chromedriver.chromium.org/downloads
stockPath = 'stock_list.txt'
url = 'http://www.etnet.com.hk/www/tc/stocks/realtime/quote.php?code='
threadLocal = threading.local()
count = 0
driverLog = []
logFile = None

def getDriver():
	#generate new webdriver if no exitisting driver
	global driverLog
	driver = getattr(threadLocal, 'driver', None)
	if driver == None:
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--disable-gpu')
		driver = webdriver.Chrome(cDriverPath, options=chrome_options)
		setattr(threadLocal, 'driver', driver)
		driverLog.append(driver) #log down all driver in use to terminate while program terminates
	return driver

def pageLoading(record):
	pageUrl = url + record[0]
	stockNumber = int(record[0])
	driver = getDriver()
	driver.get(pageUrl) #open website with headless webdriver
	refreshButton = driver.find_element_by_id("StkQuoteRefresh") #locate the refresh button to extract data
	refreshButton.click()
	sleep(0.75) #sleep for 0.75s to wait for webpage refresh
	sauce = bs(driver.page_source, 'html.parser') #pass the source page to BeautifulSoup
	result = scarping(sauce, stockNumber)
	return result

def scarping(sauce, number):
	global count
	count += 1
	print('{0} Page Taken'.format(count))
	errorType = None
	try:
		overViewTags = sauce.find("div", {"id":"StkDetailMainBox"}) #locating the wrap box for the data
		price = overViewTags.find("span", {"class":"Price"}).text.strip()
		changeSet = overViewTags.find("span", {"class":"Change"}).text.split()
		try:
			change = changeSet[0]
			changePercent = changeSet[1][1:-1]
		except IndexError:
			print("Array!")
			print(changeSet, number)
			change, changePercent = 'NA'
			errorType = 'Index'
		overViewNumbers = [tag.text for tag in overViewTags.find_all("span", {"class":"Number"})]
		try:
			high = overViewNumbers[0]
			volumn = overViewNumbers[1]
			mktCap = overViewNumbers[4]
			low = overViewNumbers[5]
			turnover = overViewNumbers[6]
		except IndexError:
			high, volumn, mktCap, low, turnover = 'NA'
			errorType = 'Index'
		breakDownTags = sauce.find("div", {"id":"StkList"})
		breakDownNumbers = [tag.text for tag in breakDownTags.find_all("li", {"class":"value"})]
		try:
			yearHigh = breakDownNumbers[11]
			yearLow = breakDownNumbers[13]
			boardLot = breakDownNumbers[12]
			peRatio = breakDownNumbers[18].split('/')[0]
			eps = breakDownNumbers[22].split()[1]
			precentYld = breakDownNumbers[20].split('/')[0]
		except IndexError:
			yearHigh, yearLow, boardLot, peRatio, eps, precentYld = 'NA'
			errorType = 'Index'
	except AttributeError:
		return [number, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'Attribute']
	return [number, price, high, low, change, changePercent, volumn, turnover, peRatio, boardLot, mktCap, eps, precentYld, yearHigh, yearLow, errorType]

if __name__ == "__main__":
	#open the stockFile
	stockFile = open(stockPath, 'r', encoding = 'utf-8')
	stockRecords = []
	for line in stockFile:
		stockRecords.append(line.strip('\n').split(','))
	stockFile.close()
	#multiprocessing
	tPool = ThreadPool(10)
	try: #try for catching Crtl-C for termination
		while True:
			print("Start")
			startTime = time()
			currentTime = localtime()
			#parallel run pageLoading function
			result = tPool.map(pageLoading, stockRecords[:20])
			#generate log files
			logFilePath = r'ETNet Log Files/' + strftime("%m%d%H%M", currentTime) + r'_etnet_log.txt'
			logFile = open(logFilePath, 'w', encoding = 'utf-8')
			for items in result:
				logFile.write(str(items) + '\n')
			logFile.close()
			print("Used Time:", time()-startTime)
			print("Current Time:", strftime("%H%M%S", localtime()))
			#if runtime for one trial takes over 60s, add sleep time so the program would restart in the next minute
			sleepTime = 60 - (time() - startTime)
			while sleepTime < 0:
				sleepTime += 60
			print("About to sleep for ", sleepTime)
			sleep(sleepTime)
	except KeyboardInterrupt:
		print("Terminaing...")
		try:
			#terminating possible opened log file
			logFile.close()
		except:
			pass

	#terminating all drivers
	for a in driverLog:
		try:
			a.close()
			a.quit()
		except:
			pass
