import os
from bs4 import BeautifulSoup
import requests
import re
import time
import logging
import threading
import time
import concurrent.futures
from requests_futures.sessions import FuturesSession

#Constants
url = 'https://www.nike.com/launch/?s=upcoming'
url2 = 'https://www.reddit.com'
urlList = [ url2, url]
attrDict = {'data-qa':'product-card-link'}
productAttr = 'aria-label'
filterWords = '\sRelease Date'
productIndex = 0
parser = 'html.parser'
header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',} 

class InternalCache:
    def __init__(self):
        self.Data = []
        self.DataDictionary = {}
        self._lock = threading.Lock()

    '''
    input: name - thread name
           item - string to store in self.Data

    return none
    '''
    def locked_update(self,name,item):
        logging.info("Thread %s: starting update", name)
        logging.debug("Thread %s: about to lock", name)

        #Acquire lock, check if data already present, and release lock
        with self._lock:
            logging.debug("Thread %s has lock", name)
            local_copy_data = self.Data
            local_copy_dictionary = self.DataDictionary
            # Store item if not present already
            if (item not in local_copy_dictionary):
                local_copy_data.append(item)
                local_copy_dictionary[item] = 1
            self.Data = local_copy_data
            self.DataDictionary = local_copy_dictionary
            logging.debug("Thread %s about to release", name)

        logging.debug("Thread %s after release", name)
        logging.info("Thread %s: finishing update", name)

'''
input: url - url to send request to
       parser - html parser to generate beautiful soup
       session - FuturesSession instantiation to make request

return HTML document from url
'''
def getHTMLDocFromURL(url,parser, session):
    r = sendAsnychRequest(url, session).result()
    if (r.status_code == requests.codes.ok):
        print('Status: ',r.status_code)
        return BeautifulSoup(r.content,parser)
    else:
        print('Status: ',r.status_code)
        r.raise_for_status()

'''
input: url - url to send request to
       session - FuturesSession instantiation to make request

return request
'''
def sendAsnychRequest(url, session):
    r = session.get(url,headers = header, timeout = 5)
    return r

'''
input: url - url to rquest page from and get links
       name - thread name
       cache - class to store data
       session - FuturesSession instantiation

return none
'''
def storeLinksInCache(url,name, cache, session):
    soup = getHTMLDocFromURL(url,parser, session)
    for link in soup.find_all(attrs = {'href':re.compile(".+")}):
        print(link["href"])
        cache.locked_update(name,link['href'])

def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format = format, level = logging.INFO,
            datefmt = "%H:%M:%S")

    session = FuturesSession(executor=concurrent.futures.ThreadPoolExecutor(max_workers=len(urlList)))
    cache = InternalCache()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(len(urlList)):
            print('Scraping ',urlList[i])
            executor.submit(storeLinksInCache, urlList[i], i, cache, session)
    print(cache.Data)

main()
'''
while(True):
    printProductNamesFromURL(url,attrDict,productAttr,productIndex,filterWords)
    time.sleep(1)
    getLinks(url2)
'''

def printProductNamesFromURL(url, attrDict, productAttr,productIndex, filterWords):
    soup = getHTMLDocFromURL(url,parser)
    for product in soup.find_all(attrs= attrDict):
        temp = re.split(filterWords, product[productAttr])
        print (temp[productIndex])

def getLinks(url):
    soup = getHTMLDocFromURL(url,parser)
    for link in soup.find_all(attrs = {'href':re.compile("^https.+")}):
            print (link['href'])
