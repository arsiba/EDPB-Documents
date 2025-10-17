BASE_URL = "https://www.edpb.europa.eu"

URLS = [
    {"url": BASE_URL + "/our-work-tools/consistency-findings/register-for-article-60-final-decisions_en",
     "folder": "article_60"},
    {"url": BASE_URL + "/our-work-tools/documents/our-documents_en",
     "folder": "our_documents"}
]

INDEX_FILE = "../index.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL + "/",
    "Connection": "keep-alive",
}
