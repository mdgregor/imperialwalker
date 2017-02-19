import requests
import re
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue


def main():

    website_list = {
        "CNN": "http://www.cnn.com",
        "MSNBC": "http://www.msnbc.com",
        "Fox News": "http://www.foxnews.com",
        "Wall Street Journal": "http://www.wsj.com/",
        "Foreign Affaris": "http://www.foreignaffairs.com/",
        "The Moscow Times": "http://themoscowtimes.com/",
        "Zeit Online": "http://www.zeit.de/index",
        "The People's Daily": "http://en.people.cn/"
    }
    words = ["Trump", "Russia"]

    data_search = Data_Search()

    for word in words:
        for key, value in website_list.items():
            data_search.website_feeder(key, value, word)


class Data_Search():

    def __init__(self):
        self.failed_urls = []

    def website_feeder(self, website_name, web_url, word):
        """
        Finds all instances of a word on a given website
        :param website_name: This should be obvious
        :param web_url: The root URL of the website/domain
        :param word: The word being searched for inside of the html
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

        for link in all_links:          # A separate Thread is created for each link. ONLY DO THIS WITH NETWORK TASKS
            worker = Worker(queue)      # Instantiate the Worker class and initialize its queue
            worker.daemon = True
            worker.start()              # Start the Worker to work on the queue
            if link is None:
                continue
            url = self.link_validation(web_url, link)
            queue.put((instances, url, word))  # Put the instances list, url, and word for a single search in the queue.

        queue.join()                    # Close out the queue/worker

        total_mentions = 0
        for item in instances:
            for value in item.values():
                total_mentions += value

        print("{} is mentioned {} times on {} across {} links found on the home page.".format(word, total_mentions, website_name, len(instances)))
        print("Number of failed urls: {}".format(len(self.failed_urls)))
        failed_urls = set(self.failed_urls)
        print("Failed URLS: {}".format(failed_urls))

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

    def search_site(self, instances, url, word):
        """
        Searches a site for every occurrences found in the html.

        :param instances: List of occurrences found.
        :param url: The url that is being retrieved and searched
        :param word: The word that is being search in the html
        """
        try:
            web_site = requests.get(url)
        except:
            print(url)
            self.failed_urls.append(url)
            return
        if web_site.status_code == 200:
            web_text = web_site.text
            words = len([m.start() for m in re.finditer(word, web_text)])
            instances.append({url: words})


class Worker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
        self.data_search = Data_Search()

    def run(self):
        while True:
            instances, url, word = self.queue.get()
            self.data_search.search_site(instances, url, word)
            self.queue.task_done()

if __name__ == "__main__":
    main()
