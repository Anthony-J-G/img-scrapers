import argparse
import json

from src.scraper import Scraper
from src.artstation import ArtStation


from hashlib import sha256



def run(opts):
    """
        Run Downloader with given options

        options structure : 
            {
                "artstation" : {
                    "fetch" : {
                        "artists"    : [# List of Artists]
                        "artworks"   : [# List of Artworks]
                        "home"      : # Number of Artworks to pull
                    },
                    "save_ref" : # Boolean
                    "download" : {
                        "categorize" : # Boolean
                    }
                }
            }

    """

    for downloader in opts:

        if downloader == "artstation":
            io = ArtStation(headless=False)

            if "fetch" in opts["artstation"] and "artists" in opts["artstation"]["fetch"]:
                io.fetch_artists(opts["artstation"]["fetch"]["artists"])

            if "fetch" in opts["artstation"] and "artworks" in opts["artstation"]["fetch"]:
                pass
            
            if "fetch" in opts["artstation"] and "artworks" in opts["artstation"]["fetch"]:
                pass

            if "save_ref" in opts["artstation"] and opts["artstation"]["save_ref"]:
                io.save_reference("artstation/artstation_ref.csv")
                print(io.reference_table)
                print("Saving Reference Table...")

            if "download" in opts["artstation"]:
                io.save_content()




if __name__ == "__main__":

    with open("artists.json") as f:
        artists = json.load(f)
    
    opts = {
        "artstation" : {
            "fetch": {
                "artists": artists,
                "artworks": ["g2wqnL"],
                "home": 10
            },
            "save_ref" : True,
            "download" : {

            }
        }
    } 
    run(opts)
   
