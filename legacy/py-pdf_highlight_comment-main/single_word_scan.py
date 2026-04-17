import fitz

def comment_pdf(input_file:str, search_text:str, comment_info:str, pages:list=None):
    comment_title = "Python Highlighter"
    found_matches = 0
    pdfIn = fitz.open(input_file)
    
    # Iterate throughout pdf pages
    for pg,page in enumerate(pdfIn):
        pageID = pg+1
        # If required to look in specific pages
        if pages and pageID not in pages:
              continue

        # Use the search_for function to find the text
        matched_values = page.search_for(search_text,hit_max=20)
        found_matches += len(matched_values) if matched_values else 0

        #Loop through the matches values
        #item will contain the coordinates of the found text
        for item in matched_values:
            # Highlight found text
            annot = page.add_highlight_annot(item)

            # Add comment to the found match
            info = annot.info
            info["title"] = comment_title # author
            info["content"] = comment_info # comment
            # info["subject"] = "Python Commenter" # leave for now
            annot.set_info(info)

            annot.update()

    #Save to output file
    output_file = input_file.split(".")[0] + " comments.pdf"
    pdfIn.save(output_file,garbage=3,deflate=True)
    pdfIn.close()

    #Process Summary
    summary = {
         "Input File": input_file
       , "Output File": output_file
       , "Comment Title": comment_title
       , "Comment Info":  comment_info
       , "Matching Instances": found_matches
    }

    # Export Process Summary
    with open('summary.txt', 'w') as summary_txt:
        summary_txt.write("\n".join("{}: {}".format(i, j) for i, j in summary.items()))

comment_pdf(input_file="report 2021 JA.pdf", search_text="人権", comment_info="human rights = 人権")