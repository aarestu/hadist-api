import logging
import re
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LocalLLMHadithParserService:
    """Service layer for parsing Hadith Narrator, Narration, and Note using Local LLM (Ollama) with Multi-language support."""

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
                    if "embed" not in name and ("qwen" in name or "llama" in name or "mistral" in name or "deepseek" in name):
                        return name
                if models:
                    return models[0].get("name")
        except Exception:
            pass
        return None

    def parse_indonesian(self, text: str) -> Dict[str, str]:
        """Ekstraksi teks Bahasa Indonesia."""
        note = "-"
        note_match = re.search(
            r"(Abu\s+'Abdullah\s+Al\s+Bukhari\s+berkata,.*$)", text, flags=re.IGNORECASE
        )
        hadith_body = text
        if note_match:
            note = note_match.group(1).strip().strip('"')
            hadith_body = text[: note_match.start()].strip()

        brackets = re.findall(r"\[(.*?)\]", hadith_body)
        narrator = "-"
        if brackets:
            narrator = brackets[-1].strip("'").strip()
            narrator = re.sub(
                r"\s*radliallahu\s+'anh(a|u)\s*", "", narrator, flags=re.IGNORECASE
            ).strip()

        narration_match = re.search(
            r"bahwa\s+(Rasulullah|Nabi|Beliau).*$",
            hadith_body,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if narration_match:
            narration = narration_match.group(0).strip()
        else:
            narration = hadith_body.strip()

        return {"narrator": narrator, "narration": narration, "note": note}

    def parse_english(self, text: str) -> Dict[str, str]:
        """Ekstraksi teks Bahasa Inggris."""
        narrator = "-"
        narration = text.strip()
        note = "-"

        # 1. Narrator extraction e.g. "Narrated Aisha: ..."
        narrated_match = re.search(r"^Narrated\s+([^:]+):", text, flags=re.IGNORECASE)
        if narrated_match:
            narrator = narrated_match.group(1).strip()
            narration = text[narrated_match.end() :].strip()

        # 2. Check for note at the end (if any)
        if "said," in narration:
            parts = narration.split("said,")
            if len(parts) > 1 and len(parts[-1].strip()) < 100 and "compulsory" not in parts[-1]:
                note = parts[-1].strip()

        return {"narrator": narrator, "narration": narration, "note": note}

    def parse_arabic(self, text: str) -> Dict[str, str]:
        """Ekstraksi teks Bahasa Arab."""
        narrator = "-"
        note = "-"

        # Note check at end e.g. "تَابَعَهُ يُونُسُ"
        if "تَابَعَهُ" in text:
            idx = text.rfind("تَابَعَهُ")
            note = text[idx:].strip().strip("‏").strip(".")
            text = text[:idx].strip()

        # Extract companion narrator before "أَنَّ رَسُولَ اللَّهِ"
        match_sahaba = re.search(r"أَنَّ\s+([\u0600-\u06FF\s]+)،?\s+أَخْبَرَتْهُ|أَخْبَرَهُ", text)
        if match_sahaba:
            narrator = match_sahaba.group(1).strip()

        narration_match = re.search(r"أَنَّ\s+رَسُولَ\s+اللَّهِ.*$", text, flags=re.DOTALL)
        if narration_match:
            narration = narration_match.group(0).strip()
        else:
            narration = text.strip()

        return {"narrator": narrator, "narration": narration, "note": note}

    def parse_hadith(self, text: str, lang: str = "Indonesian") -> Optional[Dict[str, str]]:
        """Menganalisis teks hadis berdasarkan bahasa (Indonesian, English, atau Arabic) menggunakan Local LLM."""
        model_name = self.check_local_llm_available()
        if not model_name:
            logger.info("Local LLM (Ollama) tidak ditemukan. Fitur ekstraksi LLM dihilangkan.")
            return None

        lang_lower = lang.lower()
        if "eng" in lang_lower:
            parsed = self.parse_english(text)
        elif "ara" in lang_lower:
            parsed = self.parse_arabic(text)
        else:
            parsed = self.parse_indonesian(text)

        # Coba minta LLM merapikan jika LLM responsif
        try:
            prompt = (
                f"Extract 3 fields from this Hadith ({lang}):\n"
                f"1. Narrator: Name of the last narrator/companion without honorific titles.\n"
                f"2. Narration: Main body text/events/saying of the Prophet.\n"
                f"3. Note: Any scholar note or takhrij at the end, otherwise \"-\".\n\n"
                f"Text:\n\"{text}\"\n\n"
                f"JSON Output:\n"
                f'{{"narrator": "{parsed["narrator"]}", "narration": "{parsed["narration"][:100]}...", "note": "{parsed["note"]}"}}'
            )

            resp = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=15.0,
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
            logger.warning(f"Local LLM timeout/error ({e}). Using regex parsed result.")

        return parsed
