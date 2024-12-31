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

class AppleMapsScraper(scrapy.Spider):
    name = 'apple_maps_scraper'  # Nom unique pour le spider
    allowed_domains = ['maps.apple.com']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'RETRY_TIMES': 5,
    }

    def start_requests(self):
        # Lire les URLs depuis le fichier CSV
        with open('url_apple.csv', mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row['url'].strip()  # Obtenir l'URL et enlever les espaces
                if url:  # Vérifier que l'URL n'est pas vide
                    yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Configurer Selenium pour fonctionner en mode headless
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

        # Essayer d'extraire le titre
        title = sel.xpath("//h1[@class='sc-header-title']/text()").get()

        # Si le titre n'est pas trouvé, essayer d'extraire à partir de l'autre classe
        if not title:
            title = sel.xpath("//div[@class='PZPZlf ssJ7i xgAzOe']/text()").get()

        # Extraire le numéro de téléphone (valeur après "tel:")
        phone_link = sel.xpath("//a[contains(@href, 'tel:')]/@href").get()
        phone = phone_link.split(":")[-1] if phone_link else None

        website_url = sel.xpath("//a[contains(@class, 'sc-unified-action-row-item') and div[@class='sc-unified-action-row-title mw-dir-label'][text()='Site web']]/@href").get()

        # Extraire l'adresse
        address_parts = sel.xpath("//div[contains(@class, 'sc-platter-cell-content')]/div[@dir='ltr']/text()").getall()
        address = ", ".join(part.strip() for part in address_parts) if address_parts else None

        # Extraire les horaires d'ouverture pour "Tous les jours"
        hours = {}
        
        everyday_hours = sel.xpath("//div[contains(@class, 'sc-hours-row sc-hours-everyday')]")
        
        if everyday_hours:
            day_range = everyday_hours.xpath(".//div[contains(@class, 'sc-day-range')]/text()").get()
            time_range = everyday_hours.xpath(".//div[contains(@class, 'sc-time-range')]/span/text()").getall()
            if day_range and time_range:
                hours[day_range.strip()] = " ".join(time_range).strip()

        # Si aucun horaire n'a été trouvé, essayer d'extraire à partir des autres horaires
        if not hours:  # Vérifier si le dictionnaire est vide
            opening_rows = sel.xpath("//div[contains(@class, 'sc-hours-unfolded')]//div[contains(@class, 'sc-hours-row')]")
            
            for row in opening_rows:
                day_range = row.xpath(".//div[contains(@class, 'sc-hours-day')]/text()").get()
                time_range = row.xpath(".//div[contains(@class, 'sc-time-range')]/span/text()").getall()
                if day_range and time_range:
                    hours[day_range.strip()] = " ".join(time_range).strip()

        # Fermer le navigateur Selenium
        driver.quit()

        yield {
            'title': title.strip() if title else None,
            'phone': phone,
            'website': website_url.strip() if website_url else None,
            'address': address,
            'hours': hours,
            'url': response.url
        }