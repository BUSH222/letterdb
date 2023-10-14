import subprocess
import os
import glob


DOC_REL_DIR = 'documents'
DOC_OUT_REL_DIR = 'documents-txt'


def totxt(file_name, output_path=DOC_OUT_REL_DIR):
    """Convert to txt using subprocess."""
    subprocess.call(["textutil", "-convert", "txt", f'{DOC_REL_DIR}/'
                    + file_name, "-output", os.getcwd()+f'/{output_path}/'
                    + file_name.rsplit(".", 1)[0]+'.txt'])


for filename in glob.iglob(f'{DOC_REL_DIR}/*'):
    totxt(os.path.split(filename)[-1])
