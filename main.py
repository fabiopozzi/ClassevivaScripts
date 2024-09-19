import json
import os
import requests
import re
from dotenv import dotenv_values


class Session:
    base_url = "https://web.spaggiari.eu/rest/v1"
    login_url = base_url + "/auth/login/"
    download_path = "/home/fabio/Nextcloud/Fauser/circolari24/"

    def __init__(self, username: str = None, password: str = None):
        self.logged_in  = False
        self.first_name = None
        self.last_name  = None
        self.id         = None
        self.lista_circolari = None

        self.username = username
        self.password = password
        self.token    = None
        self.phpsessid = None

        self.session = requests.Session()

        self.session.headers["User-Agent"] = "CVVS/std/4.2.3 Android/12"
        self.session.headers["z-dev-apikey"] = "Tg1NWEwNGIgIC0K"
        self.session.headers["Content-Type"] = "application/json"

    def login_php(self):
        self.session.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        url_login_php = "https://web.spaggiari.eu/auth-p7/app/default/AuthApi4.php?a=aLoginPwd"
        dati_raw = f"cid=&uid={self.username}&pwd={self.password}&pin=&target="
        r = self.session.post(
            url=url_login_php,
            data=dati_raw
            )
        #print(r.json())
        #print(len(r.cookies))
        for cookie in r.cookies:
            # print(cookie.name)
            # print(cookie.value)
            # print(cookie.domain)
            self.phpsessid = cookie.value
            break


    def login(self):
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
            url=self.login_url,
            json={
                "uid" : self.username,
                "pass": self.password,
            }
        ).json()

        if 'authentication failed' in r.get('error', ''):
            print(r['error'])
            return False
            #raise AuthenticationFailedError()

        self.logged_in  = True
        self.first_name = r['firstName']
        self.last_name  = r['lastName']
        self.token      = r['token']
        self.tokenAP    = r['tokenAP']
        self.ident      = r['ident']
        self.id         = re.sub(r"\D", "", r['ident'])
        return True

    def imposta_colloquio(self, data, num_ora, ora_inizio, ora_fine):
        self.session.headers["host"] = "web.spaggiari.eu"
        self.session.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        self.session.headers["accept"] = "*/*"
        self.session.headers["accept-language"] = "en-US,en;q=0.5"
        self.session.headers["accept-encoding"] = "gzip, deflate, br"
        self.session.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.session.headers["referer"] = "https://web.spaggiari.eu/cvv/app/default/gioprof_colloqui.php"
        self.session.headers["cookie"] = f"webrole=userdoc; webidentity={self.ident}; PHPSESSID={self.phpsessid}"

        dati = {
                'action': 'confpopupdoc',
                'ora': num_ora,
                'luogo': 'sede centrale',
                'evento_data': data,
                'genitori': 4,
                'ora_prec': num_ora, # da capire
                'data_prec': data, # da capire
                'autore_id': self.ident,
                'ora_ini': ora_inizio,
                'ora_fin': ora_fine,
                'checkboxall': 'false'
                }
        url_colloquio = "https://web.spaggiari.eu/cvv/app/default/gioprof_colloqui.php"
        r = self.session.post(
            url=url_colloquio,
            data=dati,
            headers=self.session.headers
        )
        print(r)
        return True

    def circolari(self, verbose=False):
        self.session.headers['z-auth-token'] = self.token
        url_richiesta = self.base_url + "/teachers/" + self.id + "/noticeboard?fc=138037"
        r = self.session.get(
            url=url_richiesta,
            headers=self.session.headers
        ).json()
        self.lista_circolari = r['items']

        if verbose:
            for c in self.lista_circolari:
                if c['cntCategory'] == 'Circolare':
                    # print(c)
                    print(f"{c['pubDT'].split('T')[0]} - {c['pubId']} - {c['cntTitle']}")

    def download_circolare(self, pos_circolare):
        circolare = self.lista_circolari[pos_circolare]

        url_lettura = f"{self.base_url}/teachers/{self.id}/noticeboard/read/CF/{circolare['pubId']}/101"
        r = self.session.post(
            url=url_lettura,
            headers=self.session.headers
        )

        url_allegato = f"{self.base_url}/teachers/{self.id}/noticeboard/attach/CF/{circolare['pubId']}/1"
        r = self.session.get(
            url=url_allegato,
            headers=self.session.headers
        )
        filepath = self.download_path + circolare['attachments'][0]['fileName']
        if not os.path.exists(filepath):
            print(f"Nuova circolare: {circolare['cntTitle']}")
            with open(filepath, "wb") as f:
                f.write(r.content)
        else:
            print(f"circolare {circolare['cntTitle']} gia' scaricata")

config = dotenv_values()
# print(config['USERNAME'])
# print(config['PASSWORD'])
s = Session(username=config['USERNAME'], password=config['PASSWORD'])
risultato = s.login()
s.login_php()
s.imposta_colloquio('2024-09-27', 5, '12:00', '12:50')
#s.circolari(True)
# for i, c in enumerate(s.lista_circolari):
#     if c['cntCategory'] == 'Circolare':
#         s.download_circolare(i)
