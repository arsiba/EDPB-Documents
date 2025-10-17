from bs4 import BeautifulSoup
import os

from edpb_scraper.downloader import download_file

BASE_URL = "https://www.edpb.europa.eu"

def parse_documents(soup):
    """Extract document entries from a BeautifulSoup page"""
    document_items = soup.find_all("div", class_="views-row")
    result = []
    for item in document_items:
        is_obsolete = item.find('div', class_='publication-status status-obsolete mb-1') is not None
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
            title = "No title found"
            document_url = "No URL found"

        download_links = (
                item.find_all("a", class_="download")
                + item.find_all("a", class_="file-download")
                + item.find_all("a", class_="download-link")
        )

        result.append({
            "title": title,
            "document_url": document_url,
            "download_links": download_links,
            "is_obsolete": is_obsolete
        })
    return result

def scrape_page(session, base_url, folder, downloaded_index, index_file, page_number=0):
    """Scrape documents from one page"""
    import requests
    url = f"{base_url}?page={page_number}"
    print(f"\nScraping page {page_number + 1}: {url}")
    new_downloads = 0
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        docs = parse_documents(soup)
        for doc in docs:
            if doc["is_obsolete"]:
                continue
            for link in doc["download_links"]:
                href = link.get("href")
                if not href:
                    continue
                download_url = href if href.startswith("http") else BASE_URL + href
                filename = os.path.basename(download_url.split("?")[0])
                if download_file(session, download_url, filename, folder, downloaded_index, index_file):
                    new_downloads += 1
        return new_downloads, len(docs)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return 0, 0
