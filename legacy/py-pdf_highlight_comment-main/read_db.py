import shelve

def read_db(filename):
    with shelve.open(filename) as db:
        for key in db:
            print(f"{key}: {db[key]}")

read_db('input_folder/scanned_files')