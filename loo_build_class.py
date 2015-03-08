from __future__ import print_function
import sys
import pickle
import numpy as np
#sys.path.insert(0, '/Users/rikka/liblinear-1.94/python')
#from liblinearutil import *
sys.path.insert(0, '/Users/rikka/libsvm-3.18/python')
from svmutil import *

def build_d(d, loo, c=1):     

    i = 1
    pos = d[0]
    neg = d[1]
    pl = len(pos)
    nl = len(neg)
    labels = [1 for b in range(pl)] + [-1 for b in range(nl)]
    bsqs =  pos + neg 
    #print(bsqs)
    #print(pl,nl)
    pl = float(1/pl)
    nl = float(1/nl)
    #print(pl,nl)


    #LIB LINEAR
    #prob = problem(labels, bsqs)
    #param = parameter('-q -s 2 -B 1 -c '+str(c)+' -w-1 '+str(nl)+' -w1 '+str(pl))
    #m = train(prob, param)
    #p_label, p_acc, p_val = predict([loo[0]],[loo[1]], m, '-q')
    #ACC, MSE, SCC = evaluations([loo[0]], p_label,)


    prob = svm_problem(labels, bsqs)
    param = svm_parameter('-q -t 2 -c '+str(c)+' -w-1 '+str(1/nl)+' -w1 '+str(1/pl))

    m = svm_train(prob, param)
    p_label, p_acc, p_val = svm_predict([loo[0]],[loo[1]], m, '-q')
    ACC, MSE, SCC = evaluations([loo[0]], p_label,)

    #filename = "tmp/"+str(i)
    #save_model(filename, m)
    #print(key,len(pos))
    #print(ACC,MSE,SCC,p_acc,p_val)
    return ACC
    '''
    with open(filename,'r') as f:
        tmp = f.readlines()
    n = np.array(tmp[6:-1],dtype=np.float32)
    n.resize(len(pos[0]),)
    n = n/np.linalg.norm(n)
    print(n)
    assert(np.all(n>-1))

    # associate this classifier with this event 
    d[key] = n
    
    #save data to file, pickled format
    f = open("data/"+name+".classif",'wb')
    pickle.dump(d,f)
    '''
def doer(c):
    fn = sys.argv[1]
    d= pickle.load(open(fn,"rb"))
    #NOT GENERIC CODE:
    ex = d["+"]
    wps = ex[2]
    #print(ex)
    gotwrong = []
    score = 0
    for j in range(len(ex[0])):
        resp = build_d((ex[0][:j]+ex[0][j+1:],ex[1]),(1,ex[0][j]),c)
        #print(resp)
        if resp == 100.0: score += 1
        else:
            print(ex[0][j])
            print(wps[j])
            print()
            gotwrong.append(j)
    c = j
    for j in range(len(ex[1])):
        resp = build_d((ex[0],ex[1][:j]+ex[1][j+1:]),(-1,ex[1][j]),c)
        #print(resp)
        if resp == 100.0: score += 1
        else: 
            gotwrong.append(j+c)
            print(ex[1][j])
            print(wps[j+c])
            print()

    total = len(ex[0])+len(ex[1])
    print(score,total)
    print(float(score)/float(total))
    print(gotwrong)


if __name__=="__main__":
    #for c in [0.00001,0.0001,0.001,0.01,0.1,1,10,100,1000,10000]:
    #    print(c)
    #    doer(c)
    doer(10)
