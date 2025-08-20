"""
Facts Sampler Module

This module provides functionality to:
1. Sample facts from a JSON file in chunks of 10
2. List files in a directory
"""

import json
import os
from typing import List, Generator, Union
from pathlib import Path


class FactsSampler:
    """A class to sample facts from JSON files and list directory contents."""
    
    def __init__(self):
        self.current_chunk_index = 0
        self.facts_data = []
        self.loaded_file = None
    
    def load_facts_file(self, file_path: str) -> bool:
        """
        Load facts from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file containing facts
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.facts_data = json.load(file)
                self.loaded_file = file_path
                self.current_chunk_index = 0
                print(f"Successfully loaded {len(self.facts_data)} facts from {file_path}")
                return True
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
            return False
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {file_path}")
            return False
        except Exception as e:
            print(f"Error loading file {file_path}: {str(e)}")
            return False
    
    def get_next_chunk(self, chunk_size: int = 10) -> List[str]:
        """
        Get the next chunk of facts.
        
        Args:
            chunk_size (int): Size of each chunk (default: 10)
            
        Returns:
            List[str]: List of facts in the current chunk
        """
        if not self.facts_data:
            print("No facts data loaded. Please load a file first.")
            return []
        
        start_index = self.current_chunk_index * chunk_size
        end_index = start_index + chunk_size
        
        if start_index >= len(self.facts_data):
            print("No more chunks available. Resetting to beginning.")
            self.current_chunk_index = 0
            start_index = 0
            end_index = chunk_size
        
        chunk = self.facts_data[start_index:end_index]
        self.current_chunk_index += 1
        
        print(f"Returning chunk {self.current_chunk_index} (facts {start_index + 1}-{min(end_index, len(self.facts_data))})")
        return chunk
    
    def get_all_chunks(self, chunk_size: int = 10) -> Generator[List[str], None, None]:
        """
        Generator to yield all chunks of facts.
        
        Args:
            chunk_size (int): Size of each chunk (default: 10)
            
        Yields:
            List[str]: Next chunk of facts
        """
        if not self.facts_data:
            print("No facts data loaded. Please load a file first.")
            return
        
        for i in range(0, len(self.facts_data), chunk_size):
            yield self.facts_data[i:i + chunk_size]
    
    def reset_chunk_index(self):
        """Reset the chunk index to start from the beginning."""
        self.current_chunk_index = 0
        print("Chunk index reset to beginning")
    
    def get_facts_info(self) -> dict:
        """
        Get information about the loaded facts.
        
        Returns:
            dict: Information about the loaded facts
        """
        if not self.facts_data:
            return {"loaded": False, "message": "No facts loaded"}
        
        total_facts = len(self.facts_data)
        chunks_of_10 = (total_facts + 9) // 10  # Ceiling division
        current_position = self.current_chunk_index
        
        return {
            "loaded": True,
            "file": self.loaded_file,
            "total_facts": total_facts,
            "total_chunks": chunks_of_10,
            "current_chunk_index": current_position,
            "facts_remaining": max(0, total_facts - (current_position * 10))
        }
    
    def write_chunk_to_file(self, chunk: List[str], chunk_number: int, output_dir: str = "fact-chunks") -> bool:
        """
        Write a chunk of facts to a JSON file in the specified output directory.
        
        Args:
            chunk (List[str]): List of facts to write
            chunk_number (int): The chunk number for naming the file
            output_dir (str): Output directory path (default: "fact-chunks")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Create filename
            filename = f"chunk_{chunk_number:03d}.json"
            file_path = output_path / filename
            
            # Write chunk to file
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(chunk, file, indent=2, ensure_ascii=False)
            
            print(f"Successfully wrote chunk {chunk_number} with {len(chunk)} facts to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error writing chunk {chunk_number} to file: {str(e)}")
            return False
    
    def write_all_chunks_to_files(self, chunk_size: int = 10, output_dir: str = "fact-chunks") -> int:
        """
        Write all facts as chunks to separate JSON files in the output directory.
        
        Args:
            chunk_size (int): Size of each chunk (default: 10)
            output_dir (str): Output directory path (default: "fact-chunks")
            
        Returns:
            int: Number of chunks successfully written
        """
        if not self.facts_data:
            print("No facts data loaded. Please load a file first.")
            return 0
        
        successful_writes = 0
        chunk_number = 1
        
        for chunk in self.get_all_chunks(chunk_size):
            if self.write_chunk_to_file(chunk, chunk_number, output_dir):
                successful_writes += 1
            chunk_number += 1
        
        print(f"Successfully wrote {successful_writes} chunks to {output_dir}")
        return successful_writes

    def list_directory_files(self, directory_path: str) -> List[str]:
        """
        List all files in the specified directory.
        
        Args:
            directory_path (str): Path to the directory
            
        Returns:
            List[str]: List of files in the directory
        """
        try:
            path = Path(directory_path)
            if not path.exists():
                print(f"Error: Directory {directory_path} does not exist")
                return []
            
            if not path.is_dir():
                print(f"Error: {directory_path} is not a directory")
                return []
            
            files = []
            for item in path.iterdir():
                if item.is_file():
                    files.append(item.name)
                elif item.is_dir():
                    files.append(f"{item.name}/")
            
            files.sort()
            print(f"Found {len(files)} items in {directory_path}")
            return files
            
        except PermissionError:
            print(f"Error: Permission denied accessing {directory_path}")
            return []
        except Exception as e:
            print(f"Error listing directory {directory_path}: {str(e)}")
            return []


def main():
    """Main function to demonstrate the facts sampler functionality."""
    sampler = FactsSampler()
    
    # Example usage
    print("=== Facts Sampler Demo ===")
    
    # Load facts file
    facts_file = "facts.json"
    if sampler.load_facts_file(facts_file):
        # Show info about loaded facts
        info = sampler.get_facts_info()
        print(f"Loaded {info['total_facts']} facts from {info['file']}")
        print(f"This will create {info['total_chunks']} chunks of 10 facts each")
        
        # Write all chunks to output directory
        print("\n=== Writing All Chunks to Files ===")
        chunks_written = sampler.write_all_chunks_to_files(chunk_size=10, output_dir="fact-chunks")
        print(f"Total chunks written: {chunks_written}")
        
        # Get first chunk for display
        print("\n=== First Chunk Preview (10 facts) ===")
        sampler.reset_chunk_index()  # Reset to start from beginning
        first_chunk = sampler.get_next_chunk()
        for i, fact in enumerate(first_chunk[:3], 1):  # Show only first 3 for brevity
            print(f"{i}. {fact}")
        if len(first_chunk) > 3:
            print(f"... and {len(first_chunk) - 3} more facts in this chunk")
    
    # List directory files
    print("\n=== Directory Listing Demo ===")
    directory = "fact-chunks"
    files = sampler.list_directory_files(directory)
    print(f"Files in {directory}:")
    for file in files[:10]:  # Show first 10 files
        print(f"  - {file}")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")


if __name__ == "__main__":
    main()
