import urllib.request
import urllib.parse
import json

def translate_text(text: str, source_lang: str = "auto", target_lang: str = "vi") -> str:
    """
    Translates text using the free Google Translate API.
    
    Args:
        text (str): The text to be translated.
        source_lang (str): Source language code (e.g., 'auto', 'en'). Default is 'auto'.
        target_lang (str): Target language code (e.g., 'vi', 'en'). Default is 'vi'.
        
    Returns:
        str: The translated text, or an error message if the translation fails.
    """
    if not text.strip():
        return ""

    # Google Translate free API endpoint
    base_url = "https://translate.googleapis.com/translate_a/single"
    
    # URL parameters
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": text
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
            # Parse the response JSON
            # Structure of Google Translate single API response:
            # [[[translated_text, source_text, ...], ...], ...]
            if data and len(data) > 0 and data[0]:
                translated_sentences = [sentence[0] for sentence in data[0] if sentence[0]]
                return "".join(translated_sentences)
            
            return "Error: Empty response from translation service."
            
    except urllib.error.URLError as e:
        return f"Network Error: Unable to connect to translation service. ({e.reason})"
    except json.JSONDecodeError:
        return "Error: Failed to parse translation response."
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

if __name__ == "__main__":
    # Simple console test
    test_text = "Hello world! This is a fast translation test."
    print("Original:", test_text)
    print("Translated (auto -> vi):", translate_text(test_text, "auto", "vi"))
    print("Translated (auto -> en):", translate_text("Xin chào thế giới!", "auto", "en"))
