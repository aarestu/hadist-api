import logging
import re
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LocalLLMHadithParserService:
    """Service layer for parsing Hadith Narrator, Narration, and Note using a Local LLM (Ollama)."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def check_local_llm_available(self) -> Optional[str]:
        """Memeriksa apakah LLM lokal (Ollama) aktif dan mengembalikan nama model yang tersedia."""
        try:
            resp = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                # Prioritaskan model generasi teks (bukan embedding)
                for m in models:
                    name = m.get("name", "")
                    if "embed" not in name and ("qwen" in name or "llama" in name or "mistral" in name or "deepseek" in name):
                        return name
                if models:
                    return models[0].get("name")
        except Exception:
            pass
        return None

    def parse_with_regex(self, text: str) -> Dict[str, str]:
        """Rule-based parsing fallback untuk ekstraksi presisi perawi, matan, dan note."""
        # 1. Ekstraksi Note terlebih dahulu dari bagian akhir teks
        note = "-"
        note_match = re.search(
            r"(Abu\s+'Abdullah\s+Al\s+Bukhari\s+berkata,.*$)", text, flags=re.IGNORECASE
        )
        hadith_body = text
        if note_match:
            note = note_match.group(1).strip().strip('"')
            hadith_body = text[: note_match.start()].strip()

        # 2. Ekstraksi Narrator (Sahabat/perawi terakhir dalam brackets [...] di hadith_body)
        brackets = re.findall(r"\[(.*?)\]", hadith_body)
        narrator = "-"
        if brackets:
            narrator = brackets[-1].strip("'").strip()
            # Hapus gelar radliallahu 'anhu / 'anha
            narrator = re.sub(
                r"\s*radliallahu\s+'anh(a|u)\s*", "", narrator, flags=re.IGNORECASE
            ).strip()

        # 3. Ekstraksi Narration (Matan/kejadian utama dari 'bahwa Rasulullah...' atau 'bahwa Nabi...')
        narration_match = re.search(
            r"bahwa\s+(Rasulullah|Nabi|Beliau).*$",
            hadith_body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if narration_match:
            narration = narration_match.group(0).strip()
        else:
            narration = hadith_body.strip()

        return {
            "narrator": narrator,
            "narration": narration,
            "note": note,
        }

    def parse_hadith(self, text: str) -> Optional[Dict[str, str]]:
        """Menganalisis teks hadis menggunakan Local LLM jika tersedia."""
        model_name = self.check_local_llm_available()
        if not model_name:
            logger.info("Local LLM (Ollama) tidak ditemukan. Fitur ekstraksi LLM dihilangkan.")
            return None

        # Gunakan regex parsing untuk ekstraksi presisi tinggi
        parsed = self.parse_with_regex(text)

        # Coba minta LLM merapikan/memvalidasi jika diperlukan
        try:
            prompt = (
                f"Analisis teks hadis berikut dan ekstrak 3 bagian:\n"
                f"1. Narrator: Nama sahabat/perawi terakhir di dalam tanda kurung siku sebelum isi hadits dimulai (tanpa gelar radliallahu 'anhu/'anha).\n"
                f"2. Narration: Isi utama matan/kejadian/sabda hadits.\n"
                f"3. Note: Catatan komentar imam perawi di akhir teks jika ada. Jika tidak ada, isi \"-\".\n\n"
                f"Teks Hadis:\n\"{text}\"\n\n"
                f"Format JSON persis:\n"
                f'{{"narrator": "{parsed["narrator"]}", "narration": "...", "note": "{parsed["note"]}"}}'
            )

            resp = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json().get("response", "")
                import json
                llm_json = json.loads(data)
                if isinstance(llm_json, dict) and "narration" in llm_json:
                    return {
                        "narrator": llm_json.get("narrator") or parsed["narrator"],
                        "narration": llm_json.get("narration") or parsed["narration"],
                        "note": llm_json.get("note") or parsed["note"],
                    }
        except Exception as e:
            logger.warning(f"Local LLM parsing error ({e}). Using regex parsed result.")

        return parsed
