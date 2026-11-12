import os
import re
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Set, Tuple
import httpx
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
}

def clean_html_to_text(html_content: str, source_url: str) -> Tuple[str, str, List[str]]:
    """
    Ekstrak teks bersih dan judul dari HTML, serta kumpulkan link internal.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ambil judul
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)
    if not title:
        title = urlparse(source_url).path.strip('/').replace('/', '_') or "Halaman Web"

    # Cari link internal sebelum menghapus tag
    internal_links = []
    base_domain = urlparse(source_url).netloc.lower()
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        full_url = urljoin(source_url, href)
        parsed = urlparse(full_url)
        # Pastikan domain sama dan skema http/https
        if parsed.scheme in ('http', 'https') and (parsed.netloc.lower() == base_domain or parsed.netloc.lower().endswith('.' + base_domain)):
            # Abaikan file binary/gambar
            if not re.search(r'\.(pdf|jpg|jpeg|png|gif|zip|rar|exe|svg)$', parsed.path, re.IGNORECASE):
                clean_url = full_url.split('#')[0]
                internal_links.append(clean_url)

    # Hapus elemen tidak relevan (script, style, header, footer, navigasi, ads)
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'svg', 'iframe']):
        tag.decompose()

    # Ekstrak struktur konten
    lines = []
    for el in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'th', 'blockquote', 'pre']):
        text = el.get_text(separator=' ', strip=True)
        if not text:
            continue
        tag_name = el.name
        if tag_name == 'h1':
            lines.append(f"\n# {text}\n")
        elif tag_name == 'h2':
            lines.append(f"\n## {text}\n")
        elif tag_name == 'h3':
            lines.append(f"\n### {text}\n")
        elif tag_name == 'li':
            lines.append(f"- {text}")
        else:
            lines.append(text)

    # Jika lines kosong, ambil semua teks tersisa
    if not lines:
        cleaned_body = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in cleaned_body.splitlines() if len(line.strip()) > 3]

    final_content = "\n\n".join(lines)
    # Rapikan spasi ganda
    final_content = re.sub(r'\n{3,}', '\n\n', final_content)

    return title, final_content, list(set(internal_links))

async def scrape_url_to_knowledge(start_url: str, max_pages: int = 1, custom_title: str = None) -> Dict[str, any]:
    """
    Mengunduh konten dari satu URL atau menjelajahi hingga max_pages halaman internal.
    """
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url

    parsed_root = urlparse(start_url)
    domain_name = parsed_root.netloc.replace('www.', '').replace('.', '_')

    visited: Set[str] = set()
    queue: List[str] = [start_url]
    collected_pages: List[Dict[str, str]] = []

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20.0) as client:
        while queue and len(visited) < max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                res = await client.get(current_url)
                if res.status_code == 200 and 'text/html' in res.headers.get('content-type', ''):
                    page_title, page_content, child_links = clean_html_to_text(res.text, current_url)
                    if len(page_content.strip()) > 50:
                        collected_pages.append({
                            "url": current_url,
                            "title": page_title,
                            "content": page_content
                        })
                        # Tambahkan link internal baru ke antrian
                        for link in child_links:
                            if link not in visited and link not in queue:
                                queue.append(link)
            except Exception as e:
                print(f"[Scraper] Gagal mengambil {current_url}: {e}")

    if not collected_pages:
        raise Exception(f"Gagal mengambil konten dari URL: {start_url}")

    # Buat nama file yang aman
    safe_title = custom_title or collected_pages[0]['title']
    safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '_', safe_title).strip()[:40] or "web_doc"
    filename = f"web_{domain_name}_{safe_title}.md"

    # Susun format Markdown
    doc_sections = [
        f"# Sumber Web: {domain_name} ({start_url})",
        f"Tanggal Pengambilan: Halaman diekstrak secara otomatis untuk Knowledge Base.\n"
    ]

    for p in collected_pages:
        doc_sections.append(f"## {p['title']}")
        doc_sections.append(f"*URL: {p['url']}*\n")
        doc_sections.append(p['content'])
        doc_sections.append("\n---\n")

    full_markdown = "\n\n".join(doc_sections)

    return {
        "filename": filename,
        "content": full_markdown,
        "pages_scraped": len(collected_pages),
        "domain": domain_name,
        "primary_title": collected_pages[0]['title']
    }
