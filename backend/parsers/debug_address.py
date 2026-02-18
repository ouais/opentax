
from utils import looks_like_address, clean_name

def test_address():
    text = "499 WASHINGTON BLVD"
    print(f"Testing text: '{text}'")
    
    is_addr = looks_like_address(text)
    print(f"looks_like_address('{text}') = {is_addr}")
    
    cleaned = clean_name(text)
    print(f"clean_name('{text}') = '{cleaned}'")
    
    # Test strict start with digits regex manually
    import re
    # Test strictly without number to verifying suffix logic
    text2 = "WASHINGTON BLVD"
    print(f"Testing text2: '{text2}'")
    is_addr2 = looks_like_address(text2)
    print(f"looks_like_address('{text2}') = {is_addr2}")

if __name__ == "__main__":
    test_address()
