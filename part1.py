from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from multiprocessing.pool import ThreadPool
from bs4 import BeautifulSoup as bs
import threading
from os import getpid
from time import time, sleep, localtime, strftime
from selenium.webdriver.common.keys import Keys

#global variables
cDriverPath = 'chromedriver.exe' #please change to apporiate version of chromedriver from https://chromedriver.chromium.org/downloads
stockPath = 'stock_list.txt'
etNetUrl = 'http://www.etnet.com.hk/www/tc/stocks/realtime/quote.php?code=1'
aasUrl = 'http://www.aastocks.com/tc/mobile/quote.aspx?symbol=1'
ejUrl = 'https://stock360.hkej.com/quotePlus/1'
threadLocal = threading.local()
count = 0
driverLog = []
logFile = None

def getDriver():
	#generate new webdriver if no exitisting driver
	global driverLog
	etdriver = getattr(threadLocal, 'etdriver', None)
	if etdriver == None:
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--blink-settings=imagesEnabled=false')
		chrome_options.add_argument('--disable-gpu')
		chrome_options.add_argument("--log-level=3")
		etdriver = webdriver.Chrome(cDriverPath, options=chrome_options, service_log_path = 'NUL')
		etdriver.get(etNetUrl)
		setattr(threadLocal, 'etdriver', etdriver)
		driverLog.append(etdriver) #log down all driver in use to terminate while program terminates
	aasdriver = getattr(threadLocal, 'aasdriver', None)
	if aasdriver == None:
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--blink-settings=imagesEnabled=false')
		chrome_options.add_argument('--disable-gpu')
		chrome_options.add_argument("--log-level=3")
		aasdriver = webdriver.Chrome(cDriverPath, options=chrome_options)
		aasdriver.get(aasUrl)
		setattr(threadLocal, 'aasdriver', aasdriver)
		driverLog.append(aasdriver) #log down all driver in use to terminate while program terminates
	ejdriver = getattr(threadLocal, 'ejdriver', None)
	if ejdriver == None:
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--blink-settings=imagesEnabled=false')
		chrome_options.add_argument('--disable-gpu')
		chrome_options.add_argument("--log-level=3")
		ejdriver = webdriver.Chrome(cDriverPath, options=chrome_options)
		ejdriver.get(ejUrl)
		setattr(threadLocal, 'ejdriver', ejdriver)
		driverLog.append(ejdriver) #log down all driver in use to terminate while program terminates
	return [etdriver, aasdriver, ejdriver]

def driverInitialize(arg):
	drivers = getDriver()

def pagesScrapping(record):
	etdriver, aasdriver, ejdriver = getDriver()
	etResult = etNetpageLoading(record, etdriver)
	aasResult = aaspageLoading(record, aasdriver)
	ejResult = ejpageLoading(record, ejdriver)
	global count
	count += 1
	print('{0} Stock(s) Taken'.format(count))
	return [etResult, aasResult, ejResult]


def etNetpageLoading(record, driver):
	try:
		if driver.current_url.split('/')[2] != 'www.etnet.com.hk':
			driver.get(etNetUrl) #open website with headless webdriver if currently not opening etnet
	except IndexError:
		driver.get(etNetUrl)
	try:
		textbox = driver.find_element_by_id("quotesearch") #locate the textbox
		textbox.send_keys(Keys.CONTROL, 'a') #highlight all data
		textbox.send_keys(record[0]) #input stock number
	except:
		driver.get(etNetUrl[:-1] + record[0])
	button = driver.find_element_by_id("quotesearch_submit") #locate the refresh button to extract data
	button.click()
	sleep(0.75) #sleep for 0.75s to wait for webpage refresh
	currentTime = localtime()
	sauce = bs(driver.page_source, 'html.parser') #pass the source page to BeautifulSoup
	result = etNetscarping(sauce, int(record[0]))
	result.append(strftime("%H%M", currentTime))
	return result

def aaspageLoading(record, driver):
	try:
		if not driver.current_url.split('/')[2] == 'www.aastocks.com':
			driver.get(aasUrl) #open website with headless webdriver if currently not opening AAStock
	except IndexError:
		driver.get(aasUrl)
	textbox = driver.find_element_by_id("symbol") #locate the textbox
	textbox.send_keys(Keys.CONTROL, 'a') #highlight all data
	textbox.send_keys(record[0]) #input stock number
	button = driver.find_element_by_class_name("btn_go") #locate the refresh button to extract data
	button.click()
	sleep(0.75) #sleep for 0.75s to wait for webpage refresh
	currentTime = localtime()
	sauce = bs(driver.page_source, 'html.parser') #pass the source page to BeautifulSoup
	result = aasscarping(sauce, int(record[0]))
	result.append(strftime("%H%M", currentTime))
	return result

def ejpageLoading(record, driver):
	try:
		if not driver.current_url.split('/')[2] == 'stock360.hkej.com':
			driver.get(ejUrl) #open website with headless webdriver if currently not opening AAStock
	except IndexError:
		driver.get(ejUrl)
	textbox = driver.find_element_by_id("inputCode") #locate the textbox
	textbox.send_keys(Keys.CONTROL, 'a') #highlight all data
	textbox.send_keys(record[0]) #input stock number
	button = driver.find_element_by_id("submitLink") #locate the refresh button to extract data
	button.click()
	sleep(0.75) #sleep for 0.75s to wait for webpage refresh
	currentTime = localtime()
	sauce = bs(driver.page_source, 'html.parser') #pass the source page to BeautifulSoup
	result = ejscarping(sauce, int(record[0]))
	result.append(strftime("%H%M", currentTime))
	return result

def etNetscarping(sauce, number):
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
			yearHigh, yearLow, boardLot, peRatio, eps, precentYld = 'NA', 'NA', 'NA', 'NA', 'NA', 'NA'
			errorType = 'Index'
	except AttributeError:
		return [number, 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'Attribute']
	return [number, price, high, low, change, changePercent, volumn, turnover, peRatio, boardLot, mktCap, eps, precentYld, yearHigh, yearLow, errorType]

def aasscarping(sauce, number):
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

def ejscarping(sauce, number):
	errorType = None
	try:
		stockDetailWrap = sauce.find("div", {"class":"stockDetailWrap"}) #locating the wrap box for the data
		stockOverviews = stockDetailWrap.find("div", {"class":"quote"}).find_all("p")
		try:
			price = stockOverviews[1].text
			changeSet = stockOverviews[2].text.split()
			change = changeSet[0]
			changePercent = changeSet[1][1:-1]
			breakDownWrap = stockDetailWrap.find("div", {"class":"data"})
			breakDownSet = breakDownWrap.find_all("td")
			high = breakDownSet[3].text
			turnover = breakDownSet[5].text
			low = breakDownSet[9].text
			volumn = breakDownSet[11].text
			dataGP2 = stockDetailWrap.find("div", {"class":"dataGP2"})
			dataGP2Set = dataGP2.find_all("p")
			mktCap = dataGP2Set[0].text[2:]
			boardLot = dataGP2Set[1].text[4:]
			yearHigh, yearLow = dataGP2Set[9].text[5:].split(' - ')
			eps = dataGP2Set[10].text[9:]
			peRatio = dataGP2Set[11].text[10:]
			precentYld = dataGP2Set[13].text[6:] + '%'
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
	pool = ThreadPool(5)
	#preLoading of the webdriver
	pool.map(driverInitialize, [None for i in range(5)])
	try: #try for catching Crtl-C for termination
		while True:
			print("About to sleep for", 60 - localtime()[5])
			sleep(60 - localtime()[5]) #sleep till the start of next minute

			print("Start")
			startTime = time()
			currentTime = localtime()
			result = []
			#parallel run pageLoading function
			for i in range(int(len(stockRecords)/500)):
				if i != int(len(stockRecords)/500) - 1:
					partresult = pool.map(pagesScrapping, stockRecords[i*500 : (i+1)*500])
				else:
					partresult = pool.map(pagesScrapping, stockRecords[i*500 :])
				for items in partresult:
					result.append(items)
				for i in range(len(driverLog)):
					try:
						driverLog[i].quit()
						del driverLog[i]
					except:
						pass
				threadLocal = threading.local()

			
			#generate log files
			etNetlogFilePath = r'ETNet Log Files/' + strftime("%m%d%H%M", currentTime) + r'_etnet_log.txt'
			etNetlogFile = open(etNetlogFilePath, 'w', encoding = 'utf-8')
			for items in result:
				etNetlogFile.write(str(items[0]) + '\n')
			etNetlogFile.close()

			#generate log files
			aaslogFilePath = r'AAS Log Files/' + strftime("%m%d%H%M", currentTime) + r'_AAS_log.txt'
			aaslogFile = open(aaslogFilePath, 'w', encoding = 'utf-8')
			for items in result:
				aaslogFile.write(str(items[1]) + '\n')
			aaslogFile.close()

			#generate log files
			ejlogFilePath = r'HKEJ Log Files/' + strftime("%m%d%H%M", currentTime) + r'_HKEJ_log.txt'
			ejlogFile = open(ejlogFilePath, 'w', encoding = 'utf-8')
			for items in result:
				ejlogFile.write(str(items[2]) + '\n')
			ejlogFile.close()

			print("Used Time:", time()-startTime)
			print("Current Time:", strftime("%H%M%S", localtime()))
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

		try:
			#terminating possible opened log file
			ejlogFile.close()
		except:
			pass

	#terminating all drivers
	for i in range(len(driverLog)):
		try:
			driverLog[i].quit()
			print("close driver ", i)
		except:
			pass
