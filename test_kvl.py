import kvl

# SCENARIO: A massive 10x10 grid full of dead space. 
# Only a small corner has active pixels (Red 2 and Blue 1).
massive_grid = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 2, 2, 0],
    [0, 0, 0, 0, 0, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

print("--- Testing Smart Matching & Crop Optimizations ---")

# 1. Test Active Area Cropping
crop_data = kvl.find_crop_area(massive_grid)
print(f"[+] Dead space eliminated.")
print(f"    Original canvas size : 10x10")
print(f"    Optimized canvas size: {crop_data['dimensions'][0]}x{crop_data['dimensions'][1]}")
print(f"    Cropped Matrix:")
for row in crop_data["cropped_grid"]:
    print(f"      {row}")

# 2. Test Collision Detection
objects = kvl.find_objects(massive_grid)
red_obj = kvl.filter_by_color(objects, 2)[0]
blue_obj = kvl.filter_by_color(objects, 1)[0]

# Check overlap before moving (Should be False)
initial_check = kvl.has_overlap(red_obj, blue_obj)
print(f"\n[+] Pre-Move Collision Check: {initial_check['is_overlapping']}")

# Move the Red object Down 2 rows and Right 1 column, crashing directly into the Blue object
moved_red = kvl.shift(red_obj, vector=(2, 1))

# Check overlap after moving (Should be True)
post_move_check = kvl.has_overlap(moved_red, blue_obj)
print(f"[+] Post-Move Collision Check: {post_move_check['is_overlapping']}")
if post_move_check['is_overlapping']:
    print(f"    WARNING: Collision detected at exact pixels: {post_move_check['collision_pixels']}")