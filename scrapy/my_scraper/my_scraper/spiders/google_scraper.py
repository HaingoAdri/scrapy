import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import random

# Middleware pour utiliser un User-Agent aléatoire
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
]

class GoogleScraper(scrapy.Spider):
    name = 'google_scraper'  # Nom unique pour le spider
    allowed_domains = ['google.com']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'RETRY_TIMES': 5,
    }

    def start_requests(self):
        # Lire les URLs depuis le fichier CSV
        with open('urls.csv', mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row['url'].strip()  # Obtenir l'URL et enlever les espaces
                id_value = row['id']  # Obtenir l'ID depuis le fichier CSV
                if url:  # Vérifier que l'URL n'est pas vide
                    yield scrapy.Request(
                        url,
                        callback=self.parse,
                        headers={"User-Agent": random.choice(USER_AGENTS)},
                        dont_filter=True,
                        meta={'id': id_value}  # Passer l'ID dans les meta données de la requête
                    )

    def parse(self, response):
        # Configuration de Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Exécuter Chrome en mode headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        # Ouvrir l'URL dans Selenium
        driver.get(response.url)

        # Attendre que la page soit complètement chargée (ajuster si nécessaire)
        time.sleep(3)

        # Extraire le HTML après le rendu avec Selenium
        sel = Selector(text=driver.page_source)

        # Extraction des titres principaux avec plusieurs sources possibles
        title = sel.xpath("//div[@data-attrid='title']/text()").get()
        title_h2 = sel.xpath("//h2[@data-attrid='title']/span/text()").get()
        ntt = sel.xpath("//div[@class='PZPZlf ssJ7i xgAzOe' and @data-attrid='title']/text()").get()
        new_title = sel.xpath("//div[@class='PZPZlf ssJ7i B5dxMb' and @data-attrid='title']/text()").get()
        
        final_title = title or title_h2 or new_title or ntt  # Combine titles

        # Extraction de l'adresse
        address = sel.xpath("//div[@data-local-attribute='d3adr']//span[@class='LrzXr']/text()").get()
        address_alt = sel.xpath("//div[@data-local-attribute='d3adr']//span[@class='LrzXr']/text()").get()
        final_address = address or address_alt  # Combine addresses

        phone_number = sel.xpath("//div[@data-local-attribute='d3ph']//span[@aria-label]//text()").get()
        
        # Extraction des horaires d'ouverture
        hours = {}
        
        for row in sel.xpath("//tbody/tr"):
            day = row.xpath("td[1]/text()").get()  # Le premier <td> contient le jour
            time_range = row.xpath("td[2]/text()").get()  # Le second <td> contient l'horaire
            
            if day and time_range:
                if "Ouvert 24h/24" in time_range:
                    hours[day.strip().lower()] = "00:00–24:00"  # Changer en format souhaité pour 24 heures
                else:
                    hours[day.strip().lower()] = time_range.strip()

        # Si aucun horaire n'a été trouvé, essayer d'extraire à partir du second tableau sans classe dans <td>
        if not hours:  # If no hours were found in the first extraction
            for row in sel.xpath("//div[@class='b2JWxc']//table/tbody/tr"):
                day = row.xpath("td[1]/text()").get()  # Le premier <td> contient le jour sans classe
                time_range = row.xpath("td[2]/text()").get()  # Le second <td> contient l'horaire sans classe
                
                if day and time_range:
                    if "Ouvert 24h/24" in time_range:
                        hours[day.strip().lower()] = "00:00–24:00"  # Changer en format souhaité pour 24 heures
                    else:
                        hours[day.strip().lower()] = time_range.strip()

        if not hours:  # If no hours were found in the first extraction
            for row in sel.xpath("//table[@class='WgFkxc']/tbody/tr"):
                day = row.xpath("td[1]/text()").get()  # Le premier <td> contient le jour sans classe
                time_range = row.xpath("td[2]/text()").get()  # Le second <td> contient l'horaire sans classe
                
                if day and time_range:
                    if "Ouvert 24h/24" in time_range:
                        hours[day.strip().lower()] = "00:00–24:00"  # Changer en format souhaité pour 24 heures
                    else:
                        hours[day.strip().lower()] = time_range.strip()

        # Extraction de l'URL du site web
        url = sel.xpath("//a[contains(@class, 'n1obkb mI8Pwc')]/@href").get()

        # Extraire la note 
        rating = sel.xpath("//span[@class='Aq14fc']/text()").get()

        # Extraire le texte des avis Google et convertir en entier
        reviews_text = sel.xpath("//a[@data-async-trigger='reviewDialog']/span/text()").get()
        
        reviews = None  # Initialiser reviews à None par défaut
        if reviews_text:
            reviews = int(''.join(filter(str.isdigit, reviews_text)))

        owners_count_elements = sel.xpath("//div[contains(@class, 'PhaUTe')]").get()

        # Vérification de la présence de la div spécifique pour la description
        description_present = sel.xpath('//div[@class="wDYxhc NFQFxe" and @data-attrid="kc:/local:merchant_description"]')

        if description_present:
            description_status = "OK"
            description_text = description_present.xpath('./text()').get(default=None) or None  # Récupérer le texte s'il existe.
            description_text = description_text.strip() if description_text else None 
        else:
            description_status = "NOK"
            description_text = None

        # Fermer le navigateur Selenium
        driver.quit()

        yield {
            'title': final_title.strip() if final_title else None,
            'address': final_address.strip() if final_address else None,
            'phone': phone_number.strip() if phone_number else None,  
            'url': url.strip() if url else None,  
            'source_url': response.url,  
            'hours': hours,  
            'id': response.meta.get('id'),  
            'rating': rating.strip() if rating else None,
            'owners_count': owners_count_elements.strip() if owners_count_elements else None,
            'reviews': reviews,
            'description_status': description_status,  # OK ou NOK selon la présence de la description 
            'description_text': description_text,      # Texte de la description si disponible 
        }
