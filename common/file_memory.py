# File name memory utility
class FileMemory:
    def __init__(self, file_list_path="file_list.txt"):
        self.files = set()
        # Load file names from file_list.txt on initialization
        try:
            with open(file_list_path, "r") as f:
                for line in f:
                    name = line.strip()
                    if name:
                        self.add_file(name)
        except Exception as e:
            print(f"[FileMemory] Warning: Could not load file list from {file_list_path}: {e}")
    def add_file(self, file_name):
        self.files.add(file_name)
    def has_file(self, file_name):
        return file_name in self.files
    def list_files(self):
        return list(self.files)
