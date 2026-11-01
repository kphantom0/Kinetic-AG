# test_all_400.py

import os
import json
import zipfile
import urllib.request
import kvl

REPO_ZIP_URL = "https://github.com/fchollet/ARC-AGI/archive/refs/heads/master.zip"
ZIP_LOCAL_NAME = "arc_repo.zip"
EXTRACT_DIR = "arc_extracted"
TRAINING_DATA_DIR = os.path.join(EXTRACT_DIR, "ARC-AGI-master", "data", "training")

def download_and_extract_arc():
    """Downloads the entire official ARC repository and extracts it cleanly."""
    if not os.path.exists(TRAINING_DATA_DIR):
        print("[*] Downloading the official ARC-AGI repository zip package...")
        urllib.request.urlretrieve(REPO_ZIP_URL, ZIP_LOCAL_NAME)
        
        print("[*] Extracting repository contents...")
        with zipfile.ZipFile(ZIP_LOCAL_NAME, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
            
        # Clean up the zip file to keep workspace organized
        os.remove(ZIP_LOCAL_NAME)
        print("[+] Repository downloaded and unpacked successfully.\n")
    else:
        print("[+] Official training dataset already present locally. Proceeding to test...\n")

# Run dataset setup
download_and_extract_arc()

# Metadata trackers for the mass audit
total_files_processed = 0
total_objects_extracted = 0
global_color_distribution = {i: 0 for i in range(10)}
failed_files = []

print("--- Launching Mass K-VL Robustness Check Across 400 Benchmark Tasks ---")

task_files = [f for f in os.listdir(TRAINING_DATA_DIR) if f.endswith(".json")]

for filename in task_files:
    file_path = os.path.join(TRAINING_DATA_DIR, filename)
    total_files_processed += 1
    
    try:
        with open(file_path, "r") as f:
            task_data = json.load(f)
            
        # Run K-VL parsing loops on every single training example inside the file
        for example in task_data["train"]:
            input_grid = example["input"]
            
            # Stress-test the object detection engine
            detected_objects = kvl.find_objects(input_grid)
            total_objects_extracted += len(detected_objects)
            
            # Log color instances for data analysis
            for obj in detected_objects:
                global_color_distribution[obj["color"]] += 1
                
    except Exception as e:
        print(f"[-] CRITICAL ERROR: Library failed to parse file {filename}")
        print(f"Details: {e}")
        failed_files.append((filename, str(e)))

print("\n================ MASS TEST RECAP ================")
print(f"Total Puzzle Files Audited : {total_files_processed} / 400")
print(f"Total Core Objects Isolated: {total_objects_extracted}")
print(f"Total Parsing Pipeline Failures: {len(failed_files)}")

if len(failed_files) == 0:
    print("[SUCCESS] K-VL achieved 100% processing stability across the benchmark!")
else:
    print("[-] Review the following edge cases for potential codebase bugs:")
    for f, err in failed_files:
        print(f"  - {f}: {err}")
        
print("\nGlobal Pixel Color Frequency Map across detected entities:")
for color_code, count in global_color_distribution.items():
    print(f"  Color [{color_code}]: Found {count} times")