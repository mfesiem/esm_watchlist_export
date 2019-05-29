# -*- coding: utf-8 -*-

import base64
import json
import re
import sys
from config import ESMConfig
from httpclient import HTTPClient
from exceptions import ESMError

class ESM(object):
    def __init__(self, esmcfg, api_version='2'):
        """Initialize the ESM class.

        Args: 
            esmcfg: Instance of ESMConfig object OR Dict with these keys:
                {'esmhost': '<ESM-IP>',
                'esmuser': <ESM-USERNAME>,
                'esmpass': <ESM-PASSWORD>}

            api_version (str): '1' or '2'. Defaults to '2'.

        Returns:
            Instance of ESM

        Raises:
            ValueError: esmcfg required.
            ValueError: esmhost, esmuser, esmpass required in esmcfg.
            ValueError: api_version must be '1' or '2'.
        """
        if api_version is not '2':# or not '2':
            raise ValueError('api_version is "1" or "2".')
        try:
            esmuser = esmcfg['esmuser']
        except KeyError:
            raise ValueError('Invalid esmcreds: Missing esmuser.')
        try:
            esmpass = esmcfg['esmpass']
        except KeyError:
            raise ValueError('Invalid esmcfg: Missing esmpass.')
        try:
            esmhost = esmcfg['esmhost']
        except KeyError:
            raise ValueError('Invalid esmcfg: Missing esmhost.')            

        self.session = HTTPClient()
        self.base_url = self._set_base_url(esmhost, api_version)
        self.int_url = 'https://{}/ess'.format(esmhost)
        self.login_url = 'https://{}/rs/esm/login'.format(esmhost)
        self._setup_auth(esmuser, esmpass)
        self.logged_in = False

    def _set_base_url(self, host, api_version):
        """ESM public URL setter"""
        if str(api_version) == '2':
            return 'https://{}/rs/esm/v2/'.format(host)
        elif str(api_version) == '1':
            return 'https://{}/rs/esm/'.format(host)
        else:
            raise ValueError('API Version must be 1 or 2.')

    def _setup_auth(self, user, passwd):
        """Interface to auth setup functions"""
        
        self._auth_data = {}
        self._auth_data['username'] = base64.b64encode(
                                        user.encode('utf-8')).decode()
        self._auth_data['password'] = base64.b64encode(
                                        passwd.encode('utf-8')).decode()
        self._auth_data['locale'] = 'en_US'
        self._auth_data['os'] = 'Win32'

    def login(self):
        method = 'login'
        cb = self._set_header
        self.post(method, data=self._auth_data, callback=cb, raw=True)

    def logout(self):
        """
        """
        method = 'logout'
        url = self._set_url(method)
        self.session.delete(url)
        
        
    def _set_header(self, resp):
        """Adds field to http header.
        
        Args:
            Requests response object.
        """
        self.session.add_header({'X-Xsrf-Token': 
                                    resp.headers.get('Xsrf-Token')})
        self.logged_in = True


    def _set_url(self, method):
        if method.isupper():
            url = self._int_url
            data = self._format_priv_params(method, **data)
        elif method is 'login':
            url = self.login_url
        else:
            url = ''.join([self.base_url, method])
        return url

    def post(self, method, data=None, callback=None, raw=False):
        url = self._set_url(method)
        resp = self.session.post(url, data=data)
        if raw:
            data = resp
        else:
            data = self._unpack_resp(resp)

        if callback:
            return callback(data)
        return data
        
    def _unpack_resp(self, response):
        """Unpack data from response.

        Args: 
            response: requests response object

        """
        data = None
        try:
            if isinstance(response.json(), list):
                data = response.json()
            elif isinstance(response.json(), dict):
                try:
                    data = response.json()['value']
                except KeyError:
                    try:
                        response.json()['return']
                    except KeyError:
                        data = response.json()
            return data
        except json.decoder.JSONDecodeError: 
                return

    def watchlist_fields(self):
        method = 'sysGetWatchlistFields'
        return self.post(method)


    def watchlist_summary(self):
        method = 'sysGetWatchlists?hidden=false&dynamic=false&writeOnly=false&indexedOnly=false'
        return self.post(method)

    def get_watchlist_details(self, w_id):
        method = 'sysGetWatchlistDetails'
        data = {'id': w_id}
        return self.post(method, data=data)

    def export_watchlist(self, w_id):
        wl_data = []
        file_size = 0
        bytes_read = 0

        wl_details = self.get_watchlist_details(w_id)
        filename = wl_details.get('valueFile').get('fileToken')
        file_data = self._get_watchlist_vals(filename, bytes_read)
        
        wl_data.append(file_data.get('data'))
        bytes_read += file_data.get('bytesRead')
        while bytes_read != file_data.get('fileSize'):
            file_data = self._get_watchlist_vals(filename, bytes_read)
            bytes_read += file_data.get('bytesRead')
            wl_data.append(file_data.get('data'))
        return wl_data

    def _get_watchlist_vals(self, w_id, byte_pos):
        method = 'sysGetWatchlistValues?pos={}&count=0'.format(byte_pos)
        data = {"file": {"id": w_id}}
        return self.post(method, data=data)

def format_filename(text):
    return text.replace(' ', '_').lower() + '_watchlist.txt'
        
def main():
    
    config = ESMConfig()
    esm = ESM(config)
    esm.login()
    watchlists = esm.watchlist_summary()
    
    for wl in watchlists:
        wl_data = esm.export_watchlist(wl['id'])
        wl_data = ''.join(wl_data)
        filename = format_filename(wl['name'])
        with open(filename, 'w') as f:
            f.write(wl_data)
    esm.logout()
                
if __name__ == "__main__":
    try:
        main()
        
    except KeyboardInterrupt:
        logging.warning("Control-C Pressed, stopping...")
        sys.exit()

        
        