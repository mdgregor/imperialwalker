import re
import time
from queue import Queue
from threading import Thread
from operator import itemgetter

import requests
from bs4 import BeautifulSoup


def main():
    website_list = {
        "CNN": "http://www.cnn.com",
        "MSNBC": "http://www.msnbc.com",
        "Fox News": "http://www.foxnews.com",
        "Wall Street Journal": "http://www.wsj.com/",
        "The Moscow Times": "http://themoscowtimes.com/",
        "Zeit Online": "http://www.zeit.de/index",
        "The People's Daily": "http://en.people.cn/",
        "The New York Times": "http://www.nytimes.com/",
        "Politico": "http://www.politico.com/",
        "Huffington Post": "http://www.huffingtonpost.com/",
        "CNBC": "http://www.cnbc.com",
        "Breitbart": "http://www.breitbart.com"
    }
    words = ["Trump"]
    web_ratio = []
    data_search = Data_Search()

    for key, value in website_list.items():
        web_ratio.append(data_search.website_feeder(key, value, words))

    for word in words:
        organized_list = []
        for item in web_ratio:
            for value in item:
                if value[1] == word:
                    organized_list.append(value)
        for item in sorted(organized_list, key=itemgetter(2), reverse=True):
            print(f"{item[0]} ratio for the word {item[1]} is {item[2]:.4f} for each link")

class Data_Search():
    def __init__(self):
        self.failed_urls = []

    def website_feeder(self, website_name, web_url, words):
        """
        Finds all instances of a word on a given website
        :param website_name: This should be obvious
        :param web_url: The root URL of the website/domain
        :param words: The words being searched for inside of the html
        """

        result = requests.get(web_url)
        soup = BeautifulSoup(result.text, 'html.parser')
        all_links = []
        instances = []

        # Gets every link available from a websites home page
        for link in soup.find_all('a'):
            all_links.append(link.get('href'))

        # Removes duplicate links found
        all_links = set(all_links)
        queue = Queue()

        for link in all_links:
            if link is None:
                continue
            url = self.link_validation(web_url, link)
            queue.put((instances, url, words))

        for thread in range(50):  # Create 50 threads and do the work
            worker = Worker(queue)  # Instantiate the Worker class and initialize its queue
            worker.daemon = True
            worker.start()  # Start the Worker to work on the queue

        queue.join()  # Close out the queue/worker

        total_mentions = {}

        for word in words:
            total_mentions.update({word: 0})

        for item in instances:
            for key1, value1 in item.items():
                for key2, value2 in value1.items():
                    for word in words:
                        if key1 == word:
                            current_mentions = total_mentions[word] + value2
                            total_mentions.update({word: current_mentions})

        ratio = []
        for key, value in total_mentions.items():
            try:
                print("{} is mentioned {} times on {} across {} links found on the home page.".format(key, value,
                                                                                                      website_name,
                                                                                                      len(instances)))
                ratio.append((website_name, key, value / len(instances)))
            except ZeroDivisionError:
                print(f"{website_name} blocked me for too many requests")

        return ratio

    @staticmethod
    def link_validation(web_url, link):
        """
        Takes the vareity of url links that are found on the homepage of a website and attempts to clean them up for calls through requests library
        :param web_url: The root website.  example: http://www.cnn.com
        :param link: The link found on the root website
        :return: A url which can then be fed to the requests library
        :rtype: str
        """

        if "http" in link:
            return link
        elif "//" == link[0:2]:
            return "http://" + link[2:len(link)]
        else:
            return web_url + link

    @staticmethod
    def search_site(instances, url, words):
        """
        Searches a site for every occurrences found in the html.

        :param instances: List of occurrences found.
        :param url: The url that is being retrieved and searched
        :param words: The words that are being search in the html
        """
        try:
            web_site = requests.get(url)
            time.sleep(.1)
        except Exception as error:
            # print(error)
            return
        if web_site.status_code == 200:
            web_text = web_site.text
            for word in words:
                found_words = len([m.start() for m in re.finditer(word.lower(), web_text.lower())])
                instances.append({word: {url: found_words}})


class Worker(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
        self.data_search = Data_Search()

    def run(self):
        while True:
            instances, url, words = self.queue.get()
            self.data_search.search_site(instances, url, words)
            self.queue.task_done()


if __name__ == "__main__":
    main()
