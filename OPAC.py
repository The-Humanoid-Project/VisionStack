import requests
import json
from bs4 import BeautifulSoup

class OPACInterface:
    
    def __init__(self):
        self.url = "https://opac.library.iitb.ac.in/cgi-bin/koha/opac-search.pl"
        self.PARAMS = {
            "idx": "bc",
            "q": 247148,
            "limit": 1
        }

    def get_book_details(self, opac_tag, cached):
        if cached:
            return
        else:
            self.PARAMS["q"] = opac_tag
            
            r = requests.get(self.url, self.PARAMS)
            if(r.status_code == 200):
                soup = BeautifulSoup(r.content, 'html5lib')
                
                title = soup.find('h1', attrs = {'class': 'title'}).text.strip()
                # authors = soup.find('span', attrs = {'property': "author", "typeof": "Person"}).span.text.split(", ")
                language = soup.find("span", attrs = {"class": "language"}).text.split()[1]
                subject = soup.find_all("a", attrs = {"class": "subject"})[1].text.strip()
                call_no = soup.find("td", attrs = {"class": "call_no"}).text.strip()
                availability = soup.find("td", attrs = {"class": "status"}).span.text.strip()
                due_date = soup.find("td", attrs = {"class": "date_due"}).text.strip()
                barcode = soup.find("td", attrs = {"class": "barcode"}).text.strip()
                
                description = {
                    "title": title,
                    # "authors": authors,
                    "language": language,
                    "subject": subject,
                    "call_no": call_no,
                    "availability": availability,
                    "due_date": due_date,
                    "barcode": barcode
                }
                return description
            else:
                return "Some error occured while fetching book details!"

if __name__ == "__main__":
    opacInterface = OPACInterface()      