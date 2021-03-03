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
etNetUrl = 'http://www.etnet.com.hk/www/tc/stocks/realtime/quote.php?code='
aasUrl = 'http://www.aastocks.com/tc/mobile/quote.aspx?symbol='
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

def etNetpageLoading(record):
	pageUrl = etNetUrl + record[0]
	stockNumber = int(record[0])
	driver = getDriver()
	driver.get(pageUrl) #open website with headless webdriver
	refreshButton = driver.find_element_by_id("StkQuoteRefresh") #locate the refresh button to extract data
	refreshButton.click()
	sleep(0.75) #sleep for 0.75s to wait for webpage refresh
	sauce = bs(driver.page_source, 'html.parser') #pass the source page to BeautifulSoup
	result = etNetscarping(sauce, stockNumber)
	return result

def aaspageLoading(record):
	pageUrl = aasUrl + record[0]
	stockNumber = int(record[0])
	driver = getDriver()
	driver.get(pageUrl) #open website with headless webdriver
	refreshButton = driver.find_element_by_class_name("btn_go") #locate the refresh button to extract data
	refreshButton.click()
	sleep(0.75) #sleep for 0.75s to wait for webpage refresh
	sauce = bs(driver.page_source, 'html.parser') #pass the source page to BeautifulSoup
	result = aasscarping(sauce, stockNumber)
	return result

def etNetscarping(sauce, number):
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

def aasscarping(sauce, number):
	global count
	count += 1
	print('{0} Page Taken'.format(count))
	errorType = None
	try:
		quoteOverview = sauce.find("div", {"id":"cphContent_pQuoteDetail"}) #locating the wrap box for the data
		quoteTable = quoteOverview.find("table", {"class":"quote_table"})
		td = quoteTable.find_all("td")
		try:
			overViews = td[1]
			overViewsValues = td[1].find_all("span")
			price = overViewsValues[2].text.strip()
			change = overViewsValues[3].text.strip()
			changePercent = overViewsValues[4].text.strip()

			highLowWrap = td[1].find_all("div")[3]
			highLow = highLowWrap.text.strip().split()[1]
			low, high = highLow.split('-')

			volumn = td[7].text.strip()[3:]
			boardLot = td[8].text.strip()[4:]
			turnover = td[9].text.strip()[4:]
			peRatio = td[10].text.strip()[7:]
			precentYld = td[11].text.strip()[4:]
			eps = td[13].text.strip()[5:]
			mktCap = td[14].text.strip()[2:]

			yearWrap = quoteOverview.find("div", {"id":"cphContent_p52Week"})

			yearHighLow = yearWrap.text.strip()[5:].split()
			yearLow = yearHighLow[0]
			yearHigh = yearHighLow[2]
		except IndexError:
			return [number, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'Index']
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
			etNetresult = tPool.map(etNetpageLoading, stockRecords[:20])
			#generate log files
			etNetlogFilePath = r'ETNet Log Files/' + strftime("%m%d%H%M", currentTime) + r'_etnet_log.txt'
			etNetlogFile = open(etNetlogFilePath, 'w', encoding = 'utf-8')
			for items in etNetresult:
				etNetlogFile.write(str(items) + '\n')
			etNetlogFile.close()

			#parallel run pageLoading function
			aasresult = tPool.map(aaspageLoading, stockRecords[:20])
			#generate log files
			aaslogFilePath = r'AAS Log Files/' + strftime("%m%d%H%M", currentTime) + r'_AAS_log.txt'
			aaslogFile = open(aaslogFilePath, 'w', encoding = 'utf-8')
			for items in aasresult:
				aaslogFile.write(str(items) + '\n')
			aaslogFile.close()

			print("Used Time:", time()-startTime)
			print("Current Time:", strftime("%H%M%S", localtime()))
			#if runtime for one trial takes over 60s, add sleep time so the program would restart in the next minute
			sleepTime = 60 - (time() - startTime)
			if sleepTime > 0:
				print("About to sleep for ", sleepTime)
				sleep(sleepTime)
	except KeyboardInterrupt:
		print("Terminaing...")
		try:
			#terminating possible opened log file
			etNetlogFile.close()
		except:
			pass

		try:
			#terminating possible opened log file
			aaslogFile.close()
		except:
			pass

	#terminating all drivers
	for a in driverLog:
		try:
			a.close()
			a.quit()
		except:
			pass
