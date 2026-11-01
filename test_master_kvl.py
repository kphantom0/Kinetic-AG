# test_master_kvl.py

import kvl

# SCENARIO: A complex 8x12 ARC grid.
# Features:
# - Dead space on the right and bottom.
# - A Grey (5) background lattice intersecting at row 4, col 3.
# - A hollow Blue box (1) trapping a blank space.
# - An asymmetrical Red shape (2).
master_grid = [
    [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0, 0, 2, 2, 0, 0, 0, 0],
    [0, 1, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0, 0, 2, 2, 0, 0, 0, 0],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0],
    [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

print("==================================================")
print("     KINETIC-AG: MASTER K-VL DIAGNOSTIC BOOT      ")
print("==================================================\n")

# ---------------------------------------------------------
# MODULE 1: K_SPACE (Environment & Framework)
# ---------------------------------------------------------
print("--- [1/4] K_SPACE: ENVIRONMENT SCAN ---")
dims = kvl.get_dimensions(master_grid)
print(f"[*] Canvas Dimensions: {dims[0]}x{dims[1]}")

lattice = kvl.detect_background_grid(master_grid)
if lattice:
    print(f"[*] Background Lattice Detected: Color {lattice['grid_color']}")
    print(f"    Intersections -> Rows: {lattice['row_indices']}, Cols: {lattice['column_indices']}")

blank_canvas = kvl.create_blank_grid_like(master_grid)
print(f"[*] Blank Canvas Generated: {len(blank_canvas)}x{len(blank_canvas[0])}\n")

# ---------------------------------------------------------
# MODULE 2: K_OBJECTS (Cognition & Extraction)
# ---------------------------------------------------------
print("--- [2/4] K_OBJECTS: ENTITY COGNITION ---")
objects = kvl.find_objects(master_grid)
print(f"[*] Total Raw Objects Extracted: {len(objects)}")

# Filter specific entities
blue_box = kvl.filter_by_color(objects, 1)[0]
red_shape = kvl.filter_by_color(objects, 2)[0]
largest_obj = kvl.filter_by_size(objects, condition="largest")[0]
print(f"[*] Largest Object Footprint: Color {largest_obj['color']}")

# Advanced Cognition
com_y, com_x = kvl.get_com(red_shape)
print(f"[*] Red Shape Center of Mass: Y={com_y:.2f}, X={com_x:.2f}")

enclosed_regions = kvl.get_enclosed_regions(master_grid)
hole = enclosed_regions[0]
print(f"[*] Hollow Container Detected! Trapped empty space isolated at: {hole['position']}\n")

# ---------------------------------------------------------
# MODULE 3: K_TRANSFORM (Spatial Logic & Matching)
# ---------------------------------------------------------
print("--- [3/4] K_TRANSFORM: SPATIAL PHYSICS ---")
crop_data = kvl.find_crop_area(master_grid)
print(f"[*] Grid Cropped. Optimized Active Matrix Size: {crop_data['dimensions'][0]}x{crop_data['dimensions'][1]}")

distance = kvl.get_distance(blue_box, red_shape)
alignment = kvl.is_aligned(blue_box, red_shape)
print(f"[*] Relational Physics -> Manhattan Distance: {distance} | Horizontal Alignment: {alignment['horizontal']}")

# Transform Operations
rotated_red = kvl.rotate(red_shape, degrees=90)
mirrored_red = kvl.mirror(rotated_red, axis="vertical")
shifted_red = kvl.shift(mirrored_red, vector=(0, -4)) # Move left towards the blue box

# Collision Detection
collision = kvl.has_overlap(shifted_red, blue_box)
print(f"[*] Transformation complete. Collision detected post-shift: {collision['is_overlapping']}\n")

# ---------------------------------------------------------
# MODULE 4: K_COLOR (Rendering & Manipulation)
# ---------------------------------------------------------
print("--- [4/4] K_COLOR: CANVAS RENDERING ---")

# Recolor the extracted hole and the transformed shape
filled_hole = kvl.recolor(hole, new_color=3) # Fill trapped space with Green
final_red = kvl.recolor(shifted_red, new_color=4) # Change transformed shape to Yellow

# Paint onto the clean canvas
render_layer = kvl.paint_onto(blank_canvas, blue_box)
render_layer = kvl.paint_onto(render_layer, filled_hole)
render_layer = kvl.paint_onto(render_layer, final_red)

# Flood fill the outside border to test paint-bucket
final_output = kvl.flood_fill_canvas(render_layer, start_coord=(0, 0), fill_color=8)
print("[*] Render Pipeline Complete. Final Output Matrix:")

# Crop the final output just for terminal readability
final_cropped = kvl.find_crop_area(final_output, background_color=8)
if final_cropped:
    for row in final_cropped["cropped_grid"]:
        print(f"    {row}")
else:
    for row in final_output:
        print(f"    {row}")

print("\n==================================================")
print("        ALL SYSTEMS NOMINAL. READY FOR AGI.       ")
print("==================================================")
