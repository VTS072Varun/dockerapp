
import os
import fitz  # PyMuPDF
import openai
import re
import logging
import json
from flask import Flask, request, jsonify
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import docx  # python-docx

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key from the environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key

app = Flask(__name__)

class ResumeParser():
    def __init__(self):
        # Ensure logs directory exists for logging
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # GPT-3 completion questions
        self.prompt_questions = """
            Summarize the text below into a JSON with exactly the following structure {
                basic_info: {
                    full_name, email, phone_number, City, Country, Province, linkedin_url, Experience_level, technical_expertise_in_skills , Experience_in_Years, Job_Title
                },
                work_experience: [{
                    job_title, company, location,
                }],
                Education: [{
                    Institution_Name, Start_year-End_Year, Degree, Percentage
                }],
                skills: [skill_name]
            }
        """
        
        # Set up this parser's logger
        logging.basicConfig(filename='logs/parser.log', level=logging.DEBUG)
        self.logger = logging.getLogger()

        # Initialize ChatOpenAI model with gpt-4
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.0, openai_api_key=openai_api_key)

    def pdf2string(self, pdf_path):
        """
        Extract the content of a pdf file to string using PyMuPDF.
        :param pdf_path: Path to the PDF file.
        :return: PDF content string.
        """
        pdf_text = ""
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pdf_text += page.get_text()
        doc.close()

        # Perform additional text preprocessing as needed
        pdf_text = re.sub('\s[,.]', ',', pdf_text)
        pdf_text = re.sub('[\n]+', '\n', pdf_text)
        pdf_text = re.sub('[\s]+', ' ', pdf_text)
        pdf_text = re.sub('http[s]?(://)?', '', pdf_text)

        return pdf_text

    def docx2string(self, docx_path):
        """
        Extract the content of a docx file to string using python-docx.
        :param docx_path: Path to the DOCX file.
        :return: DOCX content string.
        """
        doc = docx.Document(docx_path)
        doc_text = '\n'.join([para.text for para in doc.paragraphs])

        # Perform additional text preprocessing as needed
        doc_text = re.sub('\s[,.]', ',', doc_text)
        doc_text = re.sub('[\n]+', '\n', doc_text)
        doc_text = re.sub('[\s]+', ' ', doc_text)
        doc_text = re.sub('http[s]?(://)?', '', doc_text)

        return doc_text

    def query_completion(self, prompt):
        """
        Base function for querying OpenAI model.
        :param prompt: Prompt for the model.
        :return: Response from the model.
        """
        self.logger.info('query_completion: using gpt-4')

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']

    def query_resume(self, file_path, file_type):
        """
        Query OpenAI model for the work experience and/or basic information from the resume at the file path.
        :param file_path: Path to the file.
        :param file_type: Type of the file (pdf or docx).
        :return dictionary of resume with keys (basic_info, work_experience, Eduaction, skills).
        """
        resume = {}
        if file_type == 'pdf':
            file_str = self.pdf2string(file_path)
        elif file_type == 'docx':
            file_str = self.docx2string(file_path)
        else:
            raise ValueError("Unsupported file type")

        prompt = self.prompt_questions + '\n' + file_str

        response_text = self.query_completion(prompt)
        resume = json.loads(response_text)
        return resume

@app.route('/parse_resume', methods=['POST'])
def parse_resume():
    try:
        file = request.files['file']
        # Create uploads directory if it does not exist
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        file_path = f"uploads/{file.filename}"
        file.save(file_path)

        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx']:
            return jsonify({"error": "Unsupported file type"}), 400

        parser = ResumeParser()
        parsed_resume = parser.query_resume(file_path, file_extension)

        return jsonify(parsed_resume)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=3000, host='0.0.0.0')
