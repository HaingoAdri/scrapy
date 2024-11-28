import scrapy
import csv
import random

# Middleware pour utiliser un User-Agent aléatoire
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
]

class GoogleScraper(scrapy.Spider):
    name = 'google_scraper'
    allowed_domains = ['google.com']

    # Ignorer robots.txt
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
                if url:  # Vérifier que l'URL n'est pas vide
                    yield scrapy.Request(
                        url,
                        callback=self.parse,
                        headers={"User-Agent": random.choice(USER_AGENTS)},
                        dont_filter=True
                    )

    def parse(self, response):
        # Sauvegarder le HTML pour vérifier ce qui est récupéré
        with open("response.html", "wb") as f:
            f.write(response.body)

        # Extraire le titre depuis l'élément ciblé
        title = response.xpath("//div[@class='PZPZlf ssJ7i B5dxMb']/text()").get()

        # Extraire l'adresse depuis l'élément ciblé
        address = response.xpath("//div[@class='zloOqf PZPZlf']//span[@class='LrzXr']/text()").get()

        # Renvoyer le titre et l'adresse dans la sortie
        yield {
            'title': title.strip() if title else None,  # Enlever les espaces superflus
            'address': address.strip() if address else None,  # Enlever les espaces superflus
            'url': response.url
        }