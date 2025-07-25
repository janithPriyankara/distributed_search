# FileFetcher class: fetches a file from neighbors using HTTP request maker and neighbor table

from common.neighbor_table import NeighborTable
from http_local.request_maker import HttpRequestMaker

import random

class FileFetcher:
    def __init__(self, file_memory):
        """
        file_memory: an object that provides a list of available file names (e.g., FileMemory)
        """
        self.file_memory = file_memory

    def get_random_file(self):
        """
        Selects a random file name from file memory.
        """
        files = self.file_memory.get_all_files()
        if not files:
            print("No files available in memory.")
            return None
        file_name = random.choice(files)
        print(f"Selected random file: {file_name}")
        return file_name

    def handle_file_result(self, file_name, file_content):
        """
        Called by the HTTP request maker after searching for the file.
        """
        if file_content:
            print(f"✅ FileFetcher: Received file '{file_name}' (size: {len(file_content)} bytes)")
        else:
            print(f"❌ FileFetcher: File '{file_name}' not found in the network.")
