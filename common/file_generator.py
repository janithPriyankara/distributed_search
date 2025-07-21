# File generator utility

def generate_file(file_name, content):
    with open(file_name, 'wb') as f:
        f.write(content)
