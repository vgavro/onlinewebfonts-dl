#!/usr/bin/env python
import json

import click
from requests import Session


# This is hack because ajax is not supposed to be called on 0, obviously
SEARCH_START_CURSOR = '00'
DOWNLOAD_DEFAULT_FORMATS = ['fontface', 'ttf']


class OnlineWebFontsSession(Session):
    def _ajax(self, subdomain='www', cookies={}, **kwargs):
        resp = self.get(f'https://{subdomain}.onlinewebfonts.com/ajax.html',
                        cookies=cookies, params=kwargs)
        resp.raise_for_status()
        # Strips '(', ')', as this endpoint made for JSONP callback
        rv = json.loads(resp.text[1:-1])
        if 'error' in rv:
            raise RuntimeError(rv['error'], resp.url)
        return rv

    def get_search(self, query, cursor=SEARCH_START_CURSOR):
        rv = self._ajax(type='search', q=query, p=cursor)
        # Returns cursor, data
        # Data format is:
        # id, full name, name (uniq?), type (underscored?), type(spaces?),
        # author (underscored?), author (spaces?), size str
        return rv['p'], rv['data']

    def get_download_url(self, id, name, formats=DOWNLOAD_DEFAULT_FORMATS):
        return (self._ajax('cdn', cookies={'downloadname': name},
                type='a', id=id, format='|'.join(formats)))['data']

    def download(self, url, local_filename=None, chunk_size=8192):
        # https://stackoverflow.com/a/16696317/450103
        local_filename = local_filename or url.split('/')[-1]
        with self.get(url, stream=True) as resp:
            resp.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        # f.flush()
        return local_filename

    def download_all(self, query, formats=DOWNLOAD_DEFAULT_FORMATS,
                     cursor=SEARCH_START_CURSOR):
        while cursor:
            cursor, data = self.get_search(query, cursor)
            assert data or not cursor
            for row in data:
                url = self.get_download_url(row[0], row[2])
                local_filename = self.download(url)
                yield row, local_filename


@click.command()
@click.option('--formats', default=','.join(DOWNLOAD_DEFAULT_FORMATS),
              show_default=True)
@click.option('--query', prompt='Query to search')
def main(formats, query):
    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    session = OnlineWebFontsSession()
    for row, local_filename in session.download_all(query, formats.split(',')):
        logging.info(f'Downloaded {row} to {local_filename}')


if __name__ == '__main__':
    main()
