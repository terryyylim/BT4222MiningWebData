# Creating phone object
class Phone:
    def __init__(self, brand, model, main_url):
        self.brand = brand
        self.model = model
        self.main_url = main_url
        self.comment_urls = []
        self.comments = []
        
    def store_comment_urls(self, url):
        self.comment_urls.append(url)
        
    def store_comment(self, comment):
        self.comments.append(comment)

# Importing required libraries for scraping
import ssl
import re
import requests
from multiprocessing import Pool
from multiprocessing import Process
from bs4 import BeautifulSoup as BS

# Importing required libraries for wordprocessing
import pandas as pd
import numpy as np

# Helper functions
# is_number method is to filter out ">>" text that are present in models with more than 3 pages of comments
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False

def get_phone_brand_links(website):
    r = requests.get(website)
    data = BS(r.content, "lxml")
    all_brands_link = [website + extension for extension in (brand['href'] for brand in ((data.find("div", {"class": "brandmenu-v2"})).find("ul")).find_all("a"))]
    return all_brands_link
    
def get_model_name_link(website):
    try:
        r = requests.get(website, timeout=10)
        data = BS(r.content, "lxml")
        # getting name of brand to append to correct key in 'all_brands_phones' dictionary
        name = re.split(" ", ((data.find("div", {"class": "article-hgroup"})).find("h1", {"class": "article-info-name"})).text)[0]
        # storing only titles of links related to phones (to filter tablets,watches etc.) using boolean checker
        wanted_links = [True if "phone" in link else False for link in (type['title'] for type in ((data.find("div", {"class": "makers"})).find("ul")).find_all("img"))]
        
        # storing model and model_link
        home_url = "https://www.gsmarena.com/"
        phones = []
        for link in range(len(wanted_links)):
            if (wanted_links[link] == True):
                all_models = []
                all_links = []
                models = [all_models.append(wanted.text) for wanted in (((data.find("div", {"class": "makers"})).find("ul")).find_all("a"))][link]
                model_links = [all_links.append(home_url + extension) for extension in (models['href'] for models in (((data.find("div", {"class": "makers"})).find("ul")).find_all("a")))][link]
        for model in range(len(all_models)):
            if (wanted_links[model] == True):
                brand = ((data.find("div", {"class": "article-hgroup"})).find("h1")).text
                brand = re.split(" ", brand)[0]
                phone_model = Phone(brand, all_models[model], all_links[model])
                phones.append(phone_model)
        print("currently at " + website)
        return phones
    except ssl.SSLError:
        print("Oops SSLError faced on " + website)
    except requests.exceptions.Timeout:
        print("Timeout occured in get_model_name_link function")

def get_model_comments_urls(phone):
    try:
        url = phone.main_url
        r = requests.get(url, timeout=10)
        model_mainpage = BS(r.content, "lxml")
        #print(model_mainpage)
        if ((model_mainpage.find("div", {"id": "user-comments"})) != None):
            
            main_comments_url = (((model_mainpage.find("div", {"id": "user-comments"})).find("h2")).find("a")["href"]).replace('.php', "")
            
            # to determine number of pages of comments a particular phone model has
            home_url = "https://www.gsmarena.com/"
            
            # to remove edge cases, where there are hundreds of comments but cannot be accessed
            if (model_mainpage.find("div", {"class": "button-links"}) != None):

                # comments_mainpage is the url link for home page of all comments
                comments_mainpage = [(home_url + to_comment["href"]) for to_comment in (model_mainpage.find("div", {"class": "button-links"})).find_all("a")][0]

                r = requests.get(comments_mainpage, timeout=10)
                comments_homepage = BS(r.content, "lxml")
                
                wanted = [int(number.text) for number in ((comments_homepage.find("div", {"class": "nav-pages"})).find_all("a")) if (is_number(number.text) == True)]

                # case: more than 1 page worth of comments available           
                if ((len(wanted)) != 0):
                    number_of_pages = max(wanted)

                    for pg_number in range(2, number_of_pages+1):
                        indv_page_url = home_url + main_comments_url + "p" + str(pg_number) + ".php"
                        phone.store_comment_urls(indv_page_url)
                    #print(phone.comment_urls)
    except ssl.SSLError:
        print("Oops SSLError faced on " + phone)
    except requests.exceptions.Timeout:
        print("Timeout occured in get_model_comments_urls function")

def get_model_comments(phone):
    try:
        for review_pagelink in phone.comment_urls:
            r = requests.get(review_pagelink, timeout=10)
            review_page = BS(r.content, "lxml")

            all_comments = review_page.find_all("p", {"class": "uopin"})
            for comment in all_comments:
                # if it is a reply to a comment
                if ((comment.find('span') != None) or comment.find('a') != None):
                    # remove all nested span tags
                    while(comment.find('span') != None):
                        comment.span.decompose()
                    # remove all nested a tags
                    while(comment.find('a') != None):
                        comment.a.decompose()
                    # remove all remaining html tags
                    comment = comment.get_text()
                    comment = comment.replace('\r', '', 10)
                    comment = comment.replace('\n', '', 10)
                    # then append
                    phone.store_comment(comment)
                # no nested spans, just append
                else:
                    comment = comment.get_text()
                    comment = comment.replace('\r', '', 10)
                    comment = comment.replace('\n', '', 10)
                    phone.store_comment(comment)
    except ssl.SSLError:
        print("Oops SSLError faced on " + phone)
    except requests.exceptions.Timeout:
        print("Timeout occured in get_model_comments_urls function")
    
# Running the program
if __name__ == '__main__':
    # Website to scrape
    url = "https://www.gsmarena.com/"
    brands = get_phone_brand_links(url)
    # Storing all phone objects in a list called 'phones'
    
    with Pool(6) as pool:
        print("started pooling")
        phones = pool.map(get_model_name_link, brands)
        print(phones)
        print("Finished getting all phone models and their links")
        
        all_phones = []
        # Getting a list of all phone objects
        for brand in phones:
            for model in brand:
                all_phones.append(model)
        print(all_phones)
        print("Finished storing all phone objects into a list")
        
        # Storing list of all models review url into phone object
        #for brand in range(len(all_phones)):
        for brand in range(3):
            get_model_comments_urls(all_phones[brand])
            print("Done with " + all_phones[brand].model + " review URLs!")
            print(all_phones[brand].comment_urls)

        # Storing list of all models review into phone object    
        #for brand in range(len(all_phones)):
        for brand in range(3):
            get_model_comments(all_phones[brand])
            print("Done with " + all_phones[brand].model + " reviews!")
            print(all_phones[brand].comments)

        # Creating DataFrame to store phone model comments
        phone_df = pd.DataFrame(columns=['phone_brand', 'phone_model', 'phone_reviews'])

        print("Adding into dataframe now...")
        # Append all phone information to DataFrame
        #for phone in range(len(all_phones)):
        for phone in range(3):
            phone_brand = all_phones[phone].brand
            phone_model = all_phones[phone].model
            phone_reviews = all_phones[phone].comments
            new_row = [phone_brand, phone_model, phone_reviews]
            phone_df.loc[len(phone_df)] = new_row

        phone_df.to_csv("test.csv", encoding='utf-8', index=False)
        print(phone_df)
