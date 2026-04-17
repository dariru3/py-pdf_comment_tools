# PDF Commenting and Highlighting Tool

This Python program automates the process of searching for keywords in a PDF document, highlighting the found instances, and adding comments to them. It then generates a summary of the occurrences for each keyword.

## Features

- Search for multiple keywords in a PDF document.
- Highlight found instances in the document.
- Add comments to the highlighted text.
- Customize the color of the highlight based on the keyword.
- Generate a summary of the keyword occurrences in the document.

## Dependencies

- PyMuPDF (fitz): for PDF processing
- Python's built-in `csv` and `sys` modules

## Usage

1. Prepare a CSV file with the format: 'keyword', 'comment', 'color'. This will be used as the keyword list. If you're using Japanese text, make sure to save the CSV in Unicode (UTF-8) format to preserve the Japanese characters.
2. Set up your configuration file (`config.py`) with the following parameters:
    - `"source file"`: The path to your input PDF file.
    - `"keywords list"`: The path to your keyword list CSV file.
3. Run the script: `python <script_name.py>`

## Functions

### comment_pdf

This is the main function of the script. It reads the CSV file with the keyword list, opens the PDF file, searches for the keywords in the document, highlights them, adds the comments, and then saves the modified PDF file. It also creates a summary of the occurrences of each keyword in the document.

### read_csv

This function reads the CSV file containing the keyword list and returns it as a list.

### highlight_text

This function adds highlights and comments to the matched keywords in the PDF document.

### create_summary

This function generates a summary of the occurrences of each keyword in the PDF document and writes it to a text file.

## Output

The output of the script is a modified version of the input PDF file with the added highlights and comments, as well as a text file containing the summary of the keyword occurrences.

## Resources

This project was developed using the following resources:

- [Inspiration code (outdated)](https://www.educative.io/courses/pdf-management-python/B8pGNP0loDQ)
- [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/index.html)
- [RGB float color values](https://antongerdelan.net/colour/)
- [Google Colab (virtual Python environment)](https://colab.research.google.com/)