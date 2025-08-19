import os
import requests

def download_file(url: str, directory: str) -> str:
    """
    Downloads a file from a given URL and saves it to the specified directory.

    Args:
        url (str): The file URL.
        directory (str): Path to the directory where the file should be saved.

    Returns:
        str: The full path of the saved file.
    """
    print(f"[INFO] Preparing to download from: {url}")

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    print(f"[INFO] Ensured directory exists: {directory}")

    # Extract filename from URL
    filename = os.path.basename(url.split("?")[0])
    filepath = os.path.join(directory, filename)
    print(f"[INFO] File will be saved as: {filepath}")

    # Download and save
    response = requests.get(url, stream=True)
    response.raise_for_status()
    print(f"[INFO] Connection established, downloading...")

    total_bytes = 0
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                total_bytes += len(chunk)
    print(f"[SUCCESS] Download complete. Total size: {total_bytes/1024:.2f} KB")

    return filepath
