"""
Handles saving refactored files and managing file structure.
"""
import os
from pathlib import Path
from typing import Dict, Optional
import shutil
import json
from datetime import datetime

class RefactoringFileManager:
    def __init__(self, base_output_dir: str = "refactored_output"):
        self.base_output_dir = Path(base_output_dir)
        self.metadata_file = self.base_output_dir / "refactoring_metadata.json"
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(self.base_output_dir, exist_ok=True)
    
    def get_refactored_path(self, original_path: str) -> Path:
        """Convert original file path to refactored output path."""
        original_path = Path(original_path)
        relative_path = original_path.relative_to(original_path.anchor)
        return self.base_output_dir / relative_path
    
    def save_refactored_file(
        self,
        original_path: str,
        refactored_code: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Save refactored code to appropriate location and track metadata.
        Returns information about the saved file.
        """
        try:
            # Get output path
            output_path = self.get_refactored_path(original_path)
            
            # Ensure directory exists
            os.makedirs(output_path.parent, exist_ok=True)
            
            # Save refactored code
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(refactored_code)
            
            # Prepare metadata
            file_metadata = {
                "original_path": str(original_path),
                "refactored_path": str(output_path),
                "timestamp": datetime.now().isoformat(),
                "size": len(refactored_code),
            }
            
            # Add additional metadata if provided
            if metadata:
                file_metadata.update(metadata)
            
            # Update metadata file
            self._update_metadata(file_metadata)
            
            return file_metadata
            
        except Exception as e:
            print(f"Error saving refactored file: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _update_metadata(self, file_metadata: Dict):
        """Update the metadata file with new refactoring information."""
        try:
            # Load existing metadata
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {"refactorings": []}
            
            # Add new metadata
            metadata["refactorings"].append(file_metadata)
            
            # Save updated metadata
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Error updating metadata: {str(e)}")
    
    def create_zip_output(self) -> Optional[str]:
        """Create a ZIP file of all refactored files."""
        try:
            zip_path = f"{self.base_output_dir}_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip"
            shutil.make_archive(
                str(self.base_output_dir),
                'zip',
                str(self.base_output_dir)
            )
            return zip_path
        except Exception as e:
            print(f"Error creating ZIP: {str(e)}")
            return None
    
    def get_refactored_files(self) -> Dict:
        """Get information about all refactored files."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            return {"refactorings": []}
        except Exception as e:
            print(f"Error reading metadata: {str(e)}")
            return {"error": str(e), "refactorings": []} 