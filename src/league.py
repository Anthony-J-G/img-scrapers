import requests
import json
import pandas as pd
from datetime import datetime
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time


from dotenv import dotenv_values

from scraper import Scraper



ACCEPTABLE_FILE_EXTS = {
    "jpg":1, "png":1
}

TABLE_HEADERS = [
    "name", "skin", "url"
]

# .env variables
config = dotenv_values(".env")
CHROME_PATH = config["CHROME_PATH"]
CHROME_WEBDRIVER_PATH = config["CHROME_WEBDRIVER_PATH"]

# url variables
LOL_CHAMPION_LIST_URL = "https://leagueoflegends.fandom.com/wiki/List_of_champions"
LOR_CHAMPION_LIST_URL = "https://leagueoflegends.fandom.com/wiki/Champion_(Legends_of_Runeterra)"
LOR_FOLLOWER_LIST_URL = "https://leagueoflegends.fandom.com/wiki/Follower_(Legends_of_Runeterra)"
LOL_UNIVERSE = [
    "https://universe.leagueoflegends.com/en_US/explore/short-stories/newest/"
]

# Save Content Constants
FILE_TYPES = [
    ".png",
    ".jpg",
]

# LoL Champion Constants
POSSIBLE_CATEGORIES = {"Available":1, "Legacy Vault":1, "Upcoming":1, "Rare & Limited":1, "Wild Rift Exclusive":1}

class League(Scraper):

    CACHE_LOC = f"{Scraper.CACHE_LOC}/league"

    def __init__(self, headless=True) -> None:
        super().__init__(headless)

        try:
            os.mkdir(League.CACHE_LOC)
        except FileExistsError:
            pass

        try:
            os.mkdir(League.CACHE_LOC + "/jsons")
        except FileExistsError:
            pass 

        try:
            os.mkdir(League.CACHE_LOC + "/imgs")
        except FileExistsError:
            pass 
        


    def save_content(self, files, aggregate_dir=None):
        
        for i in files:
            info_table = pd.read_csv(f"{self.meta_data_path}/{i}")


    def lol_champions(self, table_name):
        self.driver.get(LOL_CHAMPION_LIST_URL)

        time.sleep(5) # Wait to make sure page loads
        html = self.driver.page_source

        soup = BeautifulSoup(html, features="html.parser")

        # Parse Table From the soup
        subset = soup.body
        subset = subset.find("div", class_="main-container")
        subset = subset.find("div", class_="resizable-container")
        subset = subset.find("div", class_="page has-right-rail")
        subset = subset.main
        subset = subset.find("div", id="content", class_="page-content" )
        subset = subset.find("div", id="mw-content-text", class_="mw-content-ltr")
        subset = subset.find("div", class_="mw-parser-output").find_all("table")
        table = subset[1].tbody

        # Get Champion names from the Soup
        info = pd.DataFrame(columns=["name", "url"])
        rows = table.find_all("tr")
        urls = []
        names = []
        for i in rows:
            attributes = i.td.attrs
            name = attributes['data-sort-value']
            url = i.td.span.span.a.get("href")

            urls.append(url)
            names.append(name)

        info = pd.DataFrame()
        info["name"] = names
        info["url"] = urls
        info = info.set_index("name")

        # Search through every champion webpage to parse a table of img urls
        extended = pd.DataFrame(columns=["name","filename","url"])
        for i in range( len(info.index) ):
            link = "https://leagueoflegends.fandom.com/" + info.iloc[i]["url"] + "/Cosmetics"

            self.driver.get(link)
            time.sleep(5)

            html = self.driver.page_source
            soup = BeautifulSoup(html, features="html.parser")

            # Find Champion Data
            garbage = soup.body
            garbage = garbage.find("div", class_="mw-parser-output")
            garbage = garbage.find_all(["div", "h2"], recursive=False)

            name = info.index[i]
            tbl_rows = []
            for j, tag in enumerate(garbage):
                if tag.name == "h2" and tag.get_text() in POSSIBLE_CATEGORIES:
                    tbl_rows = garbage[j+1].find_all("div", recursive=False)
                else:
                    continue

                for k in tbl_rows:
                    if "style" not in k.attrs:
                        continue
                    if k.style == "clear:both":
                        break
                    
                    try:
                        link = k.div.a.img.attrs["data-src"]
                    except:
                        print(k.div.a.attrs)

                    ind = -1
                    file_type = None
                    for t in FILE_TYPES:
                        ind = link.find(".jpg")
                        if ind != -1:
                            file_type = t
                            break
                        else:
                            ind = -1
                            continue

                    if file_type == None:
                        continue
                    link = link[:ind+len(file_type)]
                    filename = link.split("/")[-1]

                    extended = extended.append( {"name":name, "filename":filename, "url":link} , ignore_index=True)

                # break # Uncomment to only run on the first image

            # For now only focus on Aatrox
            # break # Remove the break later

        extended = extended.set_index(["name", "filename"])
        print(extended)
        extended.to_csv(f"{self.meta_data_path}/{table_name}")


    def lor_champions(self, table_name):
        self.driver.get(LOR_CHAMPION_LIST_URL)

        html = self.driver.page_source

        soup = BeautifulSoup(html, features="html.parser")

        champ_list = soup.body
        champ_list = champ_list.find("div", class_="main-container")
        champ_list = champ_list.find("div", class_="resizable-container")
        champ_list = champ_list.find("div", class_="page has-right-rail")
        champ_list = champ_list.main
        champ_list = champ_list.find("div", id="content")
        champ_list = champ_list.find("div", id="mw-content-text")
        champ_list = champ_list.find("div", class_="mw-parser-output")
        champ_list = champ_list.find(
            "table", class_="sortable article-table nopadding sticky-header jquery-tablesorter"
        )
        champ_list = champ_list.tbody.find_all("tr", recursive=False)

        url_header = "https://leagueoflegends.fandom.com/"
        champ_table = pd.DataFrame(columns=["name", "url"])
        for i, row in enumerate(champ_list):
            data = row.find_all("td", recursive=False)

            url_footer = data[1].a.get("href")

            name = data[1].a.get_text()
            url = url_header + url_footer

            champ_table = champ_table.append({"name":name, "url":url}, ignore_index=True)

            # remove this later, I just want to run this on a small subset first
            #if i > 11:
                #break

        # print(set(champ_table["name"].values))
        
        
        extended = pd.DataFrame(columns=["name", "filename", "url"])
        visited = {}
        for i, row in enumerate( champ_table.values ):
            name = row[0]
            if name in visited:
                continue
            visited[name] = True

            self.driver.get(row[1])
            time.sleep(5)

            html = self.driver.page_source
            soup = BeautifulSoup(html, features="html.parser")

            subset = soup.body
            subset = subset.find("div", class_="main-container")
            subset = subset.find("div", class_="resizable-container")
            subset = subset.find("div", class_="page has-right-rail").main
            subset = subset.find("div", id="content")
            subset = subset.find("div", id="mw-content-text")
            subset = subset.find("div", class_="mw-parser-output")

            # Determine if the champion card has any skins
            skins = subset.find_all("span", id="Skins")
            
            # If it doesn't, do search function 1
            if len(skins) == 0:
                possibles = subset.find_all("aside", class_="portable-infobox pi-background pi-border-color pi-theme-card pi-layout-default")
                
                for j, card in enumerate(possibles):
                    card_type = card.find("div", attrs={"data-source": "type"}).find("a", class_="mw-redirect").get_text()
                    if card_type == "Champion Spell" or card_type == "Spell":
                        continue
                    figures = card.find_all("figure")
                    for k, fig in enumerate(figures):
                        title = fig.figcaption.get_text()
                        if title.strip() != "Primary":
                            continue

                        print(fig.attrs)


                exit()

                

            # If it does, do search function 2
            else:
                skins = subset.find_all("div", class_="skin-single-card")
                for j, card in enumerate(skins):
                    is_champion = card.find_all("div", recursive=False)[1].span.get_text().find("Level") != -1
                    is_champion = is_champion or card.find_all("div", recursive=False)[1].span.get_text().find("Returned") != -1 # Sion Exception

                    if not is_champion:
                        continue

                    skin = card.div.attrs["data-skin"]
                    link = card.div.a.attrs["href"]

                    extended = extended.append( {"name":name, "skin":skin, "url":link}, ignore_index=True)

        extended = extended.set_index(["name", "skin"])
        extended.to_csv(table_name)


def save_content(dir_path, files, unique_dir=True):

    for i in files:
        data = pd.read_csv(f"{dir_path}/{i}")

        for j in range( len(data) ):
            
            url = data.iloc[j]["url"]
            name = data.iloc[j]["name"]
            if unique_dir:
                try:
                    os.mkdir(f"{dir_path}/{name}")
                except FileExistsError:
                    pass
            
            jpg_ind = url.find(JPG)
            png_ind = url.find(PNG)

            ind = -1
            if jpg_ind != -1:
                ind = jpg_ind
            elif png_ind != -1:
                ind = png_ind
            else:
                continue

            url = url[:ind+4]
            filename = url.split("/")[-1]

            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            if unique_dir:
                img.save(f"{dir_path}/{name}/{filename}")
            else:
                img.save(f"{dir_path}/{filename}")


def lol_universe(table_name, urlno):
    # Instantiate options
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--log-level=3")
    opts.binary_location = CHROME_PATH

    url = LOL_UNIVERSE[urlno]

    # Instantiate a webdriver
    driver = webdriver.Chrome(CHROME_WEBDRIVER_PATH, options=opts) 
    driver.get(url)

    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")
    subset = soup.body.find_all("div", class_="CardWrapper_3s9j")

    print(len(subset))

    

    
def lor_champions(table_name):

    # Instantiate options
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--log-level=3")
    opts.binary_location = CHROME_PATH

    url = LOR_CHAMPION_LIST_URL

    # Instantiate a webdriver
    driver = webdriver.Chrome(CHROME_WEBDRIVER_PATH, options=opts) 
    driver.get(url)

    time.sleep(5)
    
    html = driver.page_source

    soup = BeautifulSoup(html, features="html.parser")

    champ_list = soup.body
    champ_list = champ_list.find("div", class_="main-container")
    champ_list = champ_list.find("div", class_="resizable-container")
    champ_list = champ_list.find("div", class_="page has-right-rail")
    champ_list = champ_list.main
    champ_list = champ_list.find("div", id="content")
    champ_list = champ_list.find("div", id="mw-content-text")
    champ_list = champ_list.find("div", class_="mw-parser-output")
    champ_list = champ_list.find(
        "table", class_="sortable article-table nopadding sticky-header jquery-tablesorter"
    )
    champ_list = champ_list.tbody.find_all("tr", recursive=False)

    url_header = "https://leagueoflegends.fandom.com/"
    champ_table = pd.DataFrame(columns=["name", "url"])
    for i, row in enumerate(champ_list):
        data = row.find_all("td", recursive=False)

        url_footer = data[1].a.get("href")

        name = data[1].a.get_text()
        url = url_header + url_footer

        champ_table = champ_table.append({"name":name, "url":url}, ignore_index=True)

        # remove this later, I just want to run this on a small subset first
        #if i > 11:
            #break

    # print(champ_table)
    
    extended = pd.DataFrame(columns=["name", "skin", "url"])
    visited = {}
    for i, row in enumerate( champ_table.values ):
        name = row[0]
        if name in visited:
            continue
        visited[name] = True

        driver.get(row[1])
        time.sleep(5)

        html = driver.page_source
        soup = BeautifulSoup(html, features="html.parser")

        subset = soup.body
        subset = subset.find("div", class_="main-container")
        subset = subset.find("div", class_="resizable-container")
        subset = subset.find("div", class_="page has-right-rail").main
        subset = subset.find("div", id="content")
        subset = subset.find("div", id="mw-content-text")
        subset = subset.find("div", class_="mw-parser-output")

        # Determine if the champion card has any skins
        skins = subset.find_all("span", id="Skins")
        
        # If it doesn't, do search function 1
        if len(skins) == 0:
            possibles = subset.find_all("li", style="display:inline-block;text-indent:0px;")

            

        # If it does, do search function 2
        else:
            skins = subset.find_all("div", class_="skin-single-card")
            for j, card in enumerate(skins):
                is_champion = card.find_all("div", recursive=False)[1].span.get_text().find("Level") != -1
                is_champion = is_champion or card.find_all("div", recursive=False)[1].span.get_text().find("Returned") != -1 # Sion Exception

                if not is_champion:
                    continue

                skin = card.div.attrs["data-skin"]
                link = card.div.a.attrs["href"]

                extended = extended.append( {"name":name, "skin":skin, "url":link}, ignore_index=True)

    extended = extended.set_index(["name", "skin"])
    extended.to_csv(table_name)