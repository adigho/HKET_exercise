import requests
import bs4
from bs4 import BeautifulSoup
import re
from multiprocessing import Pool

partUrl = "https://stock360.hkej.com/stockList/all/20210226?&p="
my_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',}

def scrape(url):
        stockList = []
        html = requests.get(url, headers = my_headers)
        bs = BeautifulSoup(html.text, 'html.parser')
        stocksWrap = bs.find_all("tr", {"class": "table-rollout"})
        for stock in stocksWrap:
                breakDown = stock.children
                stock_id = next(breakDown).text
                stock_name = next(breakDown).text
                stockList.append([stock_id, stock_name])
        return stockList



if __name__ == '__main__':
        allurl = list()
        for i in range(1, 11):
                pageUrl = partUrl + str(i)
                allurl.append(pageUrl)
        f = open("stock_list.txt", "w", encoding ="utf-8")
        p = Pool(10)
        print("Pool Generated")
        result = p.map(scrape, allurl)
        p.terminate()
        p.join()
        print("Kill")
        for item in result:
                for stock in item:
                        f.write(stock[0])
                        f.write(",")
                        f.write(stock[1])
                        f.write("\n")
        f.close()
