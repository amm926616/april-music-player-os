import random
import string

def generate_secret_key():
    # Generate four random lowercase letters
    letters = random.choices(string.ascii_lowercase, k=4)
    
    # Define special characters (transformers) and a random number as string
    transformers = ['#', '@', '$']
    num = str(random.randint(1, 9))
    
    # Combine all components and shuffle
    key_list = letters + transformers + [num]
    random.shuffle(key_list)
    
    # Create the key as a string
    key = ''.join(key_list)
    return key

if __name__ == "__main__":
    generate_secret_key()
