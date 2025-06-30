# run_both.py

import subprocess

# Start FastAPI with uvicorn
fastapi_process = subprocess.Popen(["uvicorn", "main:app"])

# Start Streamlit
streamlit_process = subprocess.Popen(["streamlit", "run", "app.py"])



# Wait for both processes to finish (they won’t until you stop them)
fastapi_process.wait()
streamlit_process.wait()

