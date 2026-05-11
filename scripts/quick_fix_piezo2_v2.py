

def fix_piezo2_simple():
    filepath = 'manuscript/sections/tables.tex'
    with open(filepath, 'r') as f:
        content = f.read()

    # Simple string replace
    target_str = r"PIEZO2 & Q9H5I5 & $\eta_p$ & 4.44 & Fibrous/Extended & 79.4 & 709 & $L$ \\"
    new_str = r"PIEZO2 & Q9H5I5 & $\eta_p$ & 4.44 & Fibrous/Extended & 79.4 & 2752 & $L$ \\"

    if target_str in content:
        content = content.replace(target_str, new_str)
        print("Replaced PIEZO2 residues.")
    else:
        print("Target string not found, check spacing?")

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_piezo2_simple()
