import json
import os
import requests
import re


class Session:
    base_url = "https://web.spaggiari.eu/rest/v1"

    def __init__(self, username: str = None, password: str = None):
        self.logged_in  = False
        self.first_name = None
        self.last_name  = None
        self.id         = None

        self.username = username
        self.password = password
        self.token    = None

        self.session = requests.Session()

        self.session.headers["User-Agent"] = "CVVS/std/4.2.3 Android/12"
        self.session.headers["z-dev-apikey"] = "Tg1NWEwNGIgIC0K"
        self.session.headers["Content-Type"] = "application/json"

    def login(self, username: str = None, password: str = None):
        """
        Login to Classe Viva API
        :param username: Classe Viva username or email
        :param password: Classe Viva password
        :type username: str
        :type password: str
        :return: ID, first name and last name
        :rtype: dict
        """

        r = self.session.post(
            url=self.base_url + "/auth/login/",
            json={
                "uid" : self.username,
                "pass": self.password,
            }
        ).json()

        if 'authentication failed' in r.get('error', ''):
            raise AuthenticationFailedError()

        self.logged_in  = True
        self.first_name = r['firstName']
        self.last_name  = r['lastName']
        self.token      = r['token']
        self.tokenAP    = r['tokenAP']
        self.ident      = r['ident']
        self.id         = re.sub(r"\D", "", r['ident'])


    def circolari(self):
        self.session.headers['z-auth-token'] = self.token
        url_richiesta = self.base_url + "/teachers/" + self.id + "/noticeboard?fc=138037"
        r = self.session.get(
            url=url_richiesta,
            headers=self.session.headers
        ).json()
        circolari = r['items']
        for c in circolari:
            print(c['cntTitle'])
            print(c['pubId'])
            
        tmp_circolare = circolari[0]
        url_lettura = f"{self.base_url}/teachers/{self.id}/noticeboard/read/CF/{tmp_circolare['pubId']}/101"
        r = self.session.post(
            url=url_lettura,
            headers=self.session.headers
        )

        url_allegato = f"{self.base_url}/teachers/{self.id}/noticeboard/attach/CF/{tmp_circolare['pubId']}/1"
        r = self.session.get(
            url=url_allegato,
            headers=self.session.headers
        )
        with open(tmp_circolare['attachments'][0]['fileName'], "wb") as f:
            f.write(r.content)
        


s = Session(username="noit0005.1020809", password="bwfN-c92t-DREy-cr40")
s.login()
s.circolari()
