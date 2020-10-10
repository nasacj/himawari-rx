"""
file.py
https://github.com/sam210723/himawari-rx
"""

import bz2
import pathlib

class File:
    """
    Incoming file object containing file properties and payload
    """

    def __init__(self, name, path, parts, length, time_a, time_b):
        self.name      = name.split('.')[0]
        self.ext       = f".{name.split('.')[1]}"
        self.path      = path
        self.parts     = parts - 1
        self.length    = length
        self.time_a    = time_a
        self.time_b    = time_b
        self.time_diff = time_b[0] - time_a[0]

        self.payload = {}
        self.complete = False
        self.compressed = True


    def add(self, data):
        """
        Add data to file payload
        """

        # Get file part number
        part = self.get_int(data[8:10])

        # Append data to payload
        self.payload[part] = data[16:]

        # Check all parts have been received
        self.complete = len(self.payload) == self.parts

        return len(self.payload)


    def save(self, path):
        """
        Save file payload to disk

        Args:
            path (str): Path to output directory

        Returns:
            bool: Save success flag
        """

        if type(self.payload) == dict:
            # Assemble contiguous payload from individual parts
            file_payload = b''
            for part in range(len(self.payload)):
                try:
                    file_payload += self.payload[part]
                except KeyError:
                    print(f"    MISSING PART {part}")
            self.payload = file_payload

        # Check payload length is correct (file content without FEC)
        if len(self.payload) < self.length:
            return False
        
        # Write payload to disk
        with open(self.get_save_path(path), 'wb') as f:
            f.write(self.payload[:self.length])
            f.close()

        return True


    def decompress(self):
        """
        Decompress bz2 file payload
        """

        if type(self.payload) == dict:
            # Assemble contiguous payload from individual parts
            file_payload = b''
            for part in range(len(self.payload)):
                try:
                    file_payload += self.payload[part]
                except KeyError:
                    print(f"    MISSING PART {part}")
            self.payload = file_payload

        # Check payload length is correct (file content without FEC)
        if len(self.payload) < self.length:
            return False
        
        # Decompress bz2 payload
        try:
            decomp = bz2.decompress(self.payload[:self.length])
        except Exception:
            return False
        
        self.payload = decomp
        self.length = len(self.payload)
        self.compressed = False

        return True


    def get_save_path(self, path):
        """
        Get save path for file based on name and extension
        """

        if self.name[:3] == "IMG":
            name_split = self.name.split("_")
            date = name_split[2][:8]
            time = name_split[2][8:]

            if self.compressed:
                self.ext = ".bz2"
            else:
                self.ext = ""
            
            pathlib.Path(f"{path}\\{date}\\{time}").mkdir(parents=True, exist_ok=True)
            return f"{path}\\{date}\\{time}\\{self.name}{self.ext}"

        elif self.ext == ".tar":
            return f"{path}\\{self.name}{self.ext}"


    def get_int(self, data):
        """
        Get integer from bytes
        """

        return int.from_bytes(data, 'little')
