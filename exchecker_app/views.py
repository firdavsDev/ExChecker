from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
import sys, signal, json, os, re, subprocess, socket, time, logging, cv2, atexit, shutil
from datetime import datetime
from random import randint
from secrets import token_hex
from PyPDF2 import PdfFileWriter, PdfFileReader
from bitstring import BitArray
from pdf2image import convert_from_path
import json
import base64
import time
import cv2
import subprocess
import jinja2
import csv
import imutils
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

## --- MODULES --- ##
sys.path.append(os.path.join(BASE_DIR,  'modules'))
from config_module import config_module
from files_module import files_module
from setup_logger.setup_logger import MyLogger
from init_log import init_log

## --- EXCHECKER MODULES --- ##
sys.path.append(os.path.join(BASE_DIR,  'exchecker_modules'))
from exchecker_mails import ExcheckerMails
from pdf_creator.pdf_creator import PdfCreator

# DEFINE PYTHON USER-DEFINE EXCEPTIONS

class OMRError(Exception):
    """Raised when there is an error in OMR system"""
    pass

class NoSolutions(Exception):
    """Raised when there are not any exam with solutions (code 00000)"""
    pass

class BadInfoCode(Exception):
    """Raised when cheksum from an exam does not match"""
    pass

class QuestionsResponsesNoMatch(Exception):
    """Raised when there are exams whose question info or response info does not match"""
    pass

class MultipleSolutions(Exception):
    """Raised when there are exams whose question info or response info does not match"""
    pass

class NoExams(Exception):
    """Raised when there are not exams to check (only detect solutions exam)"""
    pass

class BadRollCode(Exception):
    """Raised when Roll code is not complete filled"""
    pass

class ReapetedRoll(Exception):
    """Raised when a repeated Roll is found"""
    pass

# ------- CONFIG LOGGING ------- #

# -- Web App Logging -- ##
CONFIG_PATH = './config_file.json'
config_object = config_module.ConfigModule(CONFIG_PATH)
config = config_object.read_config()
setup_logger = MyLogger('', config['loglevel'], config['log_path'], 
                            filemode='maxzise', maxBytes=config['maxBytes_log'],
                            backupCount=config['backupCount'])
setup_logger.configurar_fichero()
log_initializer = init_log.LogInitializer(config['log_path'], CONFIG_PATH, 'EXCHECKER WEB APP', config['loglevel'])
log_initializer.print_init_log()
log_initializer.print_version_log(config['version_file'])
log_initializer.print_config_log()

# -- Users Logging -- ##
setup_logger = MyLogger('users_logger', 'INFO', config['users_log_path'], 
                            filemode='maxzise', maxBytes=config['maxBytes_log'],
                            backupCount=config['backupCount'])
setup_logger.configurar_fichero()
users_logger = setup_logger.getlog()

# ------- END CONFIG LOGGING ------- #

# Paths from javascript, html and css templates on templates folder. 
JS_PATH = "js/"
HTML_PATH = "html/"
CSS_PATH = "css/"

# To send emails. Disabled functionality.
'''mails_obj = ExcheckerMails(config['email_sender'],
                    config['email_sender_pass'],
                    config['web_url'])'''

template_processes = {}
tokens_tmp_file = []

def ls(path):
    list = []
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            list.append(file)
    return list

def json_to_object(string):
    return json.loads(string)

def object_to_json(obj):
    result = json.dumps(obj)
    if result == '[""]':
        return '[]'
    return result
    
def file_in_folder(file, folder, regex=False):
    files = ls(folder)
    for f in files:
        if regex:
            if re.search(file, f) != None:
                return True
        else:
            if file == f:
                return True
    return False

def files_in_folder(files, folder, regex=False):
    for f in files:
        if not file_in_folder(f, folder, regex):
            return False
    return True
    
def noone_in_folder(files, folder, regex=False):
    for f in files:
        if file_in_folder(f, folder, regex):
            return False
    return True

def get_template_date(t):
    t = t.split('.')[0]
    t = t.split('_')[0]
    Y,M,D = t.split('-')
    return Y + '/' + M + '/' + D

def get_template_name(t):
    t = t.split('.')[0]
    t = t.split('_')[-1]
    return ' '.join(t.split('-'))
    
def save_template(username, template, template_name_user):
    path = config['templates_dir'] + username + '/'
    if not os.path.isdir(path):
        os.mkdir(path)
    template_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '_' + template_name_user + '.pdf'
    template_path = path + template_name
    with open(template_path, 'wb+') as destination:
        destination.write(template)
        
    images = convert_from_path(template_path)
    if len(images) == 1:
        new_name = template_name.rsplit(".",1)[0] + '.jpg'
        images[0].save(path + new_name, 'JPEG')

def create_tmp_path(token):
    tmp_path = config['checked_folder_tmp'] + str(token) + '/'
    if not os.path.isdir(config['checked_folder_tmp']):
        os.mkdir(config['checked_folder_tmp'])
        
    if os.path.isdir(tmp_path):
        shutil.rmtree(tmp_path)
    os.mkdir(tmp_path)
    
    return tmp_path

def create_input_output_path():
    request_token = randint(0,100000)
    input_path = config['inputs_folder'] + str(request_token) + '/' 
    ouput_path = config['output_dir'] + str(request_token) + '/'
    while os.path.isdir(input_path) or os.path.isdir(ouput_path):
        request_token = randint(0,100000)
        input_path = config['inputs_folder'] + str(request_token) + '/'
        ouput_path = config['output_dir'] + str(request_token) + '/'
    os.mkdir(input_path)
    os.mkdir(ouput_path)
    
    return input_path, ouput_path

def rm_input_output_path(input_path, ouput_path):
    shutil.rmtree(input_path)
    shutil.rmtree(ouput_path)

def create_template_file(n_questions, n_responses, input_path):
    templateLoader = jinja2.FileSystemLoader(searchpath=config['omr_template_path'])
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = config['omr_template_name']
    template = templateEnv.get_template(TEMPLATE_FILE)
    single_questions = []
    for q in range(1, n_questions+1):
        single_questions.append('q' + str(q))
    questions_row1 = []
    for q in range(1, n_questions+1, 3):
        questions_row1.append('q' + str(q))
    questions_row2 = []
    for q in range(2, n_questions+1, 3):
        questions_row2.append('q' + str(q))
    questions_row3 = []
    for q in range(3, n_questions+1, 3):
        questions_row3.append('q' + str(q))
    outputText = template.render(n_responses=n_responses,
                                single_questions=single_questions,
                                questions_row1=questions_row1,
                                questions_row2=questions_row2,
                                questions_row3=questions_row3)
    
    with open(input_path + 'template.json', 'w+') as destination:
        destination.write(outputText)
    

def run_omr(input_path, output_path, template_path):
    cmd = ['python', config['omr_main'],
           '--inputDir', input_path,
           '--outputDir', output_path,
           '--template', template_path]
    process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          env=os.environ.copy())
    process.wait()
    if process.returncode != 0:
        out = process.stdout.read().decode()
        logging.error(out)
        return False
    else:
        return True

def get_parity(list):
    n = sum(list)
    if n % 2 == 0:
        return 1
    else:
        return 0

def check_code_info(row):
    info_questions = [1 if row['qi1'] else 0,
                      1 if row['qi2'] else 0,
                      1 if row['qi3'] else 0,
                      1 if row['qi4'] else 0,
                      1 if row['qi5'] else 0,
                      1 if row['qi6'] else 0]
    q_parity = info_questions.pop(0)
    
    if sum(info_questions) == 0:
        logging.warning("Number of questions from an exam is 0. Probably bad scan")
        raise BadInfoCode
    
    if q_parity != get_parity(info_questions):
        logging.warning("Parity bit in info questions from an exam does not match")
        raise BadInfoCode
    
    info_responses = [1 if row['ri1'] else 0,
                      1 if row['ri2'] else 0,
                      1 if row['ri3'] else 0,
                      1 if row['ri4'] else 0]
    r_parity = info_responses.pop(0)
    
    if sum(info_responses) == 0:
        logging.warning("Number of responses from an exam is 0. Probably bad scan")
        raise BadInfoCode
    
    if r_parity != get_parity(info_responses):
        logging.warning("Parity bit in info responses from an exam does not match")
        raise BadInfoCode
    
    n_questions = BitArray(info_questions).uint
    n_responses = BitArray(info_responses).uint
    
    return n_questions, n_responses

def get_note(n_questions, n_responses, good_questions,
             max_note, penalty):
    if penalty == -1:
        # Penalty by formula
        penalty = 1/n_responses
    
    bad_questions = n_questions - good_questions
    normalized_note = good_questions - (bad_questions * penalty)
    if normalized_note < 0:
        return 0.0
    else:
        return (max_note * normalized_note) / n_questions

def bad_rotation(row):
    if len(row['Roll']) != 5:
        n_responses = 0
        for k in row:
            if k[0] == 'q' and k[1:].isnumeric():
                # It is a questions
                if len(row[k]) == 1:
                    n_responses += 1
        if n_responses < 3:
            return True
        else:
            return False
    else:
        return False

def generate_results(max_note,
                     penalty,
                     output_path):
    results_path = output_path + 'Results/results.csv'
    rows = []
    solutions = None
    n_questions = None
    n_responses = None
    roles = {}
    with open(results_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            filename = row['file_id']
            try:
                n_questions_tmp, n_responses_tmp = check_code_info(row)
            except BadInfoCode:
                # Check if is rotation is 180º
                '''if bad_rotation(row):
                    logging.info("Assuming that exam is oriented 180. Discarting.")
                    continue'''
                
                logging.warning("Error checksum info code")
                raise BadInfoCode("La codificación de preguntas y respuestas en el examen '" + filename + "' no es la correcta.\n" +
                                  "Esto puede deberse a que el sistema no ha detectado correctamente los campos del examen.\n" +
                                  "Por favor, prueba a volver a subir este documento.")
            
            if not n_questions:
                n_questions = n_questions_tmp
            if not n_responses:
                n_responses = n_responses_tmp
                
            if (n_responses_tmp != n_responses or
                n_questions_tmp != n_questions):
                logging.warning("The number of questios or responses does not match beetween exams")
                raise QuestionsResponsesNoMatch("El examen '" + filename + "' tiene una codificación del número de \
                    preguntas y respuestas diferente a la de los documentos ya subidos.")

            if len(row['Roll']) != 5:
                # Len roll is not valid
                raise BadRollCode("El código de alumno del examen '"+filename+"' no contiene los 5 digitos rellenados correctamente.")
            
            if row['Roll'] in roles:
                raise ReapetedRoll("El examen '"+filename+"' y el examen '"+ roles[row['Roll']] +"' contiene el mismo código de alumno.")
            roles[row['Roll']] = filename
            
            if row['Roll'] == '00000':
                solutions = row
            else:
                rows.append(row)

    if not solutions:
        raise NoSolutions("No hemos encontrado el examen con las soluciones (código de examen 00000).")
        #solutions = rows[0] # FOR TESTING
    
    #Check if solutions exam is wrong
    for k in solutions:
        if k[0] == 'q' and k[1:].isnumeric():
            # It is a questions
            if len(solutions[k]) > 1:
                logging.warning("Solutions exam have multiple responses.")
                raise MultipleSolutions("El examen solución (código 00000) tiene preguntas con múltiples soluciones")
    
    results = {}
    for r in rows:
        roll = r['Roll']
        questions = {}
        good_questions = 0
        for k in r:
            if k[0] == 'q' and k[1:].isnumeric():
                # It is a questions
                
                n_q = int(k[1:])
                if n_q > n_questions:
                    # question not considered
                    continue
                
                if r[k] == solutions[k]:
                    good_questions += 1
                questions[k] = r[k]
        questions['nota'] = str(get_note(n_questions, n_responses,
                                         good_questions,
                                         max_note, penalty))
        results[roll] = questions
        
    if not results:
        raise NoExams("Parece que no hemos encontrado ningún examen para corregir aparte del examen solución (código 00000)")

    return results

def generate_statics(results, max_note):
    roles = []
    notes = []
    n_approved = 0
    students_blanck_responses = 0
    students_multiple_responses = 0
    total_exams = len(results)
    for r in results:
        roles.append(str(r))
        notes.append(float(results[r]['nota']))
        if float(results[r]['nota']) >= (max_note/2):
            n_approved += 1
            
        for q in results[r]:
            if q == 'nota':
                continue
            if len(results[r][q]) > 1:
                students_multiple_responses += 1
                break
                
        for q in results[r]:
            if q == 'nota':
                continue
            elif len(results[r][q]) == 0:
                students_blanck_responses += 1
                break
    
    approved_percent = (n_approved*100) / total_exams
    fail_percent = 100 - approved_percent
    return (roles, notes, approved_percent, fail_percent,
            n_approved, total_exams-n_approved,
            (students_blanck_responses/total_exams)*100,
            (students_multiple_responses/total_exams)*100)

def mv_tmp_file_to_inputs(token, exams_folder):
    file_path = config['checked_folder_tmp'] + str(token) + '/*'
    cmd = 'mv' + ' ' + file_path + ' ' + exams_folder
    process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    process.wait()
    if process.returncode != 0:
        out = process.stdout.read().decode()
        logging.error(out)
        raise Exception(out)

def generate_tmp_token():
    token = randint(0,100000)
    while (token in tokens_tmp_file):
        token = randint(0,100000)
    return token

def create_csv(solutions_header, solutions):
    token = randint(0,100000)
    cvs_path = config['csvs_dir'] + str(token) + '/'
    while os.path.isdir(cvs_path):
        token = randint(0,100000)
        cvs_path = config['csvs_dir'] + str(token)
    os.mkdir(cvs_path)
    
    with open(cvs_path + 'resultados.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(solutions_header)
        writer.writerows(solutions)
        
    return 'csvs/' + str(token) + '/resultados.csv'


def save_tmp_file(f, token):
    path = create_tmp_path(token)
    filename = f.name
    type = f.content_type
    with open(path + filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
            
    if type.split('/')[1] == 'pdf':
        images = convert_from_path(path + filename)
        if len(images) == 1:
            new_name = filename.rsplit(".",1)[0] + '.jpg'
            images[0].save(path + new_name, 'JPEG')
        else:
            for i in range(len(images)):
                new_name = filename.rsplit(".",1)[0] + '_' + str(i) + '.jpg'
                images[i].save(path + new_name, 'JPEG')
                
        os.remove(path + filename)
        
        # Another option to convert pdf file
        '''
        inputpdf = PdfFileReader(open(path + filename, "rb"))
        if inputpdf.numPages > 1:
            for i in range(inputpdf.numPages):
                output = PdfFileWriter()
                output.addPage(inputpdf.getPage(i))
                new_name = filename.rsplit(".",1)[0] + '_' + str(i) + '.pdf'
                with open(path + new_name, "wb") as outputStream:
                    output.write(outputStream)
            os.remove(path + filename)'''
            
def decode_exam(exam):
    base64_bytes = exam.encode('ascii')
    exam_bytes = base64.b64decode(base64_bytes)
    return exam_bytes

def get_ip_client(request):
    return request.META['REMOTE_ADDR']

def email_in_db(email: str):
    try:
        User.objects.get(email=email)
    except User.DoesNotExist:
        return False
    except User.MultipleObjectsReturned as e:
        logging.error("There are more than one user registered with that email: " + str(e))
        return False
    else:
        return True

def rotate_file(file_path, angle):
    image = cv2.imread(file_path)
    
    rot = imutils.rotate_bound(image, angle=angle)
    cv2.imwrite(file_path, rot)

#----------------------VIEWS----------------------#
def main(request):
    #In this view it is saved user and IP in log
    
    user_ip = get_ip_client(request)
    
    if request.user.is_authenticated:
        user = request.user.username
        users_logger.info('Connected user: ' + user + ' [' + user_ip + ']')
    else:
        users_logger.info('Connected: [' + user_ip + ']')

    html = render(request, HTML_PATH+'main.html')
    return HttpResponse(html, content_type="text/html")

'''@login_required(redirect_field_name='', login_url='accounts/login/')
def dashboard(request):
    html = render(request, HTML_PATH+'dashboard.html')
    return HttpResponse(html, content_type="text/html")'''
    
def get_template(request):
    if request.method == 'POST':
        school_name = request.POST['school_name']
        lines = request.POST['lines']
        n_questions = int(request.POST['n_questions'])
        n_responses = int(request.POST['n_responses'])
        
        if request.user.is_authenticated:
            try:
                template_name_check = request.POST['template_name_check']
            except Exception:
                template_name = "Plantilla-Sin-Nombre"
            else:
                template_name = request.POST['template_name']
                template_name = '-'.join(template_name.split())

        '''elif penalty_type == '3':
            penalty = float(request.POST['penalty_value'])'''
            
        marker_url = config["marker_url"]
        
        pdf_creator_obj = PdfCreator()
        # Save token with obj to get status in get_progress_template() method
        token = request.session.__getitem__("get_template_token")
        template_processes[token] = pdf_creator_obj
        
        template = pdf_creator_obj.create_pdf(school_name,
                                          n_questions, n_responses,
                                          marker_url,
                                          lines)
        
        if request.user.is_authenticated:
            username = request.user.username
            save_template(username, template, template_name)
        response = HttpResponse(template, content_type="application/pdf")
        response['Content-Disposition'] = 'attachment; filename=plantilla_generada.pdf'
        return response

    # Generate token to download template and trace status
    if not request.session.__contains__('get_template_token'):
        token = token_hex(16)
        request.session.__setitem__('get_template_token', token)

    html = render(request, HTML_PATH+'get_template.html')
    return HttpResponse(html, content_type="text/html")
    
def check_exams(request):
    if request.method == 'POST':
        max_note = float(request.POST['max_note'])
        penalty_type = request.POST['penalty']
        if penalty_type == '1':
            penalty = 0.0
        elif penalty_type == '2':
            penalty = -1 # Indicates that depends of n responses
        elif penalty_type == '3':
            penalty = float(request.POST['penalty_value'])

        tokens = request.POST.getlist('filepond')
        input_path, output_path = create_input_output_path()
        for t in tokens:
            if not t:
                continue
            mv_tmp_file_to_inputs(t, input_path)
        
        # move files to others inputs (testing)
        files_to_move = ls(input_path)
        inputs = []
        for f in files_to_move:
            t = randint(0,100000)
            while os.path.isdir(input_path + str(t) + '/'):
                t = randint(0,100000)
            os.mkdir(input_path + str(t) + '/')
            shutil.move(input_path+f, input_path + str(t) + '/')
            inputs.append(input_path + str(t) + '/')
        
        for f in inputs:
            filename = ls(f)[0]
            success = run_omr(f, output_path, config['omr_template'])
            if not success:
                '''# Assuming that is rotate 90º or 270º
                rotate_file(f+filename, 90)
                success1 = run_omr(f, output_path, config['omr_template'])
                rotate_file(f+filename, 180)
                success2 = run_omr(f, output_path, config['omr_template'])
                if not success1 and not success2:'''
                
                rm_input_output_path(input_path, output_path)
                msg = "El examen '"+filename+"' no ha podido ser reconocido. Por favor, verifica la alineación de este documento e inténtalo de nuevo."
                html = render(request, HTML_PATH+'check_exams_error.html', {'text': msg})
                return HttpResponse(html, content_type="text/html")
        
        try:
            results = generate_results(max_note,
                                       penalty,
                                       output_path)
        except (NoSolutions, BadInfoCode,
                QuestionsResponsesNoMatch,
                MultipleSolutions, NoExams,
                BadRollCode, ReapetedRoll) as e:
            rm_input_output_path(input_path, output_path)
            html = render(request, HTML_PATH+'check_exams_error.html', {'text': str(e)})
            return HttpResponse(html, content_type="text/html")
        
        solutions_header = ['Codigo'] + list(list(results.values())[0].keys())
        solutions = []
        for r in results:
            row = [r]
            row = row + list(results[r].values())
            solutions.append(row)

        (roles, notes, approved_percent, fail_percent,
         n_approved, n_failed,
         students_blanck_responses,
         students_multiple_responses) = generate_statics(results, max_note)
        csv_file = create_csv(solutions_header, solutions)
        #create_template_file(n_questions, n_responses, input_path)
        
        rm_input_output_path(input_path, output_path)
        
        html = render(request, HTML_PATH+'exams_solutions.html', {'csv_file': None,
                                                                  'roles': roles,
                                                                  'notes': notes,
                                                                  'approved_percent': approved_percent,
                                                                  'fail_percent': fail_percent,
                                                                  'n_approved': n_approved,
                                                                  'n_failed': n_failed,
                                                                  'max_note': max_note,
                                                                  'mean': sum(notes)/len(notes),
                                                                  'solutions_header': solutions_header,
                                                                  'solutions': solutions,
                                                                  'students_blanck_responses': students_blanck_responses,
                                                                  'students_multiple_responses': students_multiple_responses,
                                                                  'csv_file': csv_file})
        return HttpResponse(html, content_type="text/html")
        
    html = render(request, HTML_PATH+'check_exams.html')
    return HttpResponse(html, content_type="text/html")

def upload_exams(request):
    if request.method != 'POST':
        raise Http404
    
    # A new exam has been uploaded
    token = generate_tmp_token()
    exam = request.FILES.get('filepond')
    save_tmp_file(exam, token)
    return HttpResponse(token, content_type="text/html")

@login_required(redirect_field_name='', login_url='accounts/login/')
def my_templates(request):
    user = request.user.username
    templates_folder = config['templates_dir'] + user + '/'
    
    if request.method == 'POST':
        template_name = request.POST['template_to_delete']
        template_name = template_name.split('/')[-1]
        template_name = template_name.split('.')[0]
        cmd = 'rm' + ' ' + templates_folder + template_name + '*'
        process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        process.wait()
        if process.returncode != 0:
            out = process.stdout.read().decode()
            logging.error(out)
    
    
    there_are_templates = True
    templates = []
    return_templates = []
    try:
        templates = ls(templates_folder)
    except FileNotFoundError:
        there_are_templates = False
    else:
        if not templates:
            there_are_templates = False
        else:
            templates.sort()
            for t in templates:
                if '.pdf' in t:
                    return_templates.append([get_template_date(t),
                                             get_template_name(t),
                                            'templates/' + user + '/' + t,
                                            'templates/' + user + '/' + t.split('.')[0] + '.jpg'])
            
            return_templates = [return_templates[n:n+4] for n in range(0, len(return_templates), 4)]
    
    html = render(request, HTML_PATH+'my_templates.html', {'there_are_templates': there_are_templates,
                                                           'templates': return_templates})
    return HttpResponse(html, content_type="text/html")

@login_required(redirect_field_name='', login_url='accounts/login/')
def download_all_templates(request):
    if request.method != 'POST':
        raise Http404
    
    user = request.user.username
    templates_folder = config['templates_dir'] + user + '/'
    cmd = 'zip -r -j ' + templates_folder + '/plantillas.zip ' + templates_folder +  '*.pdf'
    process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    process.wait()
    if process.returncode != 0:
        out = process.stdout.read().decode()
        logging.error(out)
        raise Exception
    
    with open(templates_folder + 'plantillas.zip', 'rb') as f:
        content = f.read()
        
    os.remove(templates_folder + 'plantillas.zip')
        
    http_response = HttpResponse(content, content_type='application/zip')
    http_response['Content-Disposition'] = 'attachment; filename=Plantillas.zip'
    return http_response

def get_progress_template(request):
    if request.method != 'POST':
        raise Http404
    
    try:
        token = request.session.__getitem__("get_template_token")
        pdf_creator_obj = template_processes[token]
    except KeyError:
        logging.warning("There is not get template process from this token")
        finished = True
    else:
        finished = pdf_creator_obj.is_finished
        if finished:
            del template_processes[token]
        elif finished == None:
            # Indicates than there is not get template process from this token
            logging.warning("There is not get template process from this token")
            finished = True

    return HttpResponse(object_to_json(finished), content_type="application/json")

#----------------------SERVER VIEWS (JS, CSS)----------------------#
def serve_js(request):
    js = render(request, JS_PATH+request.path)
    return HttpResponse(js, content_type="text/javascript")

def serve_css(request):
    css = render(request, CSS_PATH+request.path)
    return HttpResponse(css, content_type="text/css")


#----------------------USER VIEWS----------------------#
def login_view(request):
    all_users = User.objects.all()
    all_users = [u.get_username() for u in all_users]
    if request.method == 'GET':
        html = render(request, HTML_PATH+"login.html", {'all_users': all_users})
        return HttpResponse(html, content_type="text/html")
    elif request.method == 'POST':
        try:
            username = request.POST['username']
            #user = authenticate(request, username=username)
        except Exception as e:
            logging.warning("User must to specify an username")
            html = render(request, HTML_PATH+"login.html", {'all_users': all_users})
            return HttpResponse(html, content_type="text/html")
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            logging.warning("User " + username + " is not registered in database.")
            html = render(request, HTML_PATH+"login.html", {'wrong': True,
                                                            'all_users': all_users})
            return HttpResponse(html, content_type="text/html")
        else:
            login(request, user)
            return HttpResponseRedirect("/")
    else:
        raise Http404
              
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")
           
def register(request):
    if request.method == 'POST':
        try:
            user = User.objects.create_user(username=request.POST['username'],
                                            password=None,
                                            first_name=request.POST['first_name'],
                                            last_name=request.POST['last_name'])
            user.save()
        except Exception as e:
            logging.warning("There was an error registering user " + 
                            request.POST['username'] +
                            ": " + str(e))
            message = "Ha ocurrido un error registrando este usuario. Posiblemente ya exista en el sistema"
            html = render(request, HTML_PATH+"register.html", {'message': message})
            return HttpResponse(html, content_type="text/html")

        login(request, user)
        return HttpResponseRedirect("/")
        
        # This functionality lets aplication send email verification.
        # A token is generate and function verify_account() is called
        # when user click in link sended to his email account.
        '''data = {}
        data['first_name'] = request.POST['first_name']
        data['last_name'] = request.POST['last_name']
        data['email'] = request.POST['email']
        data['username'] = request.POST['username']
        data['pass'] = request.POST['pass']
        try:
            mails_obj.send_register(request.POST['email'], data)
        except Exception as e:
            logging.warning("Error sending register mail: " + str(e))
            message = "Ha ocurrido un error enviando el correo de verificación de cuenta.\
                    Por favor, inténtelo de nuevo más tarde."
        else:
            message = "Se le ha enviado un correo de verificación de cuenta al correo electrónico proporcionado.\
                    Dispone de 1 hora para acceder al enlace que le hemos enviado y verificar su cuenta."
        html = render(request, HTML_PATH+"register.html", {'message': message})
        return HttpResponse(html, content_type="text/html")'''
            
    html = render(request, HTML_PATH+"register.html")
    return HttpResponse(html, content_type="text/html")

def forgot_password(request):
    if request.method != 'POST':
        html = render(request, HTML_PATH+"forgot_password.html")
        return HttpResponse(html, content_type="text/html")

    email = request.POST['email']
    if not email_in_db(email):
        text = "Esta dirección de correo no corresponde a ninguna cuenta."
        html = render(request, HTML_PATH+"forgot_password_info.html", {'text': text})
        return HttpResponse(html, content_type="text/html")
    
    html = render(request, HTML_PATH+"restore_pass.html", {'email': email})
    return HttpResponse(html, content_type="text/html")
    
    
    # This functionality lets aplication send email to restore password.
    # A token is generate and function restore_password() is called
    # when user click in link sended to his email account.
    '''try:
        mails_obj.send_restore(request.POST['email'])
    except Exception as e:
        logging.warning("Error sending forgot pass mail: " + str(e))
        text = "Ha ocurrido un error enviando el correo de restauración de contraseña.\
                Por favor, inténtelo de nuevo más tarde."
    else:
        text = "Se le ha enviado un correo de recuperación a su dirección de correo electrónico.\
                Dispone de 1 hora para acceder al enlace que le hemos enviado y restaurar su contraseña."
    html = render(request, HTML_PATH+"forgot_password_info.html", {'text': text})
    return HttpResponse(html, content_type="text/html")'''

def verify_account(request):
    if request.method == 'POST':
        raise Http404()
    
    try:
        token = request.GET['t']
    except KeyError:
        raise Http404()
    
    ok, data = mails_obj.check_register(token)
    if not ok:
        raise Http404()
    
    user = User.objects.create_user(username=data['username'], email=data['email'],
    password=data['pass'], first_name=data['first_name'], last_name=data['last_name'])
    #login(request, user)
    html = render(request, HTML_PATH+"verify_account.html")
    return HttpResponse(html, content_type="text/html")

def restore_password(request):
    if request.method == 'GET':
        raise Http404()
    
    email = request.POST['email']
    new_pass = request.POST['password']
    u = User.objects.get(email=email)
    u.set_password(new_pass)
    u.save()
    html = render(request, HTML_PATH+"success_restore_pass.html")
    return HttpResponse(html, content_type="text/html")

    # This code is to use when email sender functionality is enabled
    '''if request.method == 'GET':
        try:
            token = request.GET['t']
        except KeyError:
            raise Http404()
        ok, email = mails_obj.check_restore(token)
        if ok:
            html = render(request, HTML_PATH+"restore_pass.html", {'email': email})
        else:
            raise Http404()
    elif request.method == 'POST':
        email = request.POST['email']
        new_pass = request.POST['password']
        u = User.objects.get(email=email)
        u.set_password(new_pass)
        u.save()
        html = render(request, HTML_PATH+"success_restore_pass.html")
    return HttpResponse(html, content_type="text/html")'''
    

#----------------------PAGE NOT FOUND (404)---------------------
def handler404(request, exception):
    html = render(request, HTML_PATH+"page_not_found.html")
    response = HttpResponse(html, content_type="text/html")
    response.status_code = 404
    return response

#---------------------SERVER ERROR (500)---------------------
def handler500(request):
    type, value, tb = sys.exc_info()
    html = render(request, HTML_PATH+"server_error.html", {"exception_value": value,
                                                           "value": type,
                                                           "tb": traceback.format_exception(type, value, tb)})
    response = HttpResponse(html, content_type="text/html")
    response.status_code = 500
    return response

