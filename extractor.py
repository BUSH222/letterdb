import re
import glob


DOC_REL_DIR = 'documents'
DOC_OUT_REL_DIR = 'documents-txt'

for filename in glob.iglob(f'{DOC_OUT_REL_DIR}/*'):
    with open(filename) as txtfile:
        contents = txtfile.read()
        result = re.search(r'Начало письма(.*?)В. Обручев', contents, re.DOTALL)
        if result:
            print(result.group(1)+'В. Обручев', file=open('letterout.txt', 'a'))
    print('\n!\n!\n!\n!\n!', file=open("letterout.txt", 'a'))
