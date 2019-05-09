#!/usr/bin/env python
import json
import os.path

import click
from requests import Session


# This is hack because ajax is not supposed to be called on 0, obviously
SEARCH_START_CURSOR = '00'
DOWNLOAD_DEFAULT_FORMATS = ['fontface', 'ttf']
USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36')


class OnlineWebFontsSession(Session):
    def _ajax(self, subdomain='www', cookies=None, headers=None, **kwargs):
        # User-Agent is not checked, but just in case...
        headers = headers or {}
        headers.setdefault('User-Agent', USER_AGENT)

        resp = self.get(f'https://{subdomain}.onlinewebfonts.com/ajax.html',
                        headers=headers, cookies=cookies, params=kwargs)
        resp.raise_for_status()
        # Strips '(', ')', as this endpoint made for JSONP callback
        rv = json.loads(resp.text[1:-1])
        if 'error' in rv:
            raise RuntimeError(rv['error'], resp.url)
        return rv

    def get_search(self, query, cursor=SEARCH_START_CURSOR):
        rv = self._ajax(type='search', q=query, p=cursor)
        # Returns data, next_cursor
        # Data format is:
        # id, full name, name (uniq?), type (underscored?), type(spaces?),
        # author (underscored?), author (spaces?), size str
        if rv['data'] == 'end':
            return [], None
        return rv['data'], rv.get('p')

    def get_download_url(self, id, name, formats=DOWNLOAD_DEFAULT_FORMATS):
        # referer is not checked, but just in case...
        referer = f'https://www.onlinewebfonts.com/download/{id}'
        return self._ajax(
            'cdn', cookies={'downloadname': name},
            headers={'Referer': referer},
            type='a', id=id, format='|'.join(formats),
            # format=('|'.join(formats) + '|').encode('utf8')
        )['data']

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
                     to='./', cursor=SEARCH_START_CURSOR):
        while cursor:
            data, cursor = self.get_search(query, cursor)
            assert data or not cursor
            for row in data:
                url = self.get_download_url(row[0], row[2], formats)
                local_filename = self.download(
                    url, os.path.join(to, f'{row[5]}-{row[2]}-{row[0]}.zip'))
                yield row, local_filename


@click.command()
@click.option('--formats', default=','.join(DOWNLOAD_DEFAULT_FORMATS),
              show_default=True)
@click.option('--to', default='./', show_default=True,
              help='download directory')
@click.option('--cursor', default=SEARCH_START_CURSOR,
              help='start cursor (integer offset) for search')
@click.option('--query', prompt='Query to search')
def main(formats, to, cursor, query):
    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    session = OnlineWebFontsSession()
    generator = session.download_all(query, formats=formats.split(','),
                                     to=to, cursor=cursor)
    for i, (row, local_filename) in enumerate(generator):
        logging.info(f'Downloaded {i + int(cursor)} {row} to {local_filename}')


if __name__ == '__main__':
    main()
