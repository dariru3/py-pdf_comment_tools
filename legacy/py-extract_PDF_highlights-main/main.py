import PyPDF2
import csv

def extract_highlighted_text(pdf_file):
    # Create a PDF object
    pdf = PyPDF2.PdfFileReader(pdf_file)
    # Create a list to store highlighted words and comments
    highlighted_words = []
    # Loop through each page in the PDF
    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)
        annotations = page.get("/Annots")
        # Check if the page has annotations
        if annotations:
            for annotation in annotations:
                # Check if the annotation is a highlight
                subtype = annotation.getObject()["/Subtype"]
                if subtype == "/Highlight":
                    # Get the highlight text
                    highlight = page.extractText(annotation).strip()
                    # Get the comment text if it exists
                    comment = annotation.get("/T")
                    if comment:
                        comment = comment.getObject().strip()
                    highlighted_words.append((highlight, comment))
    return highlighted_words

# Example usage:
if __name__ == '__main__':
    with open("sample.pdf", "rb") as pdf_file, open("output.csv", "w") as csv_file:
        highlighted_words = extract_highlighted_text(pdf_file)
        writer = csv.writer(csv_file)
        writer.writerow(["Highlight", "Comment"])
        for highlight, comment in highlighted_words:
            writer.writerow([highlight, comment])
