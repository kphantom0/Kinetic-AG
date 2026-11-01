import os
import json
import zipfile
import urllib.request
import kvl

REPO_ZIP_URL = "https://github.com/arcprize/ARC-AGI-2/archive/refs/heads/main.zip"
ZIP_LOCAL_NAME = "arc_prize_repo.zip"
EXTRACT_DIR = "arc_prize_extracted"
REPORT_OUTPUT_NAME = "kvl_audit_report.json"

def download_and_extract_arc():
    """Downloads the arcprize/ARC-AGI-2 repository and extracts it safely."""
    # We dynamic search for the path in case the zip unpacks to different branch variants
    found_dir = None
    if os.path.exists(EXTRACT_DIR):
        for root, dirs, _ in os.walk(EXTRACT_DIR):
            if "data" in dirs and "training" in os.listdir(os.path.join(root, "data")):
                found_dir = os.path.join(root, "data", "training")
                break

    if not found_dir:
        print("[*] Downloading the complete 1,000-task arcprize/ARC-AGI-2 dataset...")
        try:
            # Fallback block to try master branch if main branch link updates
            urllib.request.urlretrieve(REPO_ZIP_URL, ZIP_LOCAL_NAME)
        except Exception:
            fallback_url = "https://github.com/arcprize/ARC-AGI-2/archive/refs/heads/master.zip"
            urllib.request.urlretrieve(fallback_url, ZIP_LOCAL_NAME)
        
        print("[*] Unpacking zip archive structures...")
        with zipfile.ZipFile(ZIP_LOCAL_NAME, 'r') as zip_ref:
            zip_ref.extractall(EXTRACT_DIR)
            
        os.remove(ZIP_LOCAL_NAME)
        
        for root, dirs, _ in os.walk(EXTRACT_DIR):
            if "data" in dirs and "training" in os.listdir(os.path.join(root, "data")):
                found_dir = os.path.join(root, "data", "training")
                break
        print("[+] Dataset acquired and structured successfully.\n")
    else:
        print("[+] arcprize/ARC-AGI-2 training database located locally. Initializing mass audit...\n")
        
    return found_dir

# Initialize extraction tracking
training_path = download_and_extract_arc()

if not training_path:
    raise FileNotFoundError("Could not auto-locate the 'data/training' folder inside the extracted repository package.")

# Master database blueprint to store as down-stream training metadata
audit_report = {
    "summary": {
        "total_files_processed": 0,
        "total_pipeline_successes": 0,
        "total_pipeline_failures": 0,
        "global_objects_isolated": 0
    },
    "tasks": {}
}

print("--- Initiating Mass Robustness Verification Sweep across ARC-AGI-2 ---")

task_files = [f for f in os.listdir(training_path) if f.endswith(".json")]

for filename in task_files:
    task_id = filename.replace(".json", "")
    file_path = os.path.join(training_path, filename)
    audit_report["summary"]["total_files_processed"] += 1
    
    # Task specific profile dictionary
    task_entry = {
        "status": "NOT_RUN",
        "num_train_pairs": 0,
        "num_test_pairs": 0,
        "error_log": None,
        "train_metrics": [],
        "test_metrics": []
    }
    
    try:
        with open(file_path, "r") as f:
            task_data = json.load(f)
            
        # Dynamically evaluate whatever count configurations exist in the current file schema
        task_entry["num_train_pairs"] = len(task_data["train"])
        task_entry["num_test_pairs"] = len(task_data["test"])
        
        # Parse all available training entries dynamically
        for idx, sample in enumerate(task_data["train"]):
            in_grid = sample["input"]
            out_grid = sample["output"]
            
            in_h, in_w = kvl.get_dimensions(in_grid)
            out_h, out_w = kvl.get_dimensions(out_grid)
            
            # Stress test entity extractors
            objects = kvl.find_objects(in_grid)
            audit_report["summary"]["global_objects_isolated"] += len(objects)
            
            task_entry["train_metrics"].append({
                "example_index": idx,
                "input_dimensions": [in_h, in_w],
                "output_dimensions": [out_h, out_w],
                "objects_detected": len(objects),
                "colors_present": list(set(obj["color"] for obj in objects))
            })
            
        # Parse variable test sets dynamically (perfectly scaling to 2-4 test entries)
        for idx, sample in enumerate(task_data["test"]):
            in_grid = sample["input"]
            in_h, in_w = kvl.get_dimensions(in_grid)
            objects = kvl.find_objects(in_grid)
            
            task_entry["test_metrics"].append({
                "test_index": idx,
                "input_dimensions": [in_h, in_w],
                "objects_detected": len(objects),
                "colors_present": list(set(obj["color"] for obj in objects))
            })
            
        task_entry["status"] = "PARSED"
        audit_report["summary"]["total_pipeline_successes"] += 1
            
    except Exception as e:
        task_entry["status"] = "FAILED"
        task_entry["error_log"] = str(e)
        audit_report["summary"]["total_pipeline_failures"] += 1
        print(f"[-] Defect identified in Task ID: {task_id} | Reason: {e}")

    # Bind individual metrics block back to global storage dictionary
    audit_report["tasks"][task_id] = task_entry

# Commit full database report to absolute file storage
with open(REPORT_OUTPUT_NAME, "w") as report_file:
    json.dump(audit_report, report_file, indent=4)

print("\n================ FINAL AUDIT SUMMARY ================")
print(f"Total Tasks Processed   : {audit_report['summary']['total_files_processed']} / 1,000")
print(f"Tasks Parsed Successfully: {audit_report['summary']['total_pipeline_successes']}")
print(f"Task Parse Failures      : {audit_report['summary']['total_pipeline_failures']}")
print(f"Total Objects Extracted : {audit_report['summary']['global_objects_isolated']}")
print(f"[SUCCESS] Compilation dataset report saved to: {REPORT_OUTPUT_NAME}")
