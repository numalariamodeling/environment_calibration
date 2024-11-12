from helpers import generate_demographics, extract_climate

if __name__ == '__main__':
    print("CREATING DEMOGRAPHICS")
    generate_demographics()
    print("REQUESTING CLIMATE - You may need to log in")
    extract_climate(flatten_temp=False)
