import subprocess
import os
import glob

DOC_REL_DIR = 'doc-testfin'
DOC_OUT_REL_DIR = 'documents-txt'


#file_name = '007 Обручев - студентам СКГМИ.doc'
def totxt(file_name, output_path=DOC_OUT_REL_DIR):
    subprocess.call(["textutil", "-convert", "txt", f'{DOC_REL_DIR}/'+file_name, "-output", os.getcwd()+f'/{output_path}/'+file_name.rsplit(".",1)[0]+'.txt'])

for filename in glob.iglob(f'{DOC_REL_DIR}/*'):
    totxt(os.path.split(filename)[-1])