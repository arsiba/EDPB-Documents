# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os
import time


BASE_URL = "https://www.edpb.europa.eu"
DOCUMENTS_URL = BASE_URL + "/our-work-tools/consistency-findings/register-for-article-60-final-decisions_en"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}
DOWNLOAD_DIR = "oss_documents"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_file(url, filename):
    try:
        response = requests.get(url, stream=True, headers=HEADERS)
        response.raise_for_status()
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Datei heruntergeladen: {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Herunterladen von {url}: {e}")
        return False

def scrape_documents(base_url):
    documents = []
    page_number = 0

    while True:
        current_url = f"{base_url}?page={page_number}"
        print(f"\nScraping Seite {page_number + 1}: {current_url}")
        try:
            response = requests.get(current_url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            document_items = soup.find_all('div', class_='views-row')

            if not document_items:
                print("Keine weiteren Dokumente gefunden.")
                break

            for idx, item in enumerate(document_items, 1):
                is_obsolete = item.find('div', class_='publication-status status-obsolete mb-1') is not None
                title_element = item.find('h4', class_='document-title') or item.find('h3', class_='document-title') or item.find('h4', class_='item-title') or item.find('h3', class_='item-title')
                if title_element and title_element.a:
                    title = title_element.a.text.strip()
                    document_url = BASE_URL + title_element.a['href']
                else:
                    title = "Kein Titel gefunden"
                    document_url = "Keine URL gefunden"

                download_links = item.find_all('a', class_='download') + item.find_all('a', class_='file-download') + item.find_all('a', class_='download-link')

                print(f"\nDokument {idx} auf Seite {page_number + 1}")
                print(f"Titel: {title}")
                print(f"URL: {document_url}")
                print(f"Obsolet: {'Ja' if is_obsolete else 'Nein'}")
                print(f"Anzahl Dateien zum Download: {len(download_links)}")

                if is_obsolete:
                    print("Überspringe veraltetes Dokument.")
                    continue

                for link in download_links:
                    download_url = BASE_URL + link['href']
                    filename = download_url.split('/')[-1]
                    if download_file(download_url, filename):
                        documents.append({'title': title, 'url': document_url, 'downloaded_as': filename})
                    time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Zugriff auf {current_url}: {e}")
            break

        page_number += 1
        time.sleep(1)

    return documents

if __name__ == "__main__":
    print(f"Starte Scraper für {DOCUMENTS_URL}")
    all_documents = scrape_documents(DOCUMENTS_URL)
    print("\nScraping abgeschlossen.")
    print(f"Anzahl heruntergeladener Dokumente: {len([doc for doc in all_documents if doc.get('downloaded_as')])}")
    for doc in all_documents:
        print(f"Titel: {doc['title']}")
        print(f"URL: {doc['url']}")
        print(f"Heruntergeladen als: {doc.get('downloaded_as', 'Nicht heruntergeladen')}")
        print("-" * 30)
