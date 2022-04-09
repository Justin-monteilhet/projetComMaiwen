from ast import Str
from typing import Dict, List
import json
from collections import namedtuple
from datetime import datetime
import requests as rq
from getpass import getpass

from ftfy import fix_text

Credentials = namedtuple('Credentials', ['username', 'password'])

class Transaction:
    def __init__(self, value:int, date:str, label:str) -> None:
        self.value, self.label = value, fix_text(label)
        self.date = datetime.strptime(date, "%Y-%m-%d")

    def to_json(self) -> dict:
        return {
            "value" : self.value,
            "label" : self.label,
            "date" : self.date.strftime("%Y-%m-%d")
        }

    @classmethod
    def from_json(cls, d:dict):
        return cls(d['montant'], d['date'], d['libelle'])

class URL:
    login = "https://api.ecoledirecte.com/v3/login.awp?v=4.6.0"
    timeline = "https://api.ecoledirecte.com/v3/1/2830/timelineAccueilCommun.awp?verbe=get&v=4.6.0"
    detail = "https://api.ecoledirecte.com/v3/comptes/detail.awp?verbe=get&v=4.6.0"

class APISession:
    def __init__(self, token:str) -> None:
        self.token = token
        self._session = rq.Session()

    @classmethod
    def from_credentials(cls, username:str, password:str):
        login_credentials = "data=" + json.dumps({"identifiant" : username, "motdepasse" : password})
        login = rq.post(URL.login, data=login_credentials)
        login_data = login.json()

        return cls(login_data.get("token"))

    @property
    def names(self) -> List[str]:
        """Names of the students associated to the parent account."""
        accs_data = self._request_token(url=URL.timeline)

        accounts = [acc for acc in accs_data['data']['comptes']['comptes'] if acc["typeCompte"] == "portemonnaie"]
        names = []
        for acc in accounts:
            libelle = acc.get("libelle")  # for example PM_RESTO JAMES
            name = libelle[libelle.find(' ')+1:].lower()
            names.append(name)
            
        return names

    @property
    def solds(self) -> dict:
        """Returns a dict binding student name to his account sold"""
        accs_data = self._request_token(url=URL.timeline)

        accounts = [acc for acc in accs_data['data']['comptes']['comptes'] if acc["typeCompte"] == "portemonnaie"]
        solds = {}
        for acc in accounts:
            sold = acc['solde']
            libelle = acc.get("libelle")  # for example PM_RESTO JAMES
            name = libelle[libelle.find(' ')+1:].lower()
            solds[name] = sold
            
        return solds

    @property
    def sold_logs(self) -> Dict[str, List[Transaction]]:
        detailed_data = self._request_token(url=URL.detail)
        accounts = [acc for acc in detailed_data['data']['comptes'] if acc['typeCompte'] == "portemonnaie"]
        
        all_transactions = {}   # student name -> List of his transactions json formatted
        for account in accounts:
            libelle = account.get("libelle") 
            name = libelle[libelle.find(' ')+1:].lower()
            transactions = []

            for trans in account['ecritures']:
                if not trans['montant'] : continue
                if trans['montant'] > 0:
                    transactions.append(Transaction.from_json(trans))
                    continue

                # if here, this trans is negative and groups all the purchases
                for purchase in trans['ecritures']:
                    purchase['montant'] *= -1   # transaction becomes negative
                    transactions.append(Transaction.from_json(purchase))

            # sort transactions by datetime
            transactions.sort(key=lambda x:x.date, reverse=True)
            all_transactions[name] = transactions
        
        return all_transactions
    

    def _request_token(self, url):
        headers = {'x-token' : self.token}
        r = self._session.post(url, headers=headers, data="data={}")
        return r.json()


def main():
    s = rq.Session()
    
    login_url = "https://api.ecoledirecte.com/v3/login.awp?v=4.6.0"
    timeline_url = "https://api.ecoledirecte.com/v3/1/2830/timelineAccueilCommun.awp?verbe=get&v=4.6.0  "

    username = input("Nom d'utilisateur du compte parent : ")
    password = getpass("Mot de passe du compte parent : ")

    form_data = {
        "identifiant" : username,
        "motdepasse" : password
    }

    r = s.post(login_url, data=f"data={json.dumps(form_data)}" )

    response = r.json()
    token = response.get('token')

    r = s.post(timeline_url, headers={'x-token' : token}, data='data={}')

    timeline_data = r.json().get('data')

    with open('timeline.json', 'w') as f:
        f.write(json.dumps(timeline_data, indent=2))

    accounts = timeline_data["comptes"]["comptes"]
    accounts = [acc for acc in accounts if acc["typeCompte"] == "portemonnaie"]
    
    names = {}  # bindes names to account index in accounts
    for i, acc in enumerate(accounts):
        libelle = acc.get("libelle")  # for example PM_RESTO JAMES
        name = libelle[libelle.find(' ')+1:].lower()
        names[name] = i
    
    for name, index in names.items():
        print(f'{index+1}) {name.title()}')
    
    while 1:
        user_index = input("Entrez le chiffre devant votre nom : ")
        if user_index.isdigit() :
            if 0 < int(user_index) <= len(names) :
                break
        print("Incorrect. Veuillez entrer le chiffre devant votre nom.")
    
    user_index = int(user_index)
    user_index -= 1    # goes back from user input to correct index 

    user_acc = accounts[user_index]
    sold = user_acc.get("solde")
    
    print(f"Vous avez actuellement €{sold}.")

    # https://api.ecoledirecte.com/v3/comptes/detail.awp?verbe=get&v=4.6.0



if __name__ == '__main__' : main()