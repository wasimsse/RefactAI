import logging
import torch
import os
import psutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_memory_usage():
    """Get current memory usage statistics."""
    process = psutil.Process()
    mem_info = process.memory_info()
    return {
        'rss': mem_info.rss / 1024 / 1024,  # MB
        'vms': mem_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }

def check_environment():
    """Check the environment setup and available resources."""
    try:
        logger.info("Checking environment setup...")
        
        # Check Python version
        import sys
        logger.info(f"Python version: {sys.version}")
        
        # Check PyTorch version and capabilities
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        logger.info(f"MPS available: {torch.backends.mps.is_available()}")
        
        # Check available memory
        mem_usage = get_memory_usage()
        import psutil
        total_memory = psutil.virtual_memory().total / (1024 * 1024 * 1024)  # GB
        logger.info(f"Total system memory: {total_memory:.1f}GB")
        logger.info(f"Current memory usage: {mem_usage['rss']:.2f}MB (RSS), {mem_usage['percent']:.1f}%")
        
        # Check model files
        model_path = Path("models/code-llama")
        if not model_path.exists():
            logger.error(f"Model directory not found at {model_path}")
            return False
            
        logger.info("\nChecking model files:")
        total_size = 0
        for file in model_path.glob("**/*"):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                if size_mb > 1000:  # Only show files larger than 1GB
                    logger.info(f"- {file.name}: {size_mb/1024:.1f}GB")
                total_size += size_mb
        
        logger.info(f"\nTotal model size: {total_size/1024:.1f}GB")
        logger.info(f"Available memory: {(total_memory - mem_usage['rss']/1024):.1f}GB")
        
        if total_size/1024 > (total_memory - mem_usage['rss']/1024):
            logger.warning("WARNING: Model size is larger than available memory!")
            logger.warning("Suggestions:")
            logger.warning("1. Use a smaller model variant")
            logger.warning("2. Use CPU offloading (will be very slow)")
            logger.warning("3. Use an API-based approach instead")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during environment check: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = check_environment()
    if success:
        logger.info("Environment check completed!")
    else:
        logger.error("Environment check failed!") 