from pypdf import PdfReader

#this file is for testing the annotation of the pdf file and to see the field name of the pdf file

reader = PdfReader("Entry_Form3.pdf")
fields = reader.get_fields()

for page in reader.pages:
    
    for field in fields:
        
         print(field)