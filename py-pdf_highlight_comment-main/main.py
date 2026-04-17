import fitz
import sys
import csv
import os
import shelve
from config import config

# Difference between this file and the notebook file (.ipynb) is because of wider use case.
# This script can also be used to scan hundreds of files, outputing a summary file that includes
# how many times a word is found in a certain file.

def comment_pdf(input_folder:str, list_filename_csv:str, pages:list=None, highlight_output: bool=True):
    comment_name = "Highlighter"
    search_list = read_csv(list_filename_csv)
    matches_record = create_matches_record(search_list)
    
    for input_file in os.listdir(input_folder):
        # Check if PDF has already been scanned
        if input_file.endswith(".pdf"):
            # Check against database of scanned PDF filenames
            if is_file_scanned(input_file):
                print(f'Already scanned: {input_file}')
                continue
            full_path = os.path.join(input_folder, input_file)
            
            try:
                pdfIn = fitz.open(full_path)
            except Exception as e:
                error_message = f"Error opening file {full_path}: {e}"
                print(error_message)
                log_error(error_message)
                continue
            # Matches .ipynb file <<START>>
            for pg,page in enumerate(pdfIn):
                pageID = pg+1
                # UX
                sys.stdout.write(f"\rScanning page {pageID}...")
                sys.stdout.flush()

                # If required to look in specific pages
                if pages and pageID not in pages:
                    continue

                # Use the search_for function to find text
                for search_settings in search_list:
                    word, comment = search_settings[:2]
                    color = search_settings[2] if len(search_settings) > 2 else None

                    matched_values = page.search_for(word)
                    if matched_values:
                        update_matches_record(matches_record, word, matched_values)
                        if highlight_output:
                            highlight_text(matched_values, page, color, comment_name, comment)
            # UX
            sys.stdout.write("Done!")
            # Matches .ipynb file <<END>>
            
            # Save to output files
            if highlight_output:
                output_file = create_output_file(full_path, pdfIn)
            else:
                comment_name = "none"
                output_file = "none"
                pdfIn.close()
            
            create_summary(input_file, output_file, comment_name, matches_record)
            # Add PDF filename to database of scanned files
            log_scanned_file(input_file)
            print(f"Scan complete: {input_file}")

def read_csv(list_filename_csv):
    try:
        with open(list_filename_csv, 'r') as csv_data:
            csv_reader = csv.reader(csv_data)
            next(csv_reader) # skips the first row
            search_list = [row[:2] if len(row) == 2 else row[:3] for row in csv_reader]
        return search_list
    except Exception as e:
        print(f"Error reading CSV file {list_filename_csv}: {e}")
        sys.exit(1)

def create_matches_record(search_list):
   return {search[0]: 0 for search in search_list}

def update_matches_record(matches_record, word, match_values):
   matches_record[word] += len(match_values)

def highlight_text(matched_values, page, color, comment_title, comment):
    colors = {
        'blue': [0, 0, 1],
        'light blue': [.22, .9, 1],
        'green': [.42, .85, .16],
        'light green': [.77, .98, .45],
        'yellow': [1, .82, 0],
        'light yellow': [.99, .96, .52],
        'orange': [1, .44, .01],
        'light orange': [1, .75, .62],
        'red': [.90, .13, .22],
        'light red': [1, .50, .62],
        'pink': [.64, .19, .53],
        'light pink': [.98, .53, 1]
    }

    for item in matched_values:
        # Highlight found text
        annot = page.add_highlight_annot(item)
        if color and color.lower() in colors:
            annot.set_colors(stroke=colors[color.lower()])
        # Add comment to the found match
        info = annot.info
        info["title"] = comment_title
        info["content"] = comment
        annot.set_info(info)
        annot.update(opacity=0.4)

def create_output_file(input_file, pdfIn):
  output_file = input_file.split(".")[0] + " Highlighter.pdf"
  pdfIn.save(output_file,garbage=3,deflate=True)
  pdfIn.close()
  return output_file

def create_summary(input_file, output_file, comment_title, matches_record):
    with open('input_folder/summary.csv', 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # If the file is empty, write a header
        if csvfile.tell() == 0:
            csv_writer.writerow(["Word", "Count", "Input File", "Output File", "Comment Title"])

        for word, count in matches_record.items():
            summary_data = [word, count, input_file, output_file, comment_title]
            csv_writer.writerow(summary_data)

def log_scanned_file(filename: str):
    with shelve.open('input_folder/scanned_files') as db:
        db[filename] = True

def is_file_scanned(file_name: str) -> bool:
    with shelve.open('input_folder/scanned_files') as db:
        return file_name in db

def log_error(error_message: str):
    with open('input_folder/error_log.txt', 'a') as log_file:
        log_file.write(error_message + "\n")

if __name__ == '__main__':
    with shelve.open('input_folder/scanned_files') as db:
        pass
    comment_pdf(input_folder=config["source_folder"], list_filename_csv=config["keywords_list"], highlight_output=True)