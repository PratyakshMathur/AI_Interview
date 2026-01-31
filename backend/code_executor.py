"""Python code execution service"""
import subprocess
import tempfile
import os
import sys
from typing import Dict, Tuple

class CodeExecutor:
    """Execute Python code in a controlled environment"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        # Use the same Python interpreter that's running this code (venv Python)
        self.python_executable = sys.executable
    
    def execute_python(self, code: str) -> Tuple[bool, str, str]:
        """
        Execute Python code and return results
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute Python code using venv's Python interpreter
            result = subprocess.run(
                [self.python_executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir()
            )
            
            # Clean up
            os.unlink(temp_file)
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            return False, "", f"Code execution timed out ({self.timeout}s limit)"
            
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            return False, "", f"Execution error: {str(e)}"
