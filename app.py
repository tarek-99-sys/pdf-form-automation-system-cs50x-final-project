import os


from flask import Flask, render_template, request, redirect, url_for
from flask import send_file #user dialog box for saving the file in their computer
 
from pypdf import PdfReader, PdfWriter

#data.py to import curriculum data from user L-1, T-1 selection

from data import lookup


app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory to save uploaded files

@app.route('/', methods=['GET', 'POST'])

def index():

    if request.method == 'POST':
        
        #creating a dictionary whoose key is the same name of Entry_Form3.pdf field name 

        data_field = { 'id': None,
        'student_name_b': None,
        'father': None,
        'mother': None,
        'level': None,
        'term': None,
        'student_name': None,
        'village': None,
        'post': None,
        'zilla': None,
        'thana': None,
        'birth': None,
        'religion': None,
        'school': None,
        'college': None,
        'year_ssc': None,
        'roll_hsc': None,
        'gpa': None,
        'ssc_roll': None,
        'butex_exam': None,
        'phone': None,
        'present_address': None,
        'nationality': None,
        'ssc_board': None,
        'year_hsc': None,
        'hsc_board': None
        }

        level = request.form.get('level')  # Get the selected level from the form
        term = request.form.get('term')  # Get the selected term from the form
        key = level.replace("L-", "Level ") + " - " + term.replace("T-", "Term ")  # Normalize the key to match the format in the curriculum dictionary   

     #use the lookup function to get the course code and course name for the selected level and term
        # key = "Level 1 - Term 1"

        # lookup(key)  #this will return two dict one with course code and another with course name for the selected level and term

       #this should return two dictionary one with course code and another with course name for the selected level and term
        # code_dict, course_dict = lookup(key)

        #the sequece should be same like when the function was difined
        #first code_dict 
        #2nd course_dict

        code, course = lookup(key)


        html_data = request.form.to_dict()  # Convert form data to a dictionary

        #iterationeach dict for key value
        #if key match with html then store into new dict
        # such that it will take key from data_field and value from html_data

        match = { } #blank dict to store matched key value pair

        for key1 in data_field:
            if key1 in html_data:
                match[key1] = html_data[key1]  # Store the value from html_data in match dict with the same key




        file_open = PdfReader("Entry_Form3.pdf") #load the main pdf into memory of computer for reading

        file_write = PdfWriter() #create a blank pdf file so that we can writte on it without changing the original file
        file_write.append(file_open) #load all data from read pdf to writte pdf file.

        for page in file_write.pages:  #loop through all the pages of the writte pdf file
            file_write.update_page_form_field_values(page, match) 
            #update the form fields of ea
            # ch page of the writte pdf file with the new values
            file_write.update_page_form_field_values(page, code)

            file_write.update_page_form_field_values(page, course)

            # number_of_pages.add_text("This is a new line of text added to the pdf file.") 
            # #add new text to each page of the writte pdf file


        # Step 5: Ensure values are visible
        file_write.set_need_appearances_writer(True)

        # Step 6: Save output
        with open("output.pdf", "wb") as file:
            file_write.write(file)

       
        # Step 4: send to user (THIS triggers download)
        #using flask send_file module
        return send_file(
            "output.pdf",
            as_attachment=True,
            download_name=  f"{request.form.get('student_name')}_student_form.pdf"
            )
        
        

    else:
         
        return render_template('index.html')  # For GET requests, render the form

if __name__ == '__main__':
    app.run(debug=True)




