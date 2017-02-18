import requests
import re
from bs4 import BeautifulSoup
import json


def website_feeder(website_name, web_url):

    result = requests.get(web_url)
    soup = BeautifulSoup(result.text, 'html.parser')
    all_links = []
    outside_links = []
    instances = []

    for link in soup.find_all('a'):
        all_links.append(link.get('href'))

    all_links = set(all_links)

    for link in all_links:
        if link is None:
            continue
        if "http" in link:
            outside_links.append(link)
            continue
        elif "//" in link:
            outside_links.append(link[2:len(link)])
        else:
            url = web_url + link
            web_site = requests.get(url)
            if web_site.status_code == 200:
                web_text = web_site.text
                words = len([m.start() for m in re.finditer("Trump", web_text)])
                instances.append({url: words})
    '''
    for link in outside_links:
        if "www" not in link:
            url = "http://www.{}".format(link)
        elif "http://" not in link:
            url = "http://{}".format(link)

        web_site = requests.get(url)
        if web_site.status_code == 200:
            web_text = web_site.text
            words = len([m.start() for m in re.finditer("Trump", web_text)])
            instances.append({url: words})
    '''
    with open("{}.txt".format(website_name), "w") as f:
        f.write("Number of sites is {}\n".format(len(instances)))
        for item in instances:
            f.write(json.dumps(item))
            f.write("\n")

def main():

    website_list = {
        "CNN": "http://www.cnn.com",
        "MSNBC": "http://www.msnbc.com",
        "Fox News": "http://www.foxnews.com",
    }

    for key, value in website_list.items():
        website_feeder(key, value)

if __name__ == "__main__":
    main()
