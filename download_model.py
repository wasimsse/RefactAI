from huggingface_hub import snapshot_download, login
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_model(repo_id, model_name, token):
    try:
        if not token:
            logger.error("Please provide a Hugging Face token!")
            logger.info("You can get your token from: https://huggingface.co/settings/tokens")
            return False
            
        logger.info(f"Logging in to Hugging Face...")
        login(token)
        
        logger.info(f"Starting download of {model_name}...")
        
        # Create models directory if it doesn't exist
        os.makedirs(f"models/{model_name}", exist_ok=True)
        
        # Download the model
        model_path = snapshot_download(
            repo_id=repo_id,
            local_dir=f"models/{model_name}",
            local_dir_use_symlinks=False,
            resume_download=True,
            token=token
        )
        
        logger.info(f"Model downloaded successfully to {model_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        return False

if __name__ == "__main__":
    # Get token from environment variable or user input
    token = os.getenv("HF_TOKEN")
    if not token:
        token = input("Please enter your Hugging Face token: ").strip()
    
    # Download Qwen2.5-Coder (3.0B)
    success = download_model(
        repo_id="Qwen/Qwen2.5-Coder-3B",
        model_name="qwen2.5-coder-3b",
        token=token
    )
    
    if success:
        logger.info("Download completed successfully!")
    else:
        logger.error("Download failed!") 