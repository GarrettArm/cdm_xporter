#! /usr/bin/env python3

import urllib.request
import urllib.error
import socket
import time
import logging
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# "alias" is contentDM's term for collection name
# "pointer" is contentDM's term for item name


# contentDM hosts, e.g. CDM_API_SERVER=server17190 & CDM_BINARY_SERVER=cdm17190
CDM_API_SERVER = os.environ.get('CDM_API_SERVER')
CDM_BINARY_SERVER = os.environ.get('CDM_BINARY_SERVER')
if not CDM_API_SERVER or not CDM_BINARY_SERVER:
    raise RuntimeError('Set the CDM_API_SERVER & CDM_BINARY_SERVER environment variables, '
                       'e.g. CDM_API_SERVER=server17190 CDM_BINARY_SERVER=cdm17190')

url_prefix = 'https://{}.contentdm.oclc.org/dmwebservices/index.php?q='.format(CDM_API_SERVER)

# throttling & retry settings for all calls to contentDM
MIN_SECONDS_BETWEEN_REQUESTS = 0.5
TIMEOUT_SECONDS = 60
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}

_last_request_time = 0.0


def _wait_for_rate_limit():
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)
    _last_request_time = time.monotonic()


def _retry_after_seconds(http_error):
    # honors a numeric Retry-After header, if the server sends one
    try:
        return float(http_error.headers.get('Retry-After'))
    except (TypeError, ValueError, AttributeError):
        return None


def fetch(url):
    # every request to contentDM goes through here, so the rate limit applies globally.
    # retries 429/5xx & network errors with exponential backoff; other HTTP errors (e.g. 404) are raised.
    for attempt in range(MAX_RETRIES + 1):
        _wait_for_rate_limit()
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE_HTTP_CODES or attempt == MAX_RETRIES:
                raise
            delay = _retry_after_seconds(e) or BACKOFF_BASE_SECONDS * 2 ** attempt
            logging.warning('HTTP {} on {} -- retrying in {}s'.format(e.code, url, delay))
        except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
            if attempt == MAX_RETRIES:
                raise
            delay = BACKOFF_BASE_SECONDS * 2 ** attempt
            logging.warning('{} on {} -- retrying in {}s'.format(e, url, delay))
        time.sleep(delay)


def fetch_text(url):
    return fetch(url).decode(encoding='utf-8')


def retrieve_collections_list():
    url = '{}dmGetCollectionList/xml'.format(url_prefix)
    return fetch_text(url)


def retrieve_collection_metadata(alias):
    url = '{}dmGetCollectionArchivalInfo/{}/xml'.format(url_prefix, alias)
    return fetch_text(url)


def retrieve_collection_total_recs(alias):
    url = '{}dmQueryTotalRecs/{}|0/xml'.format(url_prefix, alias)
    return fetch_text(url)


def retrieve_collection_fields_xml(alias):
    url = '{}dmGetCollectionFieldInfo/{}/xml'.format(url_prefix, alias)
    return fetch_text(url)


def retrieve_collection_fields_json(alias):
    url = '{}dmGetCollectionFieldInfo/{}/json'.format(url_prefix, alias)
    return fetch_text(url)


def retrieve_elems_in_collection(alias, starting_position, chunk_size, xml_or_json):
    fields = 'fullrs!find!dmaccess!dmimage!dmcreated!dmmodified!dmoclcno!dmrecord'
    url = '{}dmQuery/{}/0/{}/nosort/{}/{}/1/0/0/0/0/0/{}'.format(
        url_prefix, alias, fields, chunk_size, starting_position, xml_or_json)
    return fetch_text(url)


def retrieve_item_metadata(alias, pointer, xml_or_json):
    url = '{}dmGetItemInfo/{}/{}/{}'.format(url_prefix, alias, pointer, xml_or_json)
    return fetch_text(url)


def retrieve_compound_object(alias, pointer):
    url = '{}dmGetCompoundObjectInfo/{}/{}/xml'.format(url_prefix, alias, pointer)
    return fetch_text(url)


def retrieve_parent_info(alias, pointer, xml_or_json):
    url = '{}GetParent/{}/{}/{}'.format(url_prefix, alias, pointer, xml_or_json)
    return fetch_text(url)


def retrieve_binary(alias, pointer):
    cdm_binary_url = 'https://{}.contentdm.oclc.org/utils/getfile/collection'.format(CDM_BINARY_SERVER)
    url = '{}/{}/id/{}/filename/unused.unused'.format(cdm_binary_url, alias, pointer)
    return fetch(url)


def write_xml_to_file(xml_text, folder, filename):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, '{}.xml'.format(filename))
    with open(filepath, 'w') as f:
        f.write(xml_text)


def write_json_to_file(json_text, folder, filename):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, '{}.json'.format(filename))
    with open(filepath, 'w') as f:
        f.write(json_text)


def write_binary_to_file(binary, folder, filename, filetype):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, '{}.{}'.format(filename, filetype))
    with open(filepath, 'bw') as f:
        f.write(binary)
