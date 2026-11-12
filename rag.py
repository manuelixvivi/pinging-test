import os
import glob
import re
import math
from collections import Counter
from typing import List, Dict, Any

class SimpleRAG:
    """
    Sistem pencarian pengetahuan lokal ringan (BM25 / Keyword Similarity).
    Mendukung format .pdf, .docx, .md, .txt, dan .json tanpa dependensi cloud.
    """
    def __init__(self, kb_dir: str = "./knowledge"):
        if not os.path.isabs(kb_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.kb_dir = os.path.normpath(os.path.join(base_dir, kb_dir))
        else:
            self.kb_dir = kb_dir

        self.chunks: List[Dict[str, Any]] = []
        self.doc_freqs: Counter = Counter()
        self.num_chunks: int = 0
        self.avg_chunk_len: float = 0.0
        self.file_chunk_counts: Counter = Counter()
        self.load_documents()

    def _tokenize(self, text: str) -> List[str]:
        # Pisahkan huruf dan angka agar "SGD200" atau "USD100" menjadi ["sgd", "200"], ["usd", "100"]
        tokens = re.findall(r'[a-zA-Z]{2,}|[0-9]+', text.lower())
        stopwords = {
            "yang", "di", "dan", "dari", "ini", "itu", "untuk", "pada", "adalah", "dengan",
            "ke", "oleh", "sebagai", "atau", "dalam", "bisa", "the", "and", "is", "of", "in",
            "to", "a", "for", "with", "on", "as", "by", "at", "from"
        }
        return [t for t in tokens if t not in stopwords]

    def _extract_text_from_file(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        content = ""

        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                pages_text = []
                for p in reader.pages:
                    txt = p.extract_text()
                    if txt:
                        pages_text.append(txt)
                content = "\n\n".join(pages_text)
            except Exception as e:
                print(f"[RAG] Gagal membaca PDF {file_path}: {e}")
        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                content = "\n\n".join(paragraphs)
            except Exception as e:
                print(f"[RAG] Gagal membaca DOCX {file_path}: {e}")
        elif ext in [".xlsx", ".xlsm"]:
            content = self._extract_text_from_excel(file_path)
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                print(f"[RAG] Gagal membaca teks {file_path}: {e}")

        return content

    def _extract_text_from_excel(self, file_path: str) -> str:
        """Ekstrak data dari file spreadsheet Excel (.xlsx, .xlsm) menjadi teks terstruktur dan tabel Markdown"""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
            output_parts = []

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                raw_rows = []
                for row in ws.iter_rows(values_only=True):
                    cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                    if any(cleaned_row):
                        while cleaned_row and not cleaned_row[-1]:
                            cleaned_row.pop()
                        if cleaned_row:
                            raw_rows.append(cleaned_row)

                if not raw_rows:
                    continue

                sheet_text = [f"# Lembar Kerja (Sheet): {sheet_name}"]

                # Cari baris header (baris pertama dengan >= 2 kolom terisi)
                header_idx = -1
                for idx, r in enumerate(raw_rows):
                    non_empty = [c for c in r if c]
                    if len(non_empty) >= 2:
                        header_idx = idx
                        break

                if header_idx != -1:
                    # Ambil baris judul sebelum header jika ada
                    for title_row in raw_rows[:header_idx]:
                        sheet_text.append(" ".join([c for c in title_row if c]))

                    headers = raw_rows[header_idx]
                    data_rows = raw_rows[header_idx + 1:]

                    # 1. Rincian per baris (Key-Value) untuk pencarian keyword akurat
                    sheet_text.append("\n## Data & Rincian Baris:")
                    for r_num, row in enumerate(data_rows, start=header_idx + 2):
                        pairs = []
                        for h, val in zip(headers, row):
                            if h and val:
                                pairs.append(f"{h}: {val}")
                        if pairs:
                            sheet_text.append(f"- [Baris {r_num}] " + " | ".join(pairs))

                    # 2. Format Tabel Markdown agar LLM melihat struktur kolom
                    sheet_text.append("\n## Tabel:")
                    header_line = "| " + " | ".join(headers) + " |"
                    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
                    sheet_text.append(header_line)
                    sheet_text.append(sep_line)
                    for row in data_rows:
                        padded = row + [""] * (len(headers) - len(row))
                        row_line = "| " + " | ".join(padded[:len(headers)]) + " |"
                        sheet_text.append(row_line)
                else:
                    for r in raw_rows:
                        sheet_text.append(" | ".join([c for c in r if c]))

                output_parts.append("\n\n".join(sheet_text))

            return "\n\n---\n\n".join(output_parts)
        except Exception as e:
            print(f"[RAG] Gagal membaca Excel {file_path}: {e}")
            return ""

    def load_documents(self, force_rebuild: bool = False):
        self.chunks = []
        self.file_chunk_counts = Counter()
        total_tokens = 0

        if not os.path.exists(self.kb_dir):
            os.makedirs(self.kb_dir, exist_ok=True)
            return

        # 0. Cek apakah ada file indeks terkompilasi (kb_index.json.gz) untuk pemuatan instan (<0.3s) di cloud/Vercel
        cache_path = os.path.join(self.kb_dir, "kb_index.json.gz")
        if not force_rebuild and os.path.exists(cache_path):
            try:
                import gzip
                import json
                with gzip.open(cache_path, "rt", encoding="utf-8") as f:
                    cached = json.load(f)
                self.chunks = cached.get("chunks", [])
                self.num_chunks = cached.get("num_chunks", len(self.chunks))
                self.avg_chunk_len = cached.get("avg_chunk_len", 0.0)
                self.doc_freqs = Counter(cached.get("doc_freqs", {}))
                self.file_chunk_counts = Counter(cached.get("file_chunk_counts", {}))
                print(f"[RAG] Berhasil memuat instan {self.num_chunks} fragmen dokumen dari '{cache_path}'.")
                return
            except Exception as cache_err:
                print(f"[RAG] Gagal membaca cache terkompilasi ({cache_err}), memuat dari file mentah...")

        extensions = ["*.md", "*.txt", "*.pdf", "*.docx", "*.json", "*.xlsx", "*.xlsm"]
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.kb_dir, ext)))

        for file_path in files:
            content = self._extract_text_from_file(file_path)
            if not content.strip():
                continue

            fname = os.path.basename(file_path)
            doc_topic = re.sub(r'^(?:web_[a-z0-9_\-]+_|document_|bca_)', '', fname, flags=re.I)
            doc_topic = os.path.splitext(doc_topic)[0]
            doc_topic = re.sub(r'[_.\-]+', ' ', doc_topic).strip()

            # Chunking cerdas: gabungkan bagian-bagian pendek agar chunk memiliki konteks utuh
            raw_sections = re.split(r'\n(?=#{1,4}\s)|\n\n+', content)
            grouped_sections = []
            current_group = ""

            for sec in raw_sections:
                sec_clean = sec.strip()
                if not sec_clean:
                    continue
                if len(current_group) + len(sec_clean) < 500:
                    current_group += "\n" + sec_clean if current_group else sec_clean
                else:
                    if current_group:
                        grouped_sections.append(current_group)
                    current_group = sec_clean
            if current_group:
                grouped_sections.append(current_group)

            chunk_count_for_file = 0
            for sec_clean in grouped_sections:
                if len(sec_clean) < 20:
                    continue
                full_chunk_text = f"[{doc_topic}]\n{sec_clean}"
                tokens = self._tokenize(full_chunk_text)
                if not tokens:
                    continue
                total_tokens += len(tokens)
                chunk_count_for_file += 1
                self.chunks.append({
                    "file": fname,
                    "text": full_chunk_text,
                    "tokens": tokens,
                    "tf": Counter(tokens)
                })

            self.file_chunk_counts[fname] = chunk_count_for_file

        self.num_chunks = len(self.chunks)
        self.avg_chunk_len = (total_tokens / self.num_chunks) if self.num_chunks > 0 else 1.0

        # Hitung Document Frequencies
        self.doc_freqs = Counter()
        for chunk in self.chunks:
            unique_tokens = set(chunk["tokens"])
            for t in unique_tokens:
                self.doc_freqs[t] += 1

        print(f"[RAG] Berhasil memuat {self.num_chunks} fragmen dokumen dari {len(files)} file di '{self.kb_dir}'.")
        self.save_precompiled_index()

    def save_precompiled_index(self):
        """Simpan indeks ke file .json.gz terkompresi untuk pemuatan kilat (<0.3s)"""
        try:
            import gzip
            import json
            cache_path = os.path.join(self.kb_dir, "kb_index.json.gz")
            serializable_chunks = []
            for c in self.chunks:
                serializable_chunks.append({
                    "file": c["file"],
                    "text": c["text"],
                    "tokens": c["tokens"],
                    "tf": dict(c["tf"])
                })
            data = {
                "num_chunks": self.num_chunks,
                "avg_chunk_len": self.avg_chunk_len,
                "doc_freqs": dict(self.doc_freqs),
                "file_chunk_counts": dict(self.file_chunk_counts),
                "chunks": serializable_chunks
            }
            with gzip.open(cache_path, "wt", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"[RAG] Berhasil menyimpan indeks {self.num_chunks} fragmen ke '{cache_path}'.")
        except Exception as e:
            print(f"[RAG] Gagal menyimpan cache terkompilasi: {e}")

    def get_file_list(self) -> List[Dict[str, Any]]:
        """Mengembalikan daftar semua file patokan beserta ukuran dan jumlah fragmennya"""
        if not os.path.exists(self.kb_dir):
            return []

        results = []
        for fname in os.listdir(self.kb_dir):
            fpath = os.path.join(self.kb_dir, fname)
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                size_kb = round(stat.st_size / 1024, 1)
                mtime = stat.st_mtime
                chunks_count = self.file_chunk_counts.get(fname, 0)
                ext = os.path.splitext(fname)[1].lower().replace(".", "")
                results.append({
                    "name": fname,
                    "size_kb": size_kb,
                    "modified": mtime,
                    "chunks": chunks_count,
                    "type": ext
                })

        # Urutkan berdasarkan waktu modifikasi terbaru
        results.sort(key=lambda x: x["modified"], reverse=True)
        return results

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        if not self.chunks or not query:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = []
        k1 = 1.5
        b = 0.75

        for idx, chunk in enumerate(self.chunks):
            score = 0.0
            doc_len = len(chunk["tokens"])
            tf = chunk["tf"]

            for q in query_tokens:
                if q in tf:
                    freq = tf[q]
                    df = self.doc_freqs.get(q, 1)
                    idf = math.log((self.num_chunks - df + 0.5) / (df + 0.5) + 1.0)
                    numerator = freq * (k1 + 1)
                    denominator = freq + k1 * (1 - b + b * (doc_len / self.avg_chunk_len))
                    score += idf * (numerator / denominator)

            if score > 0:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scores[:top_k]]
