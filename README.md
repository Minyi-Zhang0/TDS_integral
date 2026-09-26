
A analysis tool for TDS.

Dr. Minyi Zhang, Dr. Zhiyuan Ding

m.zhang@mpi-susmat.de

# Installation

1. Python

This software uses a GUI beased on streamlit and has been tested with Python 3.13. We recommend using Python's built-in `venv` module to create an isolated virtual environment.

2. Download the code

Download or clone the source code to a local directory. For example: `/efah_code_path/`

3. Create an venv environment

Open a Terminal on Linux or Command Prompt/PowerShell on Windows. Navigate to the directory where you would like to store the virtual environment, and run `python -m venv efah`. `efah` is the name of the virtual environment and can be replaced with any name you prefer. This command creates an `efah` directory containing the virtual environment.

4. Activate the venv environment

Run `source ./efah/bin/activate` for Linux or `.\efah\Scripts\activate.bat` for Windows

5. Install dependencies

With the virtual environment activated, install the required Python packages using `pip install -r /efah_code_path/requirements.txt`. Replace `/efah_code_path/` with the actual path to the downloaded source code.

6. Run GUI

Navigate to the source code directory, then start the app `streamlit run st_app.py`

Streamlit will display a local URL that you can open in your web browser to access the application.
