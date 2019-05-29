# -*- coding: utf-8 -*-

import requests
requests.packages.urllib3.disable_warnings()

class HTTPClient(object):
    """Interface to HTTP session."""
    def __init__(self, cert_verify=False):
        """Initialize HTTP instance."""
        self.verify = cert_verify
        self.session = requests.session()
    
    def post(self, url, data=None, callback=None):
        """Interface to HTTP post"""
        response = self._post(url, data=data)
        if callback:
            return callback(response)
        return response

    def delete(self, url, data=None):
        """Interface to HTTP Delete"""
        return self.session.delete(url, json=data, verify=self.verify)


    def _post(self, url, data=None):
        return self.session.post(url, json=data, verify=self.verify)

    def add_header(self, headers):
        self.session.headers.update(headers)