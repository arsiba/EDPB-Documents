# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os
import time
import random

BASE_URL = "https://www.edpb.europa.eu"
DOCUMENTS_URL = BASE_URL + "/our-work-tools/consistency-findings/register-for-article-60-final-decisions_en"
DOWNLOAD_DIR = "article_60"

# realistischere Browser-Header
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.edpb.europa.eu/",
    "Connection": "keep-alive",
}

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_file(session, url, filename):
    """Lädt eine Datei herunter."""
    try:
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Datei heruntergeladen: {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Herunterladen von {url}: {e}")
        return False

def scrape_documents(base_url):
    """Scraped alle Dokumentseiten."""
    session = requests.Session()
    session.headers.update(HEADERS)
    documents = []
    page_number = 0

    while True:
        current_url = f"{base_url}?page={page_number}"
        print(f"\nScraping Seite {page_number + 1}: {current_url}")

        try:
            response = session.get(current_url, timeout=30)
            if response.status_code == 403:
                print("403 Forbidden – zu viele Anfragen. Warte 60 Sekunden und versuche erneut...")
                time.sleep(60)
                response = session.get(current_url, timeout=30)
                if response.status_code == 403:
                    print("Erneut 403. Breche ab.")
                    break

            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            document_items = soup.find_all("div", class_="views-row")

            if not document_items:
                print("Keine weiteren Dokumente gefunden.")
                break

            for idx, item in enumerate(document_items, 1):
                # robustere Erkennung des Titels
                title_element = (
                    item.find("h4", class_="document-title")
                    or item.find("h3", class_="document-title")
                    or item.find("h4", class_="item-title")
                    or item.find("h3", class_="item-title")
                    or item.find("a")
                )
                if title_element and title_element.get("href"):
                    title = title_element.text.strip()
                    document_url = BASE_URL + title_element["href"]
                else:
                    title = "Kein Titel gefunden"
                    document_url = "Keine URL gefunden"

                download_links = (
                    item.find_all("a", class_="download")
                    + item.find_all("a", class_="file-download")
                    + item.find_all("a", class_="download-link")
                )

                print(f"Dokument {idx} auf Seite {page_number + 1}")
                print(f"Titel: {title}")
                print(f"URL: {document_url}")
                print(f"Anzahl Dateien: {len(download_links)}")

                for link in download_links:
                    href = link.get("href")
                    if not href:
                        continue
                    download_url = href if href.startswith("http") else BASE_URL + href
                    filename = os.path.basename(download_url.split("?")[0])
                    if download_file(session, download_url, filename):
                        documents.append({
                            "title": title,
                            "url": document_url,
                            "downloaded_as": filename,
                        })
                    time.sleep(random.uniform(0.5, 1.5))

        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Zugriff auf {current_url}: {e}")
            break

        page_number += 1
        sleep_time = random.uniform(3, 7)
        print(f"Warte {sleep_time:.1f} Sekunden vor nächster Seite...")
        time.sleep(sleep_time)

    return documents

if __name__ == "__main__":
    print(f"Starte Scraper für {DOCUMENTS_URL}")
    all_documents = scrape_documents(DOCUMENTS_URL)
    print("\nScraping abgeschlossen.")
    print(f"Anzahl heruntergeladener Dokumente: {len([d for d in all_documents if d.get('downloaded_as')])}")

    for doc in all_documents:
        print(f"Titel: {doc['title']}")
        print(f"URL: {doc['url']}")
        print(f"Heruntergeladen als: {doc.get('downloaded_as', 'Nicht heruntergeladen')}")
        print("-" * 40)
