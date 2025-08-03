import subprocess
import tempfile
import os
import shutil

def convert_audio(input_path: str) -> str:
    """
    Convert audio to 16kHz mono WAV using SoX.
    Returns path to temporary converted file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create temporary file for output
    fd, output_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    try:
        # Build SoX command
        command = [
            "sox", input_path,
            "-r", "16000",          # Sample rate
            "-c", "1",              # Mono channel
            "-b", "16",             # 16-bit depth
            "-e", "signed-integer", # PCM encoding
            output_path
        ]
        
        # Execute conversion
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise RuntimeError(f"SoX conversion failed: {e.stderr}") from e
    except FileNotFoundError:
        if shutil.which("sox") is None:
            raise RuntimeError("SoX not found. Please install SoX first")
        raise
