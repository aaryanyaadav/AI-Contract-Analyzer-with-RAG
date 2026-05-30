import os

ALLOWED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".png",
    ".jpg",
    ".jpeg"
]

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

def validate_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")

    extension = os.path.splitext(file_path)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")

    file_size = os.path.getsize(file_path)

    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes exceeds max {MAX_FILE_SIZE}")

    return True             