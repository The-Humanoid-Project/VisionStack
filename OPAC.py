import requests
from bs4 import BeautifulSoup

class OPACInterface:
    
    def __init__(self):
        self.url = "https://opac.library.iitb.ac.in/cgi-bin/koha/opac-search.pl"
        self.PARAMS = {
            "idx": "bc",
            "limit": 1
        }

    def get_book_details(self, q_tag):
        self.PARAMS["q"] = q_tag
        
        response = requests.get(self.url, params=self.PARAMS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.find('h1', class_='title').text.strip()
            language = soup.find("span", class_="language").text.split()[1]
            subject = soup.find_all("a", class_="subject")[1].text.strip()
            call_no = soup.find("td", class_="call_no").text.strip()
            availability = soup.find("td", class_="status").span.text.strip()
            due_date = soup.find("td", class_="date_due").text.strip()
            barcode = soup.find("td", class_="barcode").text.strip()
            
            description = {
                "title": title,
                "language": language,
                "subject": subject,
                "call_no": call_no,
                "availability": availability,
                "due_date": due_date,
                "barcode": barcode
            }
            return description
        else:
            return "Some error occurred while fetching book details!"

if __name__ == "__main__":
    opac_interface = OPACInterface()
    q_tag = 247148  # Example q tag value
    book_details = opac_interface.get_book_details(q_tag)
    print(book_details)