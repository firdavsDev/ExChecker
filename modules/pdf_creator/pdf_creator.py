import pdfkit
from datetime import datetime
import jinja2
import string
import os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

class PdfCreator:
    def __init__(self):
        # status to check get template status
        self.finished_status = None

    @property
    def is_finished(self):
        return self.finished_status

    def _get_parity(self, list):
        n = sum(list)
        if n % 2 == 0:
            return 1
        else:
            return 0
    
    #TODO: Posibilidad de añadir imagen o logo a la plantilla
    def create_pdf(self, 
                school_name: str,
                n_questions: int,
                n_responses: int,
                marker_url: str,
                lines: str = ""):
        
        self.finished_status = False
        
        total_rows = 10
        total_columns = 3
        rows = []
        count = 1
        for n in range(total_rows):
            elemnt_aux = []
            for c in range(total_columns):
                if count <= n_questions:
                    elemnt_aux.append(count)
                else:
                    elemnt_aux.append(False)
                count += 1
            rows.append(elemnt_aux)
            
        responses = list(string.ascii_uppercase)[:n_responses]
        
        # Insert metadata to template (n_questions and n_responses)
        info_questions = list(map(int, list('{0:05b}'.format(n_questions))))
        parity_questions = self._get_parity(info_questions)
        info_questions.insert(0, parity_questions)
        
        info_responses = list(map(int, list('{0:03b}'.format(n_responses))))
        parity_responses = self._get_parity(info_responses)
        info_responses.insert(0, parity_responses)
        # -- #
        
        templateLoader = jinja2.FileSystemLoader(searchpath=BASE_DIR)
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "template.html"
        template = templateEnv.get_template(TEMPLATE_FILE)
        outputText = template.render(school_name=school_name,
                                    lines=lines,
                                    rows=rows,
                                    responses=responses,
                                    marker_url=marker_url,
                                    info_questions=info_questions,
                                    info_responses=info_responses)
        options = {
            'encoding': "UTF-8",
            'quiet': '',
            'user-style-sheet': os.path.join(BASE_DIR, 'pdf_creator_css.css')
        }
        pdf = pdfkit.from_string(outputText, False, options=options)
        self.finished_status = True
        return pdf
    
if __name__ == '__main__':
    pdf_creator_obj = PdfCreator()
    pdf_creator_obj.create_pdf('Condestable', 'Matemáticas', 30, 5, 'Esta es la descripción')