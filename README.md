# Kindle Book Screenshot Script – Setup & Usage

This script automatically screenshots all the pages of a Kindle book in the Kindle for PC application and bundles it into a PDF.

# PRE-REQUISITES

Before using this script, make sure you have the following installed:

- Amazon Kindle for PC (desktop application)
- Python 3.14.x (or later; ensure it is added to your system PATH)
- Windows 10 or 11

This will not work on Linux or Mac!

# PROJECT SETUP STEPS

## Step 1 – Install Python

Download and install Python from https://www.python.org/downloads/windows/

During installation, check the option to "Add Python to PATH"

Verify installation by opening Powershell (Win + R → cmd) and typing:

python --version

You should see something like:

    Python 3.14.x

## Step 2 – Build the Python virtual environment

NOTE: THIS STEP ONLY NEEDS TO BE DONE ONCE.

Open the terminal. Navigate to the project root folder, for example:

    cd c:/temp/kindle_page_extractor

Run the batch script to build the virtual environment and install dependencies:

    build_venv.cmd

This will create a venv folder and install all required Python packages automatically.

## Step 3 – Open Kindle and Prepare the Book

Launch Kindle for PC, open the Kindle book you want to extract pages from, and make sure the book is on the cover page (first page).

## Step 4 – Run the Script

There are two ways to run the script.

### 4(a) - Batch Script

Please double-click 
    
    .\get_kindle_book.cmd

to execute the script with default parameters.

### 4(b) - Manual
In the same terminal window, run:

    .\venv\Scripts\python.exe .\main.py
    
This runs the script with default parameters.

### Notes for Both Methods

Screenshots will be saved to the default directory at

    .\Output\Screenshots\[YYYYMMDD_HHMMSS]

A PDF will be generated at the default location 

    .\Output\PDFs\[YYYYMMDD_HHMMSS]_Output.pdf
    

## Step 5

Repeat steps 3 and 4 for any subsequent kindle books.

# Optional – Custom Parameters

You can pass optional arguments to the script. For example:

    venv\Scripts\python.exe main.py --output-dir c:\temp\my_screenshots --book-margin 0.4 --pdf-file c:\temp\book.pdf --screenshot-limit 500

    --output-dir → Where screenshots are saved

    --book-margin → Left and right margins around the book. Express the margin size as a decimal between 0 and 1 to represent the percentage.

    --pdf-file → Output PDF path

    --screenshot-limit → Maximum screenshots to take

For more parameters, please run 

    .\venv\Scripts\python.exe main.py --help

# Logging

It should be noted that the log files for the script are stored at .\Logs\main.py.log

where "." refers to the project root.

# Appendix A: Libraries Needed

Based on the pip freeze, these are the libraries used.

    Deprecated==1.3.1
    img2pdf==0.6.3
    lxml==6.0.2
    MouseInfo==0.1.3
    packaging==25.0
    pikepdf==10.1.0
    pillow==12.0.0
    psutil==7.2.1
    PyAutoGUI==0.9.54
    PyGetWindow==0.0.9
    PyMsgBox==2.0.1
    pyperclip==1.11.0
    PyRect==0.2.0
    PyScreeze==1.0.1
    pytweening==1.2.0
    pywin32==311
    wrapt==2.0.1