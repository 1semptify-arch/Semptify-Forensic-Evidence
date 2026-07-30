import mimetypes
from pathlib import Path

def classify_file(path: Path) -> str:
    """Classify file type and return appropriate extractor name."""
    suffix = path.suffix.lower()
    
    # PDF
    if suffix == ".pdf":
        return "pdf"
    
    # Images
    if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"]:
        return "image"
    
    # Email
    if suffix == ".eml":
        return "email"
    
    # Audio
    if suffix in [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"]:
        return "audio"
    
    # CSV (carrier call logs)
    if suffix == ".csv":
        return "csv"
    
    # SMS exports
    if suffix in [".xml", ".sms"]:
        return "sms"
    
    # Try MIME type detection
    mime, _ = mimetypes.guess_type(path.name)
    if mime:
        if mime == "application/pdf":
            return "pdf"
        if mime and mime.startswith("image"):
            return "image"
        if mime and mime.startswith("audio"):
            return "audio"
        if mime == "text/csv":
            return "csv"
    
    return "unknown"
