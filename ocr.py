import base64
import io
import re
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

# Inisialisasi RapidOCR engine (singleton)
try:
    from rapidocr_onnxruntime import RapidOCR
    ocr_engine = RapidOCR()
except Exception as e:
    print(f"[OCR] RapidOCR tidak dapat diinisialisasi: {e}")
    ocr_engine = None

def extract_text_from_screenshot(image_b64: str) -> Dict[str, Any]:
    """
    Ekstrak teks soal dan opsi pilihan langsung dari screenshot menggunakan RapidOCR lokal.
    Mendukung format standar (A, B, C, D) dan format grid kartu Quizizz (2x2 Quadrant).
    """
    if not ocr_engine or not image_b64:
        return {
            "success": False,
            "raw_text": "",
            "question": "",
            "options": [],
            "lines": []
        }

    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_b64)
        pil_img = Image.open(io.BytesIO(image_bytes))

        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        w, h = pil_img.size
        img_np = np.array(pil_img)

        # Jalankan RapidOCR
        results, _ = ocr_engine(img_np, use_angle_cls=False)

        if not results:
            return {
                "success": True,
                "raw_text": "",
                "question": "",
                "options": [],
                "lines": []
            }

        # 1. Filter spasial: Abaikan hanya batas ekstrem layar (atas 2%, bawah 2%)
        filtered_items = []
        for box, txt, score in results:
            clean_txt = txt.strip()
            if not clean_txt or len(clean_txt) < 2:
                continue

            y_top = box[0][1]
            y_bottom = box[2][1]
            y_center = (y_top + y_bottom) / 2
            x_left = box[0][0]
            x_right = box[1][0]
            x_center = (x_left + x_right) / 2

            if y_center < h * 0.02 or y_center > h * 0.98:
                continue

            # Abaikan tombol navigasi kuis
            if clean_txt.lower() in ["petunjuk", "sebelumnya", "berikutnya", "kocak123", "opsiditandai", "bonus", "submit", "skip"]:
                continue

            filtered_items.append({
                "text": clean_txt,
                "box": box,
                "x_left": x_left,
                "x_right": x_right,
                "x_center": x_center,
                "y_top": y_top,
                "y_bottom": y_bottom,
                "y_center": y_center
            })

        # Periksa apakah ada opsi dengan huruf standar (A. B. C. D.)
        has_letter_options = any(re.match(r'^[A-Ea-e1-6][\.\)]\s*', item["text"]) for item in filtered_items)

        options = []
        question_text = ""
        raw_lines = []

        if has_letter_options:
            # Mode Standar Vertikal: Urutkan berdasarkan posisi Y
            filtered_items.sort(key=lambda item: item["y_center"])
            q_parts = []
            for item in filtered_items:
                txt = item["text"]
                raw_lines.append(txt)
                if re.match(r'^\d+[\/\.]\d+$', txt):
                    continue
                match_opt = re.match(r'^([A-Ea-e1-6])[\.\)]\s*(.*)$', txt)
                if match_opt:
                    options.append({
                        "label": match_opt.group(1).upper(),
                        "text": match_opt.group(2).strip()
                    })
                elif not options:
                    q_parts.append(txt)
                else:
                    options[-1]["text"] += " " + txt
            question_text = " ".join(q_parts).strip()

        else:
            # Mode Quizizz / Grid 2x2:
            # Area Atas (y < 42% tinggi layar) = Pertanyaan Soal
            # Area Bawah (y >= 42% tinggi layar) = Opsi Jawaban Grid 4 Kotak (Top-Left, Top-Right, Bottom-Left, Bottom-Right)
            split_y_question = h * 0.42
            split_y_options = (split_y_question + h * 0.95) / 2
            split_x = w * 0.50

            q_items = [it for it in filtered_items if it["y_center"] < split_y_question]
            opt_items = [it for it in filtered_items if it["y_center"] >= split_y_question]

            # Urutkan pertanyaan berdasarkan urutan baca (Y lalu X)
            q_items.sort(key=lambda it: (it["y_center"], it["x_center"]))
            question_text = " ".join([it["text"] for it in q_items]).strip()

            # Kelompokkan opsi ke dalam 4 Kuadran Quizizz:
            # Kuadran A / 1: Atas Kiri (Merah)
            # Kuadran B / 2: Atas Kanan (Biru)
            # Kuadran C / 3: Bawah Kiri (Kuning)
            # Kuadran D / 4: Bawah Kanan (Hijau)
            quadrants = {
                "A": [it for it in opt_items if it["x_center"] < split_x and it["y_center"] < split_y_options],
                "B": [it for it in opt_items if it["x_center"] >= split_x and it["y_center"] < split_y_options],
                "C": [it for it in opt_items if it["x_center"] < split_x and it["y_center"] >= split_y_options],
                "D": [it for it in opt_items if it["x_center"] >= split_x and it["y_center"] >= split_y_options]
            }

            for label in ["A", "B", "C", "D"]:
                items_in_q = quadrants[label]
                if items_in_q:
                    # Urutkan teks di dalam satu kotak kartu dari atas ke bawah
                    items_in_q.sort(key=lambda it: it["y_center"])
                    combined_text = " ".join([it["text"] for it in items_in_q]).strip()
                    options.append({
                        "label": label,
                        "text": combined_text
                    })

            # Jika kuadran tidak mendeteksi 4 kotak (misal format vertikal sederhana), fallback ke baris per baris
            if len(options) < 2 and opt_items:
                opt_items.sort(key=lambda it: it["y_center"])
                for idx, it in enumerate(opt_items[:4]):
                    options.append({
                        "label": chr(65 + idx),
                        "text": it["text"]
                    })

            raw_lines = [it["text"] for it in filtered_items]

        full_raw_text = "\n".join(raw_lines)

        return {
            "success": True,
            "raw_text": full_raw_text,
            "question": question_text,
            "options": options,
            "lines": raw_lines
        }
    except Exception as err:
        print(f"[OCR] Error: {err}")
        return {
            "success": False,
            "raw_text": "",
            "question": "",
            "options": [],
            "lines": [],
            "error": str(err)
        }
