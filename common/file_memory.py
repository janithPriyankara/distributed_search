# File name memory utility
class FileMemory:
    def __init__(self):
        self.files = set()
        # Add example file names on initialization
        for name in ["alpha.txt", "beta.txt", "gamma.txt", "delta.txt", "epsilon.txt"]:
            self.add_file(name)
    def add_file(self, file_name):
        self.files.add(file_name)
    def has_file(self, file_name):
        return file_name in self.files
    def list_files(self):
        return list(self.files)
