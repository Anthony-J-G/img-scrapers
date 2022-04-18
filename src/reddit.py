import requests
import json
import pandas as pd
from datetime import datetime
from PIL import Image
from io import BytesIO

MAX_POSTS_PER_PAGE = 100
ACCEPTABLE_FILE_EXTS = {
    "jpg":1, "png":1
}


class RedditScraper:

    def __init__(self, id, token, username, password) -> None:
        # note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
        auth = requests.auth.HTTPBasicAuth(f'{id}', f'{token}')

        # here we pass our login method (password), username, and password
        data = {'grant_type': 'password',
                'username': f'{username}',
                'password': f'{password}'}

        # setup our header info, which gives reddit a brief description of our app
        headers = {'User-Agent': 'MyBot/0.0.1'}

        # send our request for an OAuth token
        res = requests.post('https://www.reddit.com/api/v1/access_token',
                            auth=auth, data=data, headers=headers)

        # convert response to JSON and pull access_token value
        auth_token = res.json()['access_token']

        # add authorization to our headers dictionary
        self.headers = {**headers, **{'Authorization': f"bearer {auth_token}"}}

        # while the token is valid (~2 hours) we just add headers=headers to our requests
        requests.get('https://oauth.reddit.com/api/v1/me', headers=self.headers)
        

    def parse(self, res, params=[]) -> pd.DataFrame:
        params = ["title", "id"] + params
        # Initialize temporary DataFrame
        df = pd.DataFrame()

        # Append each post in response to DataFrame
        for post in res.json()['data']['children']:
            # Parse needed fields from resonse JSON
            fields = {i: post['data'][i] for i in params}

            # Determine the kind of post
            fields['kind'] = post['kind']
            
            # Add creation date
            fields['created_utc'] = datetime.fromtimestamp(
                post['data']['created_utc']
            ).strftime('%Y-%m-%dT%H:%M:%SZ')          

            # Append data to DataFrame
            df = df.append(fields, ignore_index=True)

        return df


    def fetch_from(self, subreddit, num_posts, sort_option, timescale, fields=["url"]) -> pd.DataFrame:

        # initialize empty dataframe and params dict
        data = pd.DataFrame()
        params = {
            'limit':str(MAX_POSTS_PER_PAGE),'sort':sort_option,'t':timescale
        }

        if num_posts > MAX_POSTS_PER_PAGE:
            pages = int(num_posts / MAX_POSTS_PER_PAGE)
            overflow = num_posts - (pages * MAX_POSTS_PER_PAGE)
        else:
            pages = 1
            overflow = 0
            params['limit'] = str(num_posts)

        if overflow > 0:
            pages = pages + 1
        

        # Request 'x' number of pages
        for i in range(pages):
            
            # Handle overflowing data
            if overflow > 0 and i == pages - 1:
                params['limit'] = overflow                

            # Make request
            res = requests.get(f"https://oauth.reddit.com/r/{subreddit}/{params['sort']}/",
                headers=self.headers,
                params=params)

            # Parse response to pandas DataFrame
            current_page = self.parse(res, fields)

            # Request can't be parsed to DataFrame for whateve reason, throw Error
            if type(current_page) == type(None) or len(current_page) == 0:
                print(res.json())
                print(
                    f"requests remaining: {res.headers['x-ratelimit-remaining']}, requests used: {res.headers['x-ratelimit-used']}, requests reset: {res.headers['x-ratelimit-reset']},"
                )
                # raise ValueError
                break

            # Determine the start of the next page and feed it to parameters
            # take the final row (oldest entry)
            row = current_page.iloc[len(current_page) - 1]
            # create fullname
            fullname = row['kind'] + '_' + row['id']
            # add/update fullname in params
            params['after'] = fullname
            
            # append new_df to data
            data = data.append(current_page, ignore_index=True)

        

        return data


    def save_content(self, url, dir_path, filename):

        file_ext = url.split(".")[-1]
        if file_ext not in ACCEPTABLE_FILE_EXTS:
            return False

        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img.save(f"{dir_path}/{filename}.{file_ext}")

        return True