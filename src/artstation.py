

import os
from bs4 import BeautifulSoup
from src.scraper import Scraper
import json
from tqdm import tqdm
import re
import pandas as pd


class ArtStation(Scraper):

    CACHE_LOC = f"{Scraper.CACHE_LOC}/artstation"

    def __init__(self, headless=True) -> None:
        super().__init__(headless)

        try:
            os.mkdir(ArtStation.CACHE_LOC)
        except FileExistsError:
            pass

        try:
            os.mkdir(ArtStation.CACHE_LOC + "/jsons")
        except FileExistsError:
            pass 

        try:
            os.mkdir(ArtStation.CACHE_LOC + "/imgs")
        except FileExistsError:
            pass 
 

    def fetch_artwork(self, id, output=False):
        self.driver.get(f"https://www.artstation.com/projects/{id}.json")
        content = self.driver.page_source
        soup = BeautifulSoup(content, features="html.parser")
        obj = json.loads(soup.text)

        records = []
        for asset in obj["assets"]:

            if ".jpg" not in asset['image_url'] and ".png" not in asset['image_url']:
                continue

            ext = ""
            if ".jpg" in asset['image_url']:
                ext = ".jpg"

            if ".png" in asset['image_url']:
                ext = ".png"

            data = {
                    "category"      :   obj['user']['full_name'], 
                    "subcategory"   :   obj['hash_id'], 
                    "height"        :   asset["height"], 
                    "width"         :   asset["width"], 
                    "hashdigest"    :   False, 
                    "filename"      :   asset["id"],
                    "file_type"     :   ext, 
                    "url"           :   asset['image_url']
            }
            records.append(data)

        df = pd.DataFrame().from_records(records)
        self.reference_table = pd.concat(
            [self.reference_table, df]
        )

        

        if output:
            with open(f'{ArtStation.CACHE_LOC}/jsons/{id}.json', 'w') as f:
                json.dump(obj, f, indent=2, sort_keys=True)

        return obj


    def fetch_artist(self, id, output=False):
        self.driver.get(f"https://{id}.artstation.com")
        content = self.driver.page_source

        try:
            obj = {
                "url": self.driver.current_url,
                "name": re.search(r"\"og:title\" content=\"(.+)\"", content)[1],
                "description": re.search(r"\"og:description\" content=\"(.+)\"", content)[1],
                "projects": re.findall(r"href=\"/projects/(.+?)\"", content)
            }
        except Exception as e:
            # print(e)
            # print(id)
            return None

        for project in obj["projects"]:
            self.fetch_artwork(project, output=output)

        if output:
            with open(f'{ArtStation.CACHE_LOC}/jsons/{id}.json', 'w') as f:
                json.dump(obj, f, indent=2, sort_keys=True)

        return obj


    def fetch_home(self, num, sort=None, output=False):
        self.driver.get(f"https://www.artstation.com/")
        content = self.driver.page_source

        soup = BeautifulSoup(content, features="html.parser")
        uls = soup.find_all("ul")

        print(len(uls))


    def fetch_artists(self, ids):
        for id in tqdm(ids):
            self.fetch_artist(id)