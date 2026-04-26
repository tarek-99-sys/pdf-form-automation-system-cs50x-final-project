# MY PROJECT TITLE: Student Form Fillup for Semester Final Exam

#### Video Demo:  <  https://youtu.be/FkmCYmiuRWY >

#### Description:
This project use pdfpy prebuilt libaray in pyhton for creation of filled Exam admission for my university. After running this program a responsive form will appear in the browser and after fillng the form user would get dialouge to download his semester final admit card without need of envolment of handwritting. This will saved a lot of time for student. The pdf annotation field were filled with fypdf library and html form with css for style. For backend, data communication pyhton flask and relevent library were use. For most of the HTML form design Bootstrap pre build component were used for saving time and effort. The pdf field on the original pdf file named "Entry_Form3.pdf" were used and sejda was used to create suitable pdf annotation text filed on this pdf. annotation.py is used for reading the text filed in the original file so that I can set the coresponding key from HTML form input.



---

## Overview

This project generates a PDF form dynamically based on user input from an HTML form. The system maps user-submitted data to predefined PDF fields and fills them accordingly.

This Python project automates admit card generation. Students select semester/term, and the system fetches academic and personal data, fills a PDF template, and outputs a ready-to-print file, removing manual writing and reducing errors.


---

## Workflow Explanation

First, all necessary libraries are imported. Additionally, a `lookup` function is defined in `data.py`, which is responsible for retrieving the corresponding course names and course codes and preparing them for insertion into the PDF fields.

---

## Flask Routing and Form Handling

An `@app.route` is created to handle data submission. The request method `"POST"` is used because the frontend HTML form sends user input data through this method.

* The HTML form communicates with the backend via the POST request.
* POST is also used to render and process the submitted form data securely.

---

## Data Field Mapping Strategy

A dictionary named `data_field` is created with keys that exactly match the HTML form field names.

* All values are initially set to `None`.
* This structure allows dynamic mapping instead of hardcoding values.
* Through iteration, the keys are matched with incoming form data.

This mapping is necessary because, according to **pypdf documentation**, the function:

```
update_page_form_field_values(page, data)
```

requires that dictionary keys must match the PDF form field annotations exactly. Only then will the corresponding values be inserted correctly into the PDF.

---

## Course Data Structure (`data.py`)

All course-related data (from first semester to last) is stored in `data.py`.

* The data is organized as a **nested dictionary**.
* Each semester (Level-Term) has its own dictionary.
* Example key format:

  ```
  "Level 1 - Term 1"
  ```

A total of **8 dictionaries** are created for 8 semesters.

### Purpose

When a user selects:

* Level → `L-1`
* Term → `T-1`

The system converts this into:

```
"Level 1 - Term 1"
```

This key is then used to access the corresponding course data from the nested dictionary.

---

## Lookup Function Logic

The `lookup` function is defined to process course data.

* It returns **two dictionaries**:

  * One for course codes (`c1, c2, c3...`)
  * One for course names (`s1, s2, s3...`)

### Implementation Details

* Two empty dictionaries are initialized.
* Iteration is performed over course data.
* `f-string` formatting is used to dynamically generate keys like:

  * `s1, s2, s3...` → course names
  * `c1, c2, c3...` → course codes

### Why this structure?

Because **pypdf only updates fields whose names match the PDF form field annotations**, this naming convention ensures proper mapping.

As a result, the correct course names and codes are inserted into the PDF file (`Entry_Form3.pdf`).

---

## Using Lookup in Main App

In `app.py`, the `lookup` function is called.

* The returned values are stored in:

  * `code` dictionary
  * `course` dictionary

These are later merged into the final mapping dictionary used for PDF updates.

---

## PDF Processing

### Reading the Template

```
file_open = PdfReader("Entry_Form3.pdf")
```

* Loads the template PDF into memory.

### Writing Output

```
file_write = PdfWriter()
```

* Used to create a new PDF file.
* Ensures the original template is not modified or corrupted.

---

## Updating PDF Fields

From pypdf documentation:

```
for page in file_write.pages:
    file_write.update_page_form_field_values(page, match)
```

* Iterates through all pages.
* Updates form fields using the `match` dictionary.

---

## Ensuring Field Visibility

```
file_write.set_need_appearances_writer(True)
```

* Ensures updated values are visible in the PDF.
* Without this, fields may appear unchanged even though they are updated internally.

---

## Sending File to User

Flask’s `send_file` function is used to send the generated PDF to the user as a download.

### Dynamic File Naming

```
f"{request.form.get('student_name')}_student_form.pdf"
```

* Uses the student’s name for the file.
* Makes it easier to identify and print later.

---

## Form Data Processing

```
html_data = request.form.to_dict()
```

* Converts incoming form data into a dictionary for easy handling.

### Matching Logic

```
match = {}

for key1 in data_field:
    if key1 in html_data:
        match[key1] = html_data[key1]
```

### Explanation

* A new dictionary `match` is created.
* Iterates over `data_field` keys.
* If a key exists in submitted form data, it is added to `match`.

This ensures:

* Only valid and expected fields are processed.
* Clean mapping between HTML input and PDF fields.

---

## String Manipulation for Level-Term

User input like:

```
L-1, T-1
```

is converted into:

```
"Level 1 - Term 1"
```

This transformation is necessary to match the key format used in the nested dictionary in `data.py`.

---

### Explanation annotation.py
This was used initailly for reading the field that was created using sejda and knowing all the field name from output, so that i can set coresponde key : value pair in dictionary which coresponde to pyhton dictionary and HTML FORM user input.


## Summary

* HTML form → sends data via POST
* Data is converted to dictionary
* Matching keys are filtered dynamically
* Level-Term selection maps to course dataset
* `lookup` generates structured course/code dictionaries
* pypdf fills PDF fields based on exact key matching
* Output PDF is generated and sent to user with a dynamic filename

---

