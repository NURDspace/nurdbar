import time
import random
file = open('latin_words_uppercase.txt','r')
d = file.readlines()
file.close()
if len(d)==1: d = d[0].split('\r')

words = {0:['.']}
for x in d:
    if x.strip() != '':
        l = len(x.strip())
        if l not in words:
            words[l]=[]
        words[l].append(x.strip())

#for y in words:
#    print (str(y)+':'+str(len(words[y])))

oldtime = [-1,-1,-1]
currtime = [0,0,0]
#oldtime = [-1,-1,-1,-1,-1]
#currtime = [0,0,0,0,0]
owords=['','','','','']
while True:
    currtime[0] = int(time.strftime('%I'))
    currtime[1] = int(time.strftime('%M')[0])
    currtime[2] = int(time.strftime('%M')[1])
#    currtime[3] = int(time.strftime('%S')[0])
#    currtime[4] = int(time.strftime('%S')[1])
    for x in range(len(currtime)):
        if currtime[x] != oldtime[x]:
            owords[x] = random.choice(words[currtime[x]])+' '
    output=owords[0]
    for w in owords[1:]:
        if w == '. ':
            if output[-2] != '.':
                output = output[:-1]+w
        else:
            output = output+w
    oldtime = currtime[:]
    print (output)
    time.sleep(60)
