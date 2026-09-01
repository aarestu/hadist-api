import json
import logging
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LocalLLMHadithParserService:
    """Service layer untuk parsing Hadis (Narrator, Narration, Note) murni menggunakan Local LLM (Ollama)."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url

    def check_local_llm_available(self) -> Optional[str]:
        """Memeriksa apakah LLM lokal (Ollama) aktif dan mengembalikan nama model yang tersedia."""
        try:
            resp = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                for m in models:
                    name = m.get("name", "")
                    if "embed" not in name and ("qwen" in name):
                        return name
                for m in models:
                    name = m.get("name", "")
                    if "embed" not in name and ("qwen" in name or "llama" in name or "mistral" in name):
                        return name
                if models:
                    return models[0].get("name")
        except Exception:
            pass
        return None

    def parse_hadith(self, text: str, lang: str = "Indonesian") -> Optional[Dict[str, str]]:
        """Menganalisis teks hadis murni menggunakan Local LLM. Jika LLM lokal tidak ada, kembalikan None."""
        model_name = self.check_local_llm_available()
        if not model_name:
            logger.info("Local LLM (Ollama) tidak ditemukan. Fitur ekstraksi LLM dihilangkan.")
            return None


        prompt = (

            f"Analisis dan ekstrak 3 bagian dari teks hadis ({lang}) berikut:\n"
            f"1. Narrator: Nama sahabat/perawi terakhir sebelum isi matan hadits dimulai (tanpa gelar radliallahu 'anhu/'anha).\n"
            f"2. Narration: Isi utama matan/kejadian/sabda hadits.\n"
            f"3. Note: Catatan takhrij atau komentar imam perawi di akhir teks (jika ada). Jika tidak ada, isi \"-\".\n\n"
            f"Teks Hadis:\n\"{text}\"\n\n"
            f"Berikan output JSON persis dalam format ini (tanpa teks tambahan):\n"
            f'{{"narrator": "...", "narration": "...", "note": "..."}} \n\n'
        )

        print(model_name)

        try:
            resp = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=30.0,
            )
            if resp.status_code == 200:
                raw_response = resp.json().get("response", "")
                llm_data = json.loads(raw_response)
                if isinstance(llm_data, dict):
                    return {
                        "narrator": str(llm_data.get("narrator", "-")),
                        "narration": str(llm_data.get("narration", "-")),
                        "note": str(llm_data.get("note", "-")),
                    }
        except Exception as e:
            logger.warning(f"Gagal melakukan parsing dengan Local LLM ({e}). Fitur ekstraksi dihilangkan.")

        return None
