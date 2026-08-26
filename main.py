import json
import os
import requests
import re
from dotenv import dotenv_values


class Session:
    base_url = "https://web.spaggiari.eu/rest/v1"
    login_url = base_url + "/auth/login/"
    timeout = 30
    download_path = "/home/fabio/Nextcloud/Fauser/circolari25/"

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
        url_login_php = "https://web.spaggiari.eu/auth-p7/app/default/AuthApi4.php?a=aLoginPwd"
        dati_raw = f"cid=&uid={self.username}&pwd={self.password}&pin=&target="
        r = self.session.post(
            url=url_login_php,
            data=dati_raw,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            timeout=self.timeout
            )
        #print(r.json())
        # cerca il cookie di sessione per nome: l'ordine in cui il server
        # restituisce i cookie non e' garantito
        self.phpsessid = next(
            (c.value for c in self.session.cookies if c.name == "PHPSESSID"), None
        )
        if self.phpsessid is None:
            print("login al sito classico fallito: PHPSESSID non ricevuto")
            return False
        return True


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
            },
            timeout=self.timeout
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
        # header del sito classico, diversi da quelli dell'app usati per le API REST:
        # valgono solo per questa richiesta, non per tutta la sessione
        headers = {
            "host": "web.spaggiari.eu",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.5",
            "accept-encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "referer": "https://web.spaggiari.eu/cvv/app/default/gioprof_colloqui.php",
            "cookie": f"webrole=userdoc; webidentity={self.ident}; PHPSESSID={self.phpsessid}",
        }

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
            headers=headers,
            timeout=self.timeout
        )
        print(r)
        return True

    def circolari(self, verbose=False):
        self.session.headers['z-auth-token'] = self.token
        url_richiesta = self.base_url + "/teachers/" + self.id + "/noticeboard?fc=138037"
        r = self.session.get(
            url=url_richiesta,
            headers=self.session.headers,
            timeout=self.timeout
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
            headers=self.session.headers,
            timeout=self.timeout
        )

        for num_allegato, el in enumerate(circolare['attachments'], start=1):
            filepath = self.download_path + el['fileName']
            if os.path.exists(filepath):
                print(f"circolare {circolare['cntTitle']} gia' scaricata")
                continue

            url_allegato = f"{self.base_url}/teachers/{self.id}/noticeboard/attach/CF/{circolare['pubId']}/{num_allegato}"
            r = self.session.get(
                url=url_allegato,
                headers=self.session.headers,
                timeout=self.timeout
            )
            print(f"Nuova circolare: {circolare['cntTitle']}")
            with open(filepath, "wb") as f:
                f.write(r.content)


def main():
    config = dotenv_values()
    s = Session(username=config['USERNAME'], password=config['PASSWORD'])
    if not s.login():
        return 1
    if not s.login_php():
        return 1
    s.imposta_colloquio('2026-04-14', 5, '12:10', '12:50')
    s.imposta_colloquio('2026-04-21', 5, '12:10', '12:50')
    s.imposta_colloquio('2026-04-28', 5, '12:10', '12:50')
    s.imposta_colloquio('2026-05-05', 5, '12:10', '12:50')
    s.imposta_colloquio('2026-05-12', 5, '12:10', '12:50')
    s.imposta_colloquio('2026-05-19', 5, '12:10', '12:50')
    s.imposta_colloquio('2026-05-26', 5, '12:10', '12:50')
    #s.circolari(True)
    #for i, c in enumerate(s.lista_circolari):
    #     if c['cntCategory'] == 'Circolare':
    #         s.download_circolare(i)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
