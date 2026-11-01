# test_benchmark.py

import json
import os
import urllib.request
import kvl

# A couple of classic, diverse public ARC task IDs
# 0d3d703e: Color mapping / grid scaling
# 36d67576: Moving shapes to align with a pattern
TASK_IDS = ["0d3d703e", "36d67576"]
BASE_URL = "https://raw.githubusercontent.com/fchollet/ARC-AGI/master/data/training/"

def download_task(task_id):
    """Downloads a task JSON from the official repository if not present locally."""
    filename = f"{task_id}.json"
    if not os.path.exists(filename):
        print(f"Downloading task {task_id} from official repository...")
        url = f"{BASE_URL}{filename}"
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"Successfully saved {filename}")
        except Exception as e:
            print(f"Error downloading {task_id}: {e}")
            return None
    return filename

print("--- Starting Public Benchmark Integration Test ---\n")

for task_id in TASK_IDS:
    file_path = download_task(task_id)
    if not file_path:
        continue
        
    with open(file_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)
        
    print(f"\n================ Analyzing Task: {task_id} ================")
    print(f"Total Training Examples Provided: {len(task_data['train'])}")
    print(f"Total Test Questions Provided: {len(task_data['test'])}")
    
    # Let's loop through the training examples and parse them with K-VL
    for idx, example in enumerate(task_data["train"]):
        input_grid = example["input"]
        output_grid = example["output"]
        
        # Get dimensions using K-VL
        in_h, in_w = kvl.get_dimensions(input_grid)
        out_h, out_w = kvl.get_dimensions(output_grid)
        
        # Extract objects from the input grid using K-VL
        detected_objects = kvl.find_objects(input_grid)
        
        print(f"\n  [Example {idx + 1}]")
        print(f"    Input Grid Size : {in_h}x{in_w}  |  Output Grid Size: {out_h}x{out_w}")
        print(f"    K-VL Discovered : {len(detected_objects)} independent objects.")
        
        # Quick breakdown of what colors were found
        if detected_objects:
            colors_found = set(obj["color"] for obj in detected_objects)
            print(f"    Object Colors   : {list(colors_found)}")
            
            # Find the largest object in this specific example layout
            largest = kvl.filter_by_size(detected_objects, condition="largest")[0]
            print(f"    Largest Object  : Color {largest['color']} at position {largest['position']} with size {len(largest['indices'])}px")

print("\n--- Benchmark Parsing Verification Complete ---")
