import json
import base64
import requests
from flask import request, jsonify


import io
import tempfile
import os

def extract_file_text(file) -> str:
    """
    Extract plain text from an uploaded file using Docling.

    Docling natively handles: PDF, DOCX, PPTX, XLSX, HTML, Markdown,
    plain text, CSV, and more — including scanned PDFs via OCR.

    Falls back to raw UTF-8 decode if Docling is not installed or
    if the file type is a simple plain-text format.

    Requires: pip install docling
    """
    if file is None:
        return ""

    filename = file.filename.lower()
    raw = file.read()

    # For simple plain-text formats, skip Docling overhead entirely
    PLAIN_TEXT_EXTENSIONS = (".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml")
    if filename.endswith(PLAIN_TEXT_EXTENSIONS):
        return raw.decode("utf-8", errors="replace").strip()

    # Use Docling for everything else (PDF, DOCX, PPTX, XLSX, HTML, …)
    try:
        from docling.document_converter import DocumentConverter

        # Docling works from file paths, so write to a named temp file
        suffix = os.path.splitext(filename)[1] or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(raw)
            tmp_path = tmp.name

        try:
            converter = DocumentConverter()
            result = converter.convert(tmp_path)
            # Export as Markdown — preserves headings, tables, lists cleanly
            return result.document.export_to_markdown().strip()
        finally:
            os.unlink(tmp_path)   # always clean up

    except ImportError:
        # Docling not installed — fall back to plain UTF-8 decode
        try:
            return raw.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    except Exception as e:
        # Docling failed (unsupported format, corrupt file, etc.)
        # Log and fall back gracefully
        print(f"[extract_file_text] Docling error for '{filename}': {e}")
        try:
            return raw.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""



def build_prompt(text: str, file_text: str) -> str:
    """Build the user prompt sent to the model."""
    parts = []
    if text:
        parts.append(f"=== Pasted text ===\n{text}")
    if file_text:
        parts.append(f"=== File content ===\n{file_text}")

    combined = "\n\n".join(parts) if parts else "(no content provided)"

    return (
        "You are an expert quiz generator. "
        "Based on the content below, generate 5 distinct questions that test understanding of the key concepts. "
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
    with open("file") as f:
        print(extract_file_text(f))
