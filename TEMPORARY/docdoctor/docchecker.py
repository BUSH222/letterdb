import os
import glob
import re


pattern = re.compile(r'^\d{3}\sОбручев\s-\s.*?\.txt$')
DOC_OUT_REL_DIR = 'documents-txt'

truecnt = 0
falsecnt = 0
badlist = []

for filename in glob.iglob(f'{DOC_OUT_REL_DIR}/*'):
    badreason = None
    if pattern.match(os.path.split(filename)[1]):
        with open(filename) as txtfile:
            contents = txtfile.read()
            if 'Начало письма' in contents:
                truecnt += 1
                continue
            else:
                badreason = 'No beginning'
    else:
        badreason = 'Invalid name'
    falsecnt += 1
    badlist.append([os.path.split(filename)[1], badreason])

for k in badlist:
    print(f'{k[0]}; {k[1]}')
print()
print(truecnt)
print(falsecnt)
