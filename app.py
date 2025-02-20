from flask import Flask, request, send_file, render_template
from docxtpl import DocxTemplate
import io
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

def clean_text(value):
    """Ensures the input is a string before processing."""
    return str(value).replace("\xa0", " ").strip() if value else ""

def clean_int(value, default=0):
    """Ensures the input is an integer, defaults to 0 if conversion fails."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def process_form_data(form):
    """Processes form data and converts it into the required context format."""
    try:
        context = {
            "document_version": [],
            "category_table": [],
            "credits_table": [],
            "total_credits": clean_int(form.get("total_credits", 0)),
            "dept_Code": clean_text(form.get("dept_Code", "")),
            **{key: [] for key in ["BSC", "ESC", "PCC", "ELECTIVE", "OEC", "MC", "EEC", "HSMC"]},
            **{f"course_table{i}": [] for i in range(1, 9)}
        }

        # Process Document Version
        i = 1
        while f"document_version_version_{i}" in form:
            context["document_version"].append({
                "version": clean_text(form.get(f"document_version_version_{i}", "")),
                "date": clean_text(form.get(f"document_version_date_{i}", "")),
                "author": clean_text(form.get(f"document_version_author_{i}", "")),
                "updates": clean_text(form.get(f"document_version_updates_{i}", "")),
                "approved_by": clean_text(form.get(f"document_version_approved_{i}", ""))
            })
            i += 1
        
        context["structure_total_credits"] = sum(item["credits"] for item in context["category_table"]) 
        context["regulation"] = clean_text(form.get("reg", ""))
        context["dept"] = clean_text(form.get(f"dept", ""))
        # Process Category Table (Structure of Program)
        i = 1
        while f"structure_of_program_category_{i}" in form:
            context["category_table"].append({
                "s_no": clean_int(form.get(f"structure_of_program_sno_{i}", i)),
                "category": clean_text(form.get(f"structure_of_program_category_{i}", "")),
                "credits": clean_int(form.get(f"structure_of_program_credits_{i}", "0")),
            })
            i += 1

        # Process Credits Table (Definition of Credit)
        i = 1
        while f"definition_of_credits_l_{i}" in form:
            context["credits_table"].append({
                "l": clean_text(form.get(f"definition_of_credits_l_{i}", "")),
                "t": clean_text(form.get(f"definition_of_credits_t_{i}", "")),
                "p": clean_text(form.get(f"definition_of_credits_p_{i}", "")),
            })
            i += 1

        j = 1
        for key in ["BSC", "ESC", "PCC", "ELECTIVE", "OEC", "MC", "EEC", "HSMC"]:
            
            context[f"{key}_total_credits"] = clean_text(form.get(f"{key}_total_credits", ""))

        # Process Courses (BSC, ESC, PCC, ELECTIVE, etc.)
        for key in ["BSC", "ESC", "PCC", "ELECTIVE", "OEC", "MC", "EEC", "HSMC"]:
            i = 1
            while f"{key}_title_{i}" in form:
                context[key].append({
                    "s_no": clean_int(form.get(f"{key}_sno_{i}", i)),
                    "title": clean_text(form.get(f"{key}_title_{i}", "")),
                    "sem": clean_text(form.get(f"{key}_semester_{i}", "")),
                    "ltpc": clean_text(form.get(f"{key}_ltpc_{i}", ""))
                })
                i += 1


        for table_key in [f"course_table{i}" for i in range(1, 9)]:           
            context[f"{table_key}_total_credits"] = clean_text(form.get(f"{table_key}_total_credits", ""))
           

        # Process Course Tables (course_table1 to course_table8)
        for table_key in [f"course_table{i}" for i in range(1, 9)]:
            i = 1
            while f"{table_key}_course_code_{i}" in form:
                context[table_key].append({
                    "s_no": clean_int(form.get(f"{table_key}_sno_{i}", i)),
                    "type": clean_text(form.get(f"{table_key}_type_{i}", "")),
                    "course_code": clean_text(form.get(f"{table_key}_course_code_{i}", "")),
                    "course_title": clean_text(form.get(f"{table_key}_course_title_{i}", "")),
                    "ltpc": clean_text(form.get(f"{table_key}_ltpc_{i}", "")),
                })
                i += 1

        return context
    except Exception as e:
        logging.error(f"Error in processing form data: {e}")
        raise e  # Raise the error for debugging

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            form_data = process_form_data(request.form)
            doc_io = generate_docx(form_data)

            return send_file(
                doc_io,
                as_attachment=True,
                download_name="Completed_Curriculum.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            return f"Error processing document: {e}", 500

    return render_template("index.html")

def generate_docx(context):
    """Generates the Word document using docxtpl and returns it as an in-memory file."""
    template_path = "curriculum.docx"
    
    if not os.path.exists(template_path):
        logging.error("Template file 'curriculum.docx' not found.")
        raise FileNotFoundError("Template file 'curriculum.docx' not found. Please upload the correct template.")
    
    try:
        doc = DocxTemplate(template_path)
        doc.render(context)
    except Exception as e:
        logging.error(f"Template rendering error: {e}")
        raise e  # Re-raise the error for debugging

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)

    return doc_io

if __name__ == "__main__":
    app.run(debug=True)
