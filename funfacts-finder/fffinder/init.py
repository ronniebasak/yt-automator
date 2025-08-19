from dlfile import download_file


BASE = "https://www.factslides.com"
BASE_DIR = "./raw_dataset"
URLs = []


# PHASE 1: COLLECT URLs
for i in range(1, 200):
    f_url = None
    if i == 1:
        f_url = BASE
    else:
        f_url = f"{BASE}/p-{i}"

    URLs.append(f_url)


# PHASE 2: COLLECT
for u in URLs:
    download_file(u, BASE_DIR)
