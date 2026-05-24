import io
import json
import requests
from flask import request, jsonify


def extract_file_text(file) -> str:
    """
    Extract plain text from an uploaded file.

    Uses pdfminer for PDFs and UTF-8 decoding for plain text files.
    """
    if file is None:
        return ""

    filename = getattr(file, "filename", None) or getattr(file, "name", "")
    filename = filename.lower()
    raw = file.read()
    # print(raw)
    if isinstance(raw, str):
        raw = raw.encode("utf-8", errors="replace")
    is_pdf = filename.endswith(".pdf") or raw[:5] == b"%PDF-"

    # For simple plain-text formats, decode directly
    PLAIN_TEXT_EXTENSIONS = (".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml")
    if filename.endswith(PLAIN_TEXT_EXTENSIONS):
        return raw.decode("utf-8", errors="replace").strip()

    if is_pdf:
        return _extract_pdf_text_pdfminer(raw)

    # Fallback: best-effort UTF-8 decode for other file types
    return raw.decode("utf-8", errors="replace").strip()

def _extract_pdf_text_pdfminer(raw: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return ""

    try:
        with io.BytesIO(raw) as bio:
            text = extract_text(bio)
    except Exception:
        return ""

    return text.strip() if text else ""



def build_prompt(text: str, file_text: str, subject: str = "", chapter: str = "") -> str:
    """Build the user prompt sent to the model."""
    parts = []
    if subject:
        parts.append(f"=== Subject ===\n{subject}")
    if chapter:
        parts.append(f"=== Chapter ===\n{chapter}")
    if text:
        parts.append(f"=== Pasted text ===\n{text}")
    if file_text:
        parts.append(f"=== File content ===\n{file_text}")

    combined = "\n\n".join(parts) if parts else "(no content provided)"

    return (
        "You are an expert quiz generator. "
        "Based on the content below, generate as many distinct questions as you think are needed to test understanding of the key concepts. "
        "Use the subject and chapter as the organizational context for the questions. "
        "Return ONLY a valid JSON array where each element is an object with keys: "
        '"question" (string), "answer" (the correct short answer string), '
        f"{combined}"
    )


def parse_questions(raw_text: str) -> list:
    """Parse the model's JSON response, stripping markdown fences if present."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]          # drop opening fence + lang tag
        if text.startswith("json"):
            text = text[4:]
        if "```" in text:
            text = text[: text.rindex("```")]   # drop closing fence
    return json.loads(text.strip())


def generate_questions_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> list:
    """
    Args:
        prompt:  The fully-built user prompt.
        api_key: Your OpenAI API key (sk-…).
        model:   Any chat model, e.g. "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo".

    Returns:
        A list of question dicts parsed from the model's JSON response.

    Raises:
        requests.HTTPError: on non-2xx responses.
        json.JSONDecodeError: if the model returns malformed JSON.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that always responds with valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"]
    return parse_questions(raw)


def generate_questions_openrouter(
    prompt: str,
    api_key: str,
    model: str = "openai/gpt-4o-mini",
    site_url: str = "",
    site_name: str = "",
) -> list:
    """
    Args:
        prompt:    The fully-built user prompt.
        api_key:   Your OpenRouter API key.
        model:     The model slug to use.
        site_url:  Optional – your app's URL (shown in OpenRouter dashboard).
        site_name: Optional – your app's name (shown in OpenRouter dashboard).

    Returns:
        A list of question dicts parsed from the model's JSON response.

    Raises:
        requests.HTTPError: on non-2xx responses.
        json.JSONDecodeError: if the model returns malformed JSON.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter for ranking/attribution
        **({"HTTP-Referer": site_url} if site_url else {}),
        **({"X-Title": site_name} if site_name else {}),
    }
    payload = {
        "model": model,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that always responds with valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    print(payload)
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"]
    return parse_questions(raw)



if __name__ == "__main__":
    with open("test/file.pdf", "rb") as f:
        output = extract_file_text(f)
        print(output)