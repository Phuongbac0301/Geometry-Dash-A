import random

def generate_map_string(cols, density, seed):
    random.seed(seed)
    rows = 10
    map_data = [["." for _ in range(cols)] for _ in range(rows)]
    col = 25
    while col < cols - 20: 
        gap = random.randint(int(6 / density), int(12 / density))
        col += gap
        if col >= cols - 20:
            break
            
        choice = random.choice([1, 2, 3, 4, 5, 6])
        
        if choice == 1:
            map_data[9][col] = '^'
        elif choice == 2:
            if col + 1 < cols:
                map_data[9][col] = '^'
                map_data[9][col+1] = '^'
        elif choice == 3:
            map_data[9][col] = '#'
        elif choice == 4:
            if col + 1 < cols:
                map_data[9][col] = '#'
                map_data[9][col+1] = '#'
        elif choice == 5:
            map_data[9][col] = '#'
            map_data[8][col] = '^'
        elif choice == 6:
            if col + 2 < cols:
                map_data[9][col] = '#'
                map_data[9][col+1] = '#'
                map_data[8][col+1] = '#'
                map_data[9][col+2] = '#'
                map_data[8][col+2] = '#'
                map_data[7][col+2] = '#'
                
    map_strings = ["".join(r) for r in map_data]
    return map_strings

# Calculate max possible cols (up to 240 seconds = 4 mins, speed = 600)
# 240 * 600 / 40 = 3600 cols
easy = generate_map_string(3600, 0.8, 42)
normal = generate_map_string(3600, 1.2, 100)
hard = generate_map_string(3600, 1.8, 666)

with open('maps.py', 'w') as f:
    f.write("EASY_MAP = [\n")
    for r in easy: f.write(f'    "{r}",\n')
    f.write("]\n\n")
    
    f.write("NORMAL_MAP = [\n")
    for r in normal: f.write(f'    "{r}",\n')
    f.write("]\n\n")

    f.write("HARD_MAP = [\n")
    for r in hard: f.write(f'    "{r}",\n')
    f.write("]\n")
