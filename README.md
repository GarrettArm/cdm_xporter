# cdm_xporter

Before using this suite of scripts, consider using https://github.com/MarcusBarnes/mik for migrating from contentDM to Islandora.

scrape_cDM.py pulls all the necessary binaries and metadata for converting to mods & migration to Islandora.  There are two sections in the `if __name__ == '__main__':`.  The first allows you to specify certain collections to scrape.  The second allows you to pull all aliases, except those you specify.  

The output of scrape_cDM.py is DublinCore metadata, as found in contentdm.  These metadata can be source material for our branch of mik.  They can also be source material for our cDM_to_mods.py.  Both programs convert the DublinCore to mods.

`git clone https://github.com/lsulibraries/cdm_xporter/`

`python3 scrape_cDM`

look for the output in "../Cached_Cdm_files"

cDM_api_call.py is merely a group of frequently used contentDM API calls.  It's useful as an import.  You will want to change the string specifying your contentDM server address.

The test file can be run using pytest.

Make a .env file:
```
CDM_API_SERVER=server12345
CDM_BINARY_SERVER=cdm12345
COLLECTION_ALIAS=p12345coll1
```

COLLECTION_ALIAS is the collection the first section of scrape_cDM.py scrapes.  It can be a comma-separated list, e.g. `COLLECTION_ALIAS=p12345coll1,p12345coll2`.