import requests
import re
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue


def website_feeder(website_name, web_url, word):

    result = requests.get(web_url)
    soup = BeautifulSoup(result.text, 'html.parser')
    all_links = []
    instances = []
    failed_urls = []

    for link in soup.find_all('a'):
        all_links.append(link.get('href'))

    all_links = set(all_links)
    queue = Queue()
    for link in all_links:
        worker = Worker(queue)  # so that essentially all URLS are called
        worker.daemon = True  # at the same tim
        worker.start()
        if link is None:
            continue
        if "http" in link:
            queue.put((instances, link, word))
        elif "//" == link[0:2]:
            url = "http://" + link[2:len(link)]
            queue.put((instances, url, word))
        else:
            url = web_url + link
            queue.put((instances, url, word))

    queue.join()
    total_mentions = 0
    for item in instances:
        for value in item.values():
            total_mentions += value
    print("{} is mentioned {} times on {} across {} links found on the home page".format(word, total_mentions, website_name, len(instances)))


def search_site(instances, url, word):
    try:
        web_site = requests.get(url)
    except:
        return
    if web_site.status_code == 200:
        web_text = web_site.text
        words = len([m.start() for m in re.finditer(word, web_text)])
        instances.append({url: words})


def main():

    website_list = {
        "CNN": "http://www.cnn.com",
        "MSNBC": "http://www.msnbc.com",
        "Fox News": "http://www.foxnews.com",
        "Wall Street Journal": "http://www.wsj.com/",
        "Foreign Affaris": "http://www.foreignaffairs.com/",
        "The Moscow Times": "http://themoscowtimes.com/",
        "Zeit Online": "http://www.zeit.de/index"
    }
    words = ["Trump", "Russia"]
    for word in words:
        for key, value in website_list.items():
            website_feeder(key, value, word)


class Worker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            instances, url, word = self.queue.get()
            search_site(instances, url, word)
            self.queue.task_done()

if __name__ == "__main__":
    main()
