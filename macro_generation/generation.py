import gdstk
import random
import math
min_metal6_width = 1.7 #1.64  # Minimum Metal6 width in microns
min_metal6_spacing = 1.7 #1.64 

factor = 2

length = 8 / factor  # Reduced from 8
avg_width = 2 / factor # Reduced from 3
gap = 0.5  # Reduced from 1

sizeX = 4 * factor #13
sizeY = 4 * factor #10


x_width = [4] * sizeX
y_width = [4] * sizeY



# Create 4 separate structure arrays for 2x2 grid
def create_mirrored_structure(sizeX, sizeY):
    """Create a single mirrored structure array"""
    structure = [[0 for _ in range(sizeY)] for _ in range(sizeX)]
    
    # Calculate quarter dimensions
    quarter_x = sizeX // 2
    quarter_y = sizeY // 2
    
    # Randomly fill the top-left quarter
    for x in range(quarter_x):
        for y in range(quarter_y):
            structure[x][y] = random.randint(0, 1)
    
    # Mirror to top-right quarter (horizontal mirror)
    for x in range(quarter_x):
        for y in range(quarter_y, sizeY):
            structure[x][y] = structure[x][sizeY - 1 - y]
    
    # Mirror to bottom-left quarter (vertical mirror)
    for x in range(quarter_x, sizeX):
        for y in range(quarter_y):
            structure[x][y] = structure[sizeX - 1 - x][y]
    
    # Mirror to bottom-right quarter (both horizontal and vertical mirror)
    for x in range(quarter_x, sizeX):
        for y in range(quarter_y, sizeY):
            structure[x][y] = structure[sizeX - 1 - x][sizeY - 1 - y]
    
    return structure

# Create 6 structures for 3x2 grid
structures = []
for i in range(6):
    structures.append(create_mirrored_structure(sizeX, sizeY))



# The GDSII file is called a library, which contains multiple cells.
lib = gdstk.Library()

# Geometry must be placed in cells.
cell = lib.new_cell("my_logo")

# Create 3x2 grid of structures with padding
padding = length * 1.0  # Padding between structures
grid_size_x = 3  # 3 in x direction
grid_size_y = 2  # 2 in y direction

for grid_x in range(grid_size_x):
    for grid_y in range(grid_size_y):
        structure_index = grid_x * grid_size_y + grid_y
        structure = structures[structure_index]
        
        # Calculate offset for this grid position
        offset_x = grid_x * (sizeX * length + padding)
        offset_y = grid_y * (sizeY * length + padding)
        
        # Generate pattern for this structure
        for x in range(sizeX):
            for y in range(sizeY):
                if structure[x][y] == 1:
                    # Create main rectangle with grid offset
                    rect = gdstk.rectangle(
                        (offset_x + x*length+gap, offset_y + y*length+gap), 
                        (offset_x + x*length+length-gap, offset_y + y*length+length-gap), 
                        layer=71, datatype=20
                    )
                    
                    # Create four small rectangles to subtract from center of each side
                    cutout_size = gap*1.7
                    center_x = offset_x + x*length + length/2
                    center_y = offset_y + y*length + length/2
                    
                    # Top side cutout
                    top_cutout = gdstk.rectangle((center_x - cutout_size/2, offset_y + y*length+gap), (center_x + cutout_size/2, offset_y + y*length+gap+cutout_size), layer=71, datatype=20)
                    # Bottom side cutout  
                    bottom_cutout = gdstk.rectangle((center_x - cutout_size/2, offset_y + y*length+length-gap-cutout_size), (center_x + cutout_size/2, offset_y + y*length+length-gap), layer=71, datatype=20)
                    # Left side cutout
                    left_cutout = gdstk.rectangle((offset_x + x*length+gap, center_y - cutout_size/2), (offset_x + x*length+gap+cutout_size, center_y + cutout_size/2), layer=71, datatype=20)
                    # Right side cutout
                    right_cutout = gdstk.rectangle((offset_x + x*length+length-gap-cutout_size, center_y - cutout_size/2), (offset_x + x*length+length-gap, center_y + cutout_size/2), layer=71, datatype=20)
                    
                    # Subtract the side cutouts to create cross shape
                    cross_shape = gdstk.boolean(rect, [top_cutout, bottom_cutout, left_cutout, right_cutout], 'not', layer=71, datatype=20)
                    for shape in cross_shape:
                        cell.add(shape)
        


# Add PR boundary (placement and routing boundary)
# Layer 235, datatype 4 for sky130 PR boundary
pr_boundary = gdstk.rectangle((0, 0), (length,length), layer=235, datatype=4)
cell.add(pr_boundary)

# SkyWater fill pattern parameters - using dummy fill layers
#fill_dist = 2.0  # Spacing between fill elements
#fill_size = 1.0  # Size of fill elements

# Add dummy fill patterns for SkyWater PDK - these are non-functional
#for i in range(35):  # Cover the design area
#    for j in range(23):  # Cover the design area
#        tx = i * (fill_size + fill_dist)
#        ty = j * (fill_size + fill_dist)#

#        # Dummy fill on metal1 layer (layer 68) with datatype 0 for standard metal
#        metal1_fill = gdstk.rectangle((tx, ty), (tx+fill_size, ty+fill_size), layer=68, datatype=0)
#        cell.add(metal1_fill)
       
#        # Dummy fill on metal2 layer (layer 69) with datatype 0 for standard metal
#        metal2_fill = gdstk.rectangle((tx, ty), (tx+fill_size, ty+fill_size), layer=69, datatype=0)
#        cell.add(metal2_fill)

        




# Generate LEF file
def write_lef_file(filename, cell_name, cell_bounds, pins):
    """Write a LEF file for the cell"""
    with open(filename, 'w') as f:
        f.write("# LEF file generated for {}\n".format(cell_name))
        f.write("VERSION 5.8 ;\n")
        f.write("NAMESCASESENSITIVE ON ;\n")
        f.write("DIVIDERCHAR \"/\" ;\n")
        f.write("BUSBITCHARS \"[]\" ;\n")
        f.write("UNITS\n")
        f.write("   DATABASE MICRONS 1000 ;\n")
        f.write("END UNITS\n\n")
        
        # Define the cell
        f.write("MACRO {}\n".format(cell_name))
        f.write("   CLASS BLOCK ;\n")
        f.write("   FOREIGN {} 0 0 ;\n".format(cell_name))
        f.write("   SIZE {:.3f} BY {:.3f} ;\n".format(cell_bounds[2] - cell_bounds[0], cell_bounds[3] - cell_bounds[1]))
        f.write("   SYMMETRY X Y ;\n")
        
        # No pins - pure blackbox module
        # No OBS section - keep LEF simple
        
        f.write("END {}\n".format(cell_name))

# Calculate cell bounds for 3x2 grid layout
total_width = grid_size_x * sizeY * length + (grid_size_x - 1) * padding
total_height = grid_size_y * sizeX * length + (grid_size_y - 1) * padding
cell_bounds = (0, 0, total_width, total_height)

# Write LEF file
write_lef_file("../macros/my_logo.lef", "my_logo", cell_bounds, [])

# Save the library in a GDSII or OASIS file.
lib.write_gds("../macros/my_logo.gds")

# Optionally, save an image of the cell as SVG.
cell.write_svg("../macros/my_logo.svg")