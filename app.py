import os
import time
import json
import re
import base64
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

from rag import SimpleRAG
from scraper import scrape_url_to_knowledge

# Load konfigurasi dari .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_KEYS = os.getenv("GROQ_API_KEYS", "") or GROQ_API_KEY
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

LOCAL_KB_DIR = os.getenv("LOCAL_KB_DIR", "./knowledge")

# ====================================================
# Multi-Key Pool & Auto-Failover Manager
# ====================================================
class KeyPool:
    def __init__(self, raw_keys: str):
        self.keys = []
        for k in re.split(r'[,;\n\r]+', raw_keys):
            clean = k.strip()
            if clean and clean.startswith("gsk_") and clean not in self.keys:
                self.keys.append(clean)
        self.cooldowns: Dict[str, float] = {}

    def add_key(self, key: str) -> bool:
        clean = key.strip()
        if clean and clean.startswith("gsk_") and clean not in self.keys:
            self.keys.append(clean)
            return True
        return False

    def remove_key(self, key: str) -> bool:
        if key in self.keys:
            self.keys.remove(key)
            return True
        return False

    def mark_limited(self, key: str, wait_seconds: float = 60.0):
        self.cooldowns[key] = time.time() + wait_seconds
        print(f"[KeyPool] Kunci ...{key[-6:]} masuk masa jeda cooldown {wait_seconds:.1f} detik.")

    def get_available_keys(self) -> List[str]:
        now = time.time()
        ready = [k for k in self.keys if self.cooldowns.get(k, 0) <= now]
        if ready:
            return ready
        if self.keys:
            return sorted(self.keys, key=lambda k: self.cooldowns.get(k, 0))
        return []

    def get_status_list(self) -> List[Dict[str, Any]]:
        now = time.time()
        results = []
        for idx, k in enumerate(self.keys):
            expire = self.cooldowns.get(k, 0)
            is_cooling = expire > now
            wait_left = max(0, int(expire - now)) if is_cooling else 0
            results.append({
                "index": idx + 1,
                "masked": f"gsk_...{k[-6:]}",
                "status": "cooldown" if is_cooling else "ready",
                "wait_seconds": wait_left,
                "key": k
            })
        return results

key_pool = KeyPool(GROQ_API_KEYS)

# Inisialisasi Simple RAG
rag = SimpleRAG(kb_dir=LOCAL_KB_DIR)

# Riwayat audit pemindaian & bukti dokumen yang dibaca
solve_history = []

app = FastAPI(title="AI Browser Assistant Backend", version="0.2.0")

# Setup CORS untuk extension browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptionItem(BaseModel):
    id: Optional[str] = None
    label: Optional[str] = None
    text: Optional[str] = None

class SolveRequest(BaseModel):
    screenshot: Optional[str] = None   # Base64 data URL (e.g. data:image/jpeg;base64,...)
    html: Optional[str] = None
    question_context: Optional[str] = None
    options: Optional[List[OptionItem]] = None
    provider: Optional[str] = None     # 'groq' atau 'openai'

class SolveResponse(BaseModel):
    status: str
    answer: str
    matched_text: Optional[str] = None
    confidence: str
    provider_used: str
    references_used: int = 0
    ocr_text: Optional[str] = None
    error: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "name": "AI Browser Assistant Backend",
        "version": "0.2.0",
        "status": "running",
        "default_provider": DEFAULT_PROVIDER,
        "kb_chunks": rag.num_chunks
    }

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "default_provider": DEFAULT_PROVIDER,
        "ollama_configured": True,
        "ollama_model": OLLAMA_MODEL,
        "groq_configured": bool(GROQ_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "kb_chunks": rag.num_chunks
    }

@app.get("/simulation", response_class=HTMLResponse)
def get_simulation_page():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_simulation.html"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_page", "quiz_simulation.html")),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Halaman simulasi tidak ditemukan</h1>", status_code=404)

# ====================================================
# Knowledge Base Manager Web UI & Endpoints
# ====================================================

@app.get("/kb", response_class=HTMLResponse)
def get_kb_manager_page():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb_manager.html"),
        os.path.join(os.getcwd(), "kb_manager.html"),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Halaman Knowledge Base Manager tidak ditemukan</h1>", status_code=404)

@app.get("/api/kb/files")
def list_kb_files():
    files = rag.get_file_list()
    return {
        "status": "ok",
        "total_files": len(files),
        "total_chunks": rag.num_chunks,
        "files": files
    }

@app.post("/api/kb/upload")
async def upload_kb_files(files: List[UploadFile] = File(...)):
    saved_files = []
    for upload in files:
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', upload.filename)
        dest_path = os.path.join(rag.kb_dir, safe_name)
        with open(dest_path, "wb") as f:
            content = await upload.read()
            f.write(content)
        saved_files.append(safe_name)
    
    # Re-index
    rag.load_documents()
    return {
        "status": "ok",
        "uploaded": saved_files,
        "total_chunks": rag.num_chunks
    }

class TextDocRequest(BaseModel):
    title: str
    content: str

class ScrapeUrlRequest(BaseModel):
    url: str
    max_pages: Optional[int] = 1
    title: Optional[str] = None

@app.post("/api/kb/scrape")
async def scrape_website_to_kb(req: ScrapeUrlRequest):
    try:
        res = await scrape_url_to_knowledge(
            start_url=req.url, 
            max_pages=req.max_pages or 1, 
            custom_title=req.title
        )
        dest_path = os.path.join(rag.kb_dir, res["filename"])
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(res["content"])
        
        # Re-index RAG
        rag.load_documents()
        return {
            "status": "ok",
            "filename": res["filename"],
            "pages_scraped": res["pages_scraped"],
            "title": res["primary_title"],
            "total_chunks": rag.num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil website: {str(e)}")

@app.post("/api/kb/text")
def save_kb_text(doc: TextDocRequest):
    safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '_', doc.title.strip())
    if not safe_title:
        safe_title = "catatan_referensi"
    filename = f"{safe_title}.md"
    dest_path = os.path.join(rag.kb_dir, filename)

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(f"# {doc.title}\n\n{doc.content.strip()}\n")

    rag.load_documents()
    return {
        "status": "ok",
        "filename": filename,
        "total_chunks": rag.num_chunks
    }

@app.delete("/api/kb/files/{filename}")
def delete_kb_file(filename: str):
    safe_name = os.path.basename(filename)
    target_path = os.path.join(rag.kb_dir, safe_name)
    if os.path.exists(target_path):
        os.remove(target_path)
        rag.load_documents()
        return {"status": "ok", "deleted": safe_name, "total_chunks": rag.num_chunks}
    raise HTTPException(status_code=404, detail="File tidak ditemukan")

@app.get("/api/kb/view/{filename}", response_class=PlainTextResponse)
def view_kb_file(filename: str):
    safe_name = os.path.basename(filename)
    target_path = os.path.join(rag.kb_dir, safe_name)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    text = rag._extract_text_from_file(target_path)
    return text

@app.get("/api/kb/search")
def search_kb(q: str):
    results = rag.search(q, top_k=4)
    return {
        "query": q,
        "total_results": len(results),
        "results": [{"file": r["file"], "text": r["text"]} for r in results]
    }

@app.get("/api/kb/history")
def get_kb_history():
    return {
        "status": "ok",
        "total": len(solve_history),
        "history": list(reversed(solve_history))
    }

def save_keys_to_env():
    """Simpan pool kunci API ke file .env agar tidak hilang saat server restart"""
    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            found = False
            joined_keys = ",".join(key_pool.keys)
            for line in lines:
                if line.startswith("GROQ_API_KEYS="):
                    new_lines.append(f"GROQ_API_KEYS={joined_keys}\n")
                    found = True
                elif line.startswith("GROQ_API_KEY=") and key_pool.keys:
                    new_lines.append(f"GROQ_API_KEY={key_pool.keys[0]}\n")
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"GROQ_API_KEYS={joined_keys}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
    except Exception as e:
        print(f"[KeyPool] Gagal simpan ke .env: {e}")

class KeyAddRequest(BaseModel):
    key: str

@app.get("/api/keys")
def get_api_keys():
    return {
        "status": "ok",
        "total": len(key_pool.keys),
        "keys": key_pool.get_status_list()
    }

@app.post("/api/keys")
def add_api_key(req: KeyAddRequest):
    added = key_pool.add_key(req.key)
    if added:
        save_keys_to_env()
        return {"status": "ok", "message": "Kunci API berhasil ditambahkan ke pool failover", "keys": key_pool.get_status_list()}
    raise HTTPException(status_code=400, detail="Format kunci API tidak valid (harus gsk_...) atau kunci sudah terdaftar.")

@app.delete("/api/keys")
def remove_api_key(req: KeyAddRequest):
    removed = key_pool.remove_key(req.key)
    if removed:
        save_keys_to_env()
        return {"status": "ok", "message": "Kunci API berhasil dihapus", "keys": key_pool.get_status_list()}
    raise HTTPException(status_code=404, detail="Kunci API tidak ditemukan.")

@app.post("/api/refresh-kb")
def refresh_kb():
    rag.load_documents()
    return {"status": "ok", "total_chunks": rag.num_chunks}

def clean_json_response(content: str) -> Dict[str, Any]:
    """Ekstrak JSON murni dari output AI yang mungkin dibungkus markdown codeblock atau reasoning tags"""
    content = content.strip()
    # Hapus tag <think>...</think> jika model reasoning menyertakannya
    content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
    
    # Ekstrak dari blok codeblock ```json ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if match:
        content = match.group(1).strip()
    
    try:
        return json.loads(content)
    except Exception:
        # Cari pola objek JSON {...}
        json_match = re.search(r'(\{[\s\S]*\})', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass
        
        # Ekstrak field "answer": "..." jika parsing JSON utuh gagal
        ans_match = re.search(r'"answer"\s*:\s*"([^"]+)"', content, re.IGNORECASE)
        txt_match = re.search(r'"matched_text"\s*:\s*"([^"]+)"', content, re.IGNORECASE)
        if ans_match:
            return {
                "answer": ans_match.group(1).strip(),
                "matched_text": txt_match.group(1).strip() if txt_match else "",
                "confidence": "medium"
            }
        
        # Fallback jika model hanya menyebutkan huruf A/B/C/D
        match_letter = re.search(r'\b([A-E])\b', content, re.IGNORECASE)
        if match_letter:
            return {"answer": match_letter.group(1).upper(), "confidence": "medium"}
        return {"answer": "", "raw": content, "confidence": "low"}

def resolve_answer(parsed: dict, options: List[OptionItem]) -> tuple:
    ans = (parsed.get("answer") or "").strip().upper()
    matched = (parsed.get("matched_text") or "").strip()

    # Jika answer berupa "OPSI A" atau "PILIHAN B", ambil hurufnya
    m = re.search(r'\b([A-E])\b', ans)
    if m:
        ans = m.group(1).upper()

    # Jika answer kosong tapi matched_text ada, cari kecocokan di daftar opsi
    if not ans and options:
        matched_lower = matched.lower()
        for opt in options:
            opt_text_lower = (opt.text or "").lower()
            if opt_text_lower and (matched_lower in opt_text_lower or opt_text_lower in matched_lower):
                ans = (opt.label or "").upper()
                break
        
        # Jika masih belum ketemu, cari kemiripan kata kunci
        if not ans and matched:
            matched_words = [w for w in matched_lower.split() if len(w) > 3]
            for opt in options:
                opt_words = [w for w in (opt.text or "").lower().split() if len(w) > 3]
                common = set(matched_words) & set(opt_words)
                if len(common) >= 2:
                    ans = (opt.label or "").upper()
                    break

    # Jika answer berupa nomor (1, 2, 3, 4), petakan ke A, B, C, D jika opsi berhuruf
    if ans in ["1", "2", "3", "4", "5", "6"]:
        idx = int(ans) - 1
        if 0 <= idx < len(options) and options[idx].label:
            ans = options[idx].label.upper()

    # Fallback garansi: jika ans masih kosong, pastikan tidak mengembalikan string kosong
    if not ans:
        match_m = re.search(r'\b([A-D])\b', matched)
        if match_m:
            ans = match_m.group(1).upper()
        elif options and options[0].label:
            ans = options[0].label.upper()
        else:
            ans = "A"

    return ans, matched

NOISE_PATTERNS = [
    r"persyaratan layanan\s*\|\s*kebijakan privasi\s*\|\s*pelajari selengkapnya",
    r"pelajari selengkapnya",
    r"dibuat oleh ai berdasarkan sumber.*",
    r"arrow_back\s+ke notebook.*",
    r"\b(info_spark|link_2|thumb_up|thumb_down|flag)\b"
]

def clean_noise_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    for pat in NOISE_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def extract_options_from_text(text: str) -> List[OptionItem]:
    """Cari pola baris A. ... B. ... C. ... D. ... dari teks mentah"""
    if not text:
        return []
    lines = [line.strip() for line in re.split(r'[\r\n]+', text) if line.strip()]
    options = []
    
    for line in lines:
        m = re.match(r'^([A-Fa-f1-6])[\.\)\:\-]\s*(.+)$', line)
        if m:
            label = m.group(1).upper()
            opt_text = m.group(2).strip()
            if not any(n in opt_text.lower() for n in ["pelajari", "kebijakan", "persyaratan"]):
                options.append(OptionItem(label=label, text=opt_text))
    
    if len(options) < 2:
        matches = re.findall(r'(?:^|\s)([A-Ea-e])[\.\)\:\-]\s+([^A-E\.\n]{4,300})', text)
        if len(matches) >= 2:
            options = [OptionItem(label=m[0].upper(), text=m[1].strip()) for m in matches]
            
    return options

@app.post("/api/solve", response_model=SolveResponse)
async def solve_question(req: SolveRequest):
    # Prioritaskan Groq jika ada kunci API aktif di key pool (kecepatan 1-2 detik)
    active_groq_keys = key_pool.get_available_keys()
    req_prov = (req.provider or "").lower()
    if active_groq_keys and req_prov != "ollama_forced":
        provider = "groq"
    else:
        provider = (req.provider or DEFAULT_PROVIDER or "ollama").lower()
    
    ocr_extracted_text = ""
    # 0. Local OCR: Ekstrak teks langsung dari screenshot secara lokal di background worker thread
    if req.screenshot:
        try:
            import asyncio
            from ocr import extract_text_from_screenshot
            ocr_res = await asyncio.wait_for(
                asyncio.to_thread(extract_text_from_screenshot, req.screenshot),
                timeout=7.0
            )
            if ocr_res.get("success") and ocr_res.get("raw_text"):
                ocr_extracted_text = ocr_res.get("raw_text", "")
                ocr_q = ocr_res.get("question", "")
                ocr_opts = ocr_res.get("options", [])

                print("\n" + "="*65)
                print(" [LOCAL OCR] Teks Berhasil Diekstrak dari Screenshot:")
                print(f" Soal : {ocr_q[:150]}")
                if ocr_opts:
                    print(" Opsi :")
                    for o in ocr_opts:
                        print(f"   {o.get('label')}. {o.get('text')}")
                print("="*65 + "\n")

                # Gunakan hasil OCR jika teks DOM kosong atau tidak lengkap
                if (not req.question_context or len(req.question_context.strip()) < 15) and ocr_q:
                    req.question_context = ocr_q
                if (not req.options or len(req.options) < 2) and ocr_opts:
                    req.options = [OptionItem(label=o["label"], text=o["text"]) for o in ocr_opts]
        except Exception as ocr_err:
            print(f"[OCR Warning/Timeout] {ocr_err}")

    # Bersihkan noise/footer dari question_context dan html
    if req.question_context:
        req.question_context = clean_noise_text(req.question_context)
    if req.html:
        req.html = clean_noise_text(req.html)

    # Filter opsi jika ada yang berisi noise/disclaimer (misal "Pelajari selengkapnya")
    if req.options:
        req.options = [
            o for o in req.options 
            if not any(n in (o.text or "").lower() for n in ["pelajari selengkapnya", "persyaratan layanan", "kebijakan privasi", "dibuat oleh ai"])
        ]

    # Jika req.options kosong atau hanya 1, coba ekstrak dari req.html atau req.question_context
    if not req.options or len(req.options) < 2:
        extracted = extract_options_from_text(req.html or "")
        if len(extracted) >= 2:
            req.options = extracted
        elif req.question_context:
            extracted_from_q = extract_options_from_text(req.question_context)
            if len(extracted_from_q) >= 2:
                req.options = extracted_from_q

    # Fallback jaring pengaman: Jika question_context masih kosong/sangat pendek, gunakan teks halaman (req.html)
    if (not req.question_context or len(req.question_context.strip()) < 5) and req.html:
        clean_html = re.sub(r'<[^>]+>', ' ', req.html)
        clean_html = re.sub(r'\s+', ' ', clean_html).strip()
        req.question_context = clean_html[:2000]

    # 1. Kumpulkan teks untuk pencarian Knowledge Base
    search_query = req.question_context or ""
    if req.options:
        search_query += " " + " ".join([f"{o.label or ''} {o.text or ''}" for o in req.options])
    if not search_query.strip() and ocr_extracted_text:
        search_query = ocr_extracted_text
    if not search_query.strip() and req.html:
        # Ambil cuplikan teks dari HTML jika tidak ada question context
        search_query = re.sub(r'<[^>]+>', ' ', req.html)[:1000]

    # 2. Cari referensi yang cocok di Knowledge Base lokal
    # Untuk CPU lokal (Ollama), batasi top_k=3 dan pangkas teks agar proses inferensi CPU cepat (< 8 detik)
    top_k_count = 3 if provider == "ollama" else 5
    kb_results = rag.search(search_query, top_k=top_k_count)
    if provider == "ollama":
        kb_context = "\n---\n".join([f"[{item['file']}]\n{item['text'][:400]}" for item in kb_results])
    else:
        kb_context = "\n---\n".join([f"[Dari file: {item['file']}]\n{item['text']}" for item in kb_results])

    # 3. Format opsi jawaban
    options_formatted = ""
    if req.options:
        options_formatted = "\n".join([
            f"- Opsi {o.label or index}: {o.text}" 
            for index, o in enumerate(req.options, 1)
        ])

    system_prompt = (
        "Anda adalah asisten AI browser dalam mode 'Direct Answer' untuk simulasi dan kuis perbankan BCA (SOPAN).\n"
        "Tugas Anda: Analisis soal latihan/simulasi dari teks halaman, pilihan jawaban, dan referensi dokumen Knowledge Base jika tersedia.\n"
        "Tentukan opsi jawaban yang PALING BENAR secara presisi.\n\n"
        "PANDUAN KETELITIAN:\n"
        "- Baca dengan sangat cermat kata kunci pembatas / negasi (seperti: 'TIDAK mendapatkan fisik bilyet', 'bebas biaya', 'tanpa bilyet').\n"
        "- Tolak opsi pengecoh yang salah faktual meskipun terdengar meyakinkan (misal: 'menerima Bilyet fisik via kurir', 'mencetak di ATM BCA Multiguna', 'Safe Deposit Box').\n"
        "- Pada e-Deposito BCA, nasabah TIDAK mendapatkan fisik bilyet (tanpa bilyet fisik, transaksi dan catatan kepemilikan 100% digital di e-channel).\n\n"
        "ATURAN WAJIB:\n"
        "1. Jawab HANYA dalam format JSON valid berikut tanpa penjelasan, tanpa basa-basi:\n"
        "{\n"
        '  "answer": "HURUF_OPSI (misal A, B, C, D, E)",\n'
        '  "matched_text": "teks opsi yang benar persis seperti tertulis di halaman",\n'
        '  "confidence": "high | medium | low"\n'
        "}\n"
        "2. Pastikan 'matched_text' berisi kalimat/teks pilihan jawaban yang benar persis agar extension dapat menemukannya di halaman DOM.\n"
        "3. JANGAN sertakan alasan atau teks di luar JSON."
    )

    user_text = f"SOAL/KONTEKS HALAMAN:\n{req.question_context or 'Perhatikan teks halaman.'}\n\n"
    if options_formatted:
        user_text += f"PILIHAN OPSI JAWABAN:\n{options_formatted}\n\n"
    else:
        user_text += "PERHATIAN: Pilihan jawaban ada di dalam teks konteks/halaman di atas. Identifikasi opsi yang paling tepat, tuliskan hurufnya (A, B, C, D) di 'answer' dan teks pilihannya di 'matched_text'.\n\n"
    if kb_context:
        user_text += f"REFERENSI DOKUMEN KNOWLEDGE BASE:\n{kb_context}\n\n"
    user_text += "Berikan jawaban yang benar dalam format JSON sesuai instruksi."

    # Karena screenshot sudah di-OCR secara lokal menjadi teks murni, kita TIDAK perlu
    # mengirim gambar ke API cloud. Ini menghemat 100% token gambar dan jauh lebih hemat kuota!
    attach_screenshot = False

    # Siapkan pesan konten
    messages_content: List[Dict[str, Any]] = [{"type": "text", "text": user_text}]

    # Tambahkan screenshot hanya jika diperlukan (soal gambar/diagram tanpa teks)
    if attach_screenshot:
        img_url = req.screenshot
        if not img_url.startswith("data:image"):
            img_url = f"data:image/jpeg;base64,{img_url}"
        messages_content.append({
            "type": "image_url",
            "image_url": {"url": img_url}
        })

    # 4. Panggil model sesuai Provider dengan Auto-Failover Kunci API
    async with httpx.AsyncClient(timeout=30.0) as client:
        if provider == "groq":
            keys_to_try = key_pool.get_available_keys()
            if not keys_to_try:
                print("\n[AUTO-FAILOVER] Tidak ada kunci Groq API aktif! Mengoper otomatis ke Local AI (Ollama)...\n")
                provider = "ollama"
            else:
                groq_success = False
                last_err_msg = ""
                parsed = {}
                used_key = ""

                # Deteksi model penalaran (reasoning model) seperti openai/gpt-oss-20b atau r1
                is_reasoning_model = any(m in GROQ_MODEL.lower() for m in ["gpt-oss", "reasoning", "deepseek-r1"])

                for attempt_idx, key in enumerate(keys_to_try):
                    used_key = key
                    headers = {
                        "Authorization": f"Bearer {key}",
                        "User-Agent": "Mozilla/5.0"
                    }
                    payload = {
                        "model": GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": messages_content if attach_screenshot else user_text}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000 if is_reasoning_model else 500
                    }
                    # Jangan gunakan response_format strict untuk model reasoning agar tidak json_validate_failed
                    if not is_reasoning_model:
                        payload["response_format"] = {"type": "json_object"}

                    try:
                        res = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
                        if res.status_code == 429:
                            err_data = {}
                            try:
                                err_data = res.json().get("error", {})
                            except:
                                pass
                            msg = err_data.get("message", "")
                            
                            # Parse waktu jeda dari pesan error (contoh: "try again in 137.14ms" atau "try again in 5.4s")
                            wait_secs = 30.0
                            wait_ms = re.search(r'try again in ([\d\.]+)ms', msg)
                            if wait_ms:
                                wait_secs = max(0.1, float(wait_ms.group(1)) / 1000.0)
                            else:
                                wait_s = re.search(r'try again in ([\d\.]+)s', msg)
                                if wait_s:
                                    wait_secs = float(wait_s.group(1))

                            # Jika jeda sangat singkat (<= 2.0 detik), tunggu sebentar lalu coba lagi sekali
                            if wait_secs <= 2.0:
                                print(f"[AUTO-RETRY] Jeda hanya {wait_secs:.2f}s, menunggu sebentar...")
                                import asyncio
                                await asyncio.sleep(wait_secs + 0.15)
                                res_retry = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
                                if res_retry.status_code == 200:
                                    data = res_retry.json()
                                    content = data["choices"][0]["message"]["content"]
                                    parsed = clean_json_response(content)
                                    groq_success = True
                                    break

                            key_pool.mark_limited(key, wait_seconds=wait_secs)

                            print(f"\n[RATE LIMIT 429] Kunci ...{key[-6:]} terkena limit! Pesan: {msg[:80]}")
                            if attempt_idx < len(keys_to_try) - 1:
                                next_key = keys_to_try[attempt_idx + 1]
                                print(f"[AUTO-FAILOVER] Mengoper otomatis ke Kunci Cadangan berikutnya (...{next_key[-6:]})...\n")
                                continue
                            else:
                                last_err_msg = msg or "Semua kunci Groq sedang limit kuota."
                                break
                        elif res.status_code == 200:
                            data = res.json()
                            content = data["choices"][0]["message"]["content"]
                            parsed = clean_json_response(content)
                            groq_success = True
                            break
                        elif res.status_code == 400:
                            err_body = res.text
                            print(f"[Groq 400 Bad Request] Key ...{key[-6:]}: {err_body[:200]}")
                            # Jika karena JSON validator atau format, coba kirim sekali tanpa response_format
                            if "response_format" in payload:
                                del payload["response_format"]
                                payload["max_tokens"] = 1000
                                res_retry = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
                                if res_retry.status_code == 200:
                                    data = res_retry.json()
                                    content = data["choices"][0]["message"]["content"]
                                    parsed = clean_json_response(content)
                                    groq_success = True
                                    break
                            last_err_msg = err_body
                            break
                        else:
                            if attach_screenshot:
                                attach_screenshot = False
                                payload["messages"][1]["content"] = user_text
                                res = await client.post(f"{GROQ_BASE_URL}/chat/completions", headers=headers, json=payload)
                                if res.status_code == 200:
                                    data = res.json()
                                    content = data["choices"][0]["message"]["content"]
                                    parsed = clean_json_response(content)
                                    groq_success = True
                                    break
                            res.raise_for_status()
                    except Exception as e:
                        print(f"[Groq Exception] Key ...{key[-6:]}: {e}")
                        last_err_msg = str(e)
                        continue

                if not groq_success:
                    # Coba failover ke OpenAI jika ada kuota
                    if OPENAI_API_KEY:
                        print("[AUTO-FAILOVER] Semua kunci Groq limit! Mengoper otomatis ke OpenAI...")
                        try:
                            headers_oai = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
                            payload_oai = {
                                "model": OPENAI_MODEL,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_text}
                                ],
                                "response_format": {"type": "json_object"},
                                "temperature": 0.1,
                                "max_tokens": 150
                            }
                            res_oai = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers_oai, json=payload_oai)
                            if res_oai.status_code == 200:
                                data_oai = res_oai.json()
                                parsed = clean_json_response(data_oai["choices"][0]["message"]["content"])
                                groq_success = True
                                provider = "openai"
                        except Exception as oai_err:
                            print(f"[OpenAI Failover Error] {oai_err}")

                if not groq_success:
                    # Jika Groq dan OpenAI tidak berhasil, oper otomatis ke Local Ollama (100% Offline)
                    print(f"\n[AUTO-FAILOVER] Groq/OpenAI tidak tersedia ({last_err_msg[:60]}). Mengoper otomatis ke Local AI (Ollama)...\n")
                    provider = "ollama"
                else:
                    ans, matched = resolve_answer(parsed, req.options)
                    parsed["answer"] = ans
                    parsed["matched_text"] = matched

                    # Rekam ke riwayat audit & tampilkan di terminal
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    history_entry = {
                        "timestamp": timestamp,
                        "question": req.question_context or "(Soal dari screenshot)",
                        "answer": parsed.get("answer", ""),
                        "matched_text": parsed.get("matched_text", ""),
                        "confidence": parsed.get("confidence", "high"),
                        "ocr_text": ocr_extracted_text,
                        "provider": f"{provider} (...{used_key[-6:] if used_key else ''})",
                        "kb_references": [
                            {"file": item["file"], "snippet": item["text"][:350]}
                            for item in kb_results
                        ]
                    }
                    solve_history.append(history_entry)
                    if len(solve_history) > 30:
                        solve_history.pop(0)

                    print("\n" + "="*65)
                    print(f" [AI SOLVE] {timestamp} | Provider: {provider.upper()} (...{used_key[-6:] if used_key else ''})")
                    print(f" Soal: {(req.question_context or '')[:100]}...")
                    print(f" [RAG] Menemukan {len(kb_results)} Dokumen Referensi dari Knowledge Base:")
                    for i, r in enumerate(kb_results, 1):
                        print(f"   {i}. File: {r['file']}")
                        print(f"      Kutipan Teks: {r['text'][:120]}...")
                    print(f" [HASIL AI] Jawaban: {parsed.get('answer')} | Pilihan: {parsed.get('matched_text')}")
                    print("="*65 + "\n")

                    return SolveResponse(
                        status="success",
                        answer=parsed.get("answer", ""),
                        matched_text=parsed.get("matched_text", ""),
                        confidence=parsed.get("confidence", "high"),
                        provider_used=provider,
                        references_used=len(kb_results),
                        ocr_text=ocr_extracted_text
                    )

        if provider == "openai":
            if not OPENAI_API_KEY:
                raise HTTPException(status_code=500, detail="OPENAI_API_KEY belum dikonfigurasi di .env")

            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": messages_content}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 150
            }

            try:
                res = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                parsed = clean_json_response(content)
                ans, matched = resolve_answer(parsed, req.options)
                parsed["answer"] = ans
                parsed["matched_text"] = matched

                return SolveResponse(
                    status="success",
                    answer=parsed.get("answer", ""),
                    matched_text=parsed.get("matched_text", ""),
                    confidence=parsed.get("confidence", "high"),
                    provider_used="openai",
                    references_used=len(kb_results)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")

        if provider == "ollama":
            ollama_api_url = "http://127.0.0.1:11434/api/chat"
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100
                }
            }

            try:
                res = await client.post(ollama_api_url, json=payload, timeout=40.0)
                res.raise_for_status()
                data = res.json()
                content = data["message"]["content"]
                parsed = clean_json_response(content)
                ans, matched = resolve_answer(parsed, req.options)
                parsed["answer"] = ans
                parsed["matched_text"] = matched

                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                history_entry = {
                    "timestamp": timestamp,
                    "question": req.question_context or "(Soal dari screenshot)",
                    "answer": parsed.get("answer", ""),
                    "matched_text": parsed.get("matched_text", ""),
                    "confidence": parsed.get("confidence", "high"),
                    "ocr_text": ocr_extracted_text,
                    "provider": f"ollama ({OLLAMA_MODEL}) [100% OFFLINE]",
                    "kb_references": [
                        {"file": item["file"], "snippet": item["text"][:350]}
                        for item in kb_results
                    ]
                }
                solve_history.append(history_entry)
                if len(solve_history) > 30:
                    solve_history.pop(0)

                print("\n" + "="*65)
                print(f" [AI SOLVE - 100% OFFLINE] {timestamp} | Provider: OLLAMA ({OLLAMA_MODEL})")
                print(f" Soal: {(req.question_context or '')[:100]}...")
                print(f" [RAG] Menemukan {len(kb_results)} Dokumen Referensi dari Knowledge Base:")
                for i, r in enumerate(kb_results, 1):
                    print(f"   {i}. File: {r['file']}")
                print(f" [HASIL AI] Jawaban: {parsed.get('answer')} | Pilihan: {parsed.get('matched_text')}")
                print("="*65 + "\n")

                return SolveResponse(
                    status="success",
                    answer=parsed.get("answer", ""),
                    matched_text=parsed.get("matched_text", ""),
                    confidence=parsed.get("confidence", "high"),
                    provider_used=f"ollama ({OLLAMA_MODEL}) [100% OFFLINE]",
                    references_used=len(kb_results),
                    ocr_text=ocr_extracted_text
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ollama Error: {str(e)}. Pastikan service Ollama aktif di http://127.0.0.1:11434")

        else:
            raise HTTPException(status_code=400, detail=f"Provider tidak valid: {provider}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("app:app", host=host, port=port, reload=True)
