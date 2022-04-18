import requests
import json
import pandas as pd
from datetime import datetime
from multiprocessing import cpu_count
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

from tqdm import tqdm

from dotenv import dotenv_values


config = dotenv_values(".env")
CHROME_PATH = config["CHROME_PATH"]
CHROME_WEBDRIVER_PATH = config["CHROME_WEBDRIVER_PATH"]


class Scraper:

    CACHE_LOC = "out"
    THREADS = cpu_count() * 3
    download_chunk_size = 1048576

    def __init__(self, headless=True) -> None:
        # Instantiate options
        self.opts = Options()
        if headless:
            self.opts.add_argument("--headless") # Headless stops a window from opening when run
        self.opts.add_argument("--log-level=3")
        self.opts.binary_location = CHROME_PATH

        # Instantiate a webdriver
        self.driver = webdriver.Chrome(CHROME_WEBDRIVER_PATH, options=self.opts)

        self.reference_table = pd.DataFrame(columns=["category", "subcategory", "height", "width", "hashdigest", "filename", "file_type", "url"])

        try:
            os.mkdir(Scraper.CACHE_LOC)
        except FileExistsError:
            pass     


    def search(self, url):
        res = self.driver.get(url)

        time.sleep(5) # Wait to make sure page loads
        html = self.driver.page_source

        soup = BeautifulSoup(html, features="html.parser")
        imgs = soup.find_all("img")


    def save_content(self):
        N = len(self.reference_table)
        for i in tqdm( range(N) ):
            url = self.reference_table.iloc[i]["url"]
            filename = self.reference_table.iloc[i]["filename"]
            file_ext = self.reference_table.iloc[i]["file_type"]

            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img.save(f"out/artstation/imgs/{filename}{file_ext}")


    def save_reference(self, name):
        self.reference_table.to_csv(f"{Scraper.CACHE_LOC}/{name}")