import os
import sys

def check_directory_structure():
    print("Checking directory structure...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check data directory
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print(f"Creating data directory: {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    else:
        print(f"Data directory exists: {data_dir}")
    
    # Check memory directory
    memory_dir = os.path.join('data', 'memory')
    if not os.path.exists(memory_dir):
        print(f"Creating memory directory: {memory_dir}")
        os.makedirs(memory_dir, exist_ok=True)
    else:
        print(f"Memory directory exists: {memory_dir}")
    
    # Check write permissions
    try:
        test_file = os.path.join(memory_dir, 'test_write.txt')
        with open(test_file, 'w') as f:
            f.write('Test write permission')
        print(f"Successfully wrote to: {test_file}")
        os.remove(test_file)
        print(f"Successfully removed test file")
    except Exception as e:
        print(f"Error writing to memory directory: {e}")
    
    # Print all directories and files
    print("\nDirectory structure:")
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

if __name__ == "__main__":
    check_directory_structure()
