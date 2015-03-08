from __future__ import print_function
import pickle
import sys
import re
import json
import jsonrpclib
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from sklearn.feature_extraction.text import TfidfVectorizer

class mdreln:
    # this class represents a multiplication/division relationship
    def __init__(self,e1,e2):
        self.e1=e1
        self.e2=e2
        self.matrix = [[],[]]

    def startMatrix(self):
        #deal with each, per, and in
        if self.e1.each:
            self.matrix[0][0]=1
            self.matrix[0][1]=self.e2.num
            self.matrix[1][0]=self.e1.num
        elif self.e2.each:
            self.matrix[0][0]=self.e1.num
            self.matrix[0][1]=1
            self.matrix[1][1]=self.e2.num




class entity:
    # an entity corresponds to a quantified pl or mass noun
    # TODO distinguish pl and mass nouns from others somehow
    def __init__(self,num="",ent="",deps=None,s=None,p=None):
        self.num = num
        self.ent = ent
        self.adj = ""
        self.verb = ""
        self.role = ""
        self.ow = ""
        self.orels = ""
        self.loc = ""
        self.container = ""
        self.sent = ""
        self.text = ""
        self.each = False
        if deps != None:
            self.parsedeps(deps)
        if s != None:
            self.text = s["text"]
            self.getContainer(s)
        if p:
            self.processq(p)

    def processq(p):
        pdeps = p["indexeddependencies"]
        

    def getContainer(self,s):
        self.container = ' '.join([w[0] for w in s["words"] if w[1]["PartOfSpeech"] in ["PRP","NNP"]])
        print(self.container)

    def parsedeps(self,deps):
        #nn fix
        if 'nn' in deps:
            self.ent = deps['nn']+" "+self.ent

        preps = [x for x in deps if "prep" in x]
        locations = [deps[x] for x in preps if x.split("_")[1] in ["in","at","on"]]
        # need to check if prep_on is a noun or a verb
        self.loc = " ".join(locations)

        if "nsubj" in deps:
            self.verb = self.verb+" "+deps["nsubj"]
            self.role = "s"

        if "nsubjpass" in deps:
            self.verb = self.verb+" "+deps["nsubjpass"]
            self.role = "s"

        if "dobj" in deps:
            self.verb = self.verb+" "+deps["dobj"]
            self.role = "do"

        #TODO add idobj

        if "amod" in deps:
            self.adj += " "+deps["amod"]

        for x in deps:
            if x not in ["amod","dobj","nsubjpass","nsubj","prep_in","prep_at","prep_on","nn"]:
                #all other relations
                self.orels += " "+x
                self.ow += " "+deps[x]


        print(deps)
    def mod(self,li,mod):
        try:
            exec("self."+li+".append("+mod+")")
        except:
            print("Attribute "+li+" not found; nothing updated")
    
class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()

def getNouns(s):
    deps = s['indexeddependencies']

    nouns = []
    for i,w in enumerate(s['words']):
        if w[1]['PartOfSpeech'] in ['NNS',"NN"]: 
            nouns.append(w[0]+"-"+str(i+1))

    nound = {}
    for noun in nouns:
        ndeps = [x for x in deps if x[1] == noun]
        protod = [(x[0],x[2].split("-")[0]) for x in ndeps]
        ndeps = [x for x in deps if x[2] == noun]
        protod.extend([(x[0],x[1].split("-")[0]) for x in ndeps])
        d = {k:v for k,v in protod}
        nound[noun.split("-")[0]]=d

    return nound

def combine(a,b,op):
    #takes two entities and returns a combo of them.
    c = entity()
    for k in a.__dict__:
        if k == "num":
            c.num = a.__dict__[k]+" "+op+" "+b.__dict__[k]
        else:
            if k!='each':
                c.__dict__[k]= a.__dict__[k]+" "+b.__dict__[k]
    print(c.__dict__)
    return c


def training(trips,problem,target):
    #this function take the trips and creates positive and negative training instances from them
    global raw_counts 
    
    texamples = {x:([],[]) for x in ["+","*"]}
    for op,a,b in trips:
        a = a[1]
        b = b[1]

        #calculate statistics
        '''
        for w in s:
            if w not in raw_counts[op]:
                raw_counts[op][w] = 1
            else:
                raw_counts[op][w] += 1
        '''
        s = a.sent.lower().strip()+" "
        if op == "=":
            return texamples
        raw_counts[op] += s

        #build vector from two quantities:
        vec = []
        
        #local
        for k in a.__dict__:
            #print(k)
            if k in ["sent","ow","orels",'text','each']:continue
            ak = a.__dict__[k].strip().split()
            bk = b.__dict__[k].strip().split()
            if len([x for x in ak if x in bk])>0:
                dist = 0
            else:
                dist = 1
                for aw in ak:
                    asyns = wn.synsets(aw)
                    for asyn in asyns:
                        for bw in bk:
                            bsyns = wn.synsets(bw)
                            for bsyn in bsyns:
                                if asyn._pos != bsyn._pos: continue
                                try:
                                    sim = 1/(1+bsyn.res_similarity(asyn,brown_ic))
                                except:
                                    continue
                                if sim < dist:
                                    dist = sim
            vec.append(dist)
        #match location to entity
        if len(set(a.__dict__["loc"].split()).intersection(set(b.__dict__["ent"].split())))>0:
            vec.append(1)
        else: vec.append(0)
        if len(set(b.__dict__["loc"].split()).intersection(set(a.__dict__["ent"].split())))>0:
            vec.append(1)
        else: vec.append(0)

        if a.each:
            vec.append(1)
        else:
            vec.append(0)
        if b.each: vec.append(1)
        else: vec.append(0)

        if a.ent==target: vec.append(1)
        else: vec.append(0)
        if b.ent==target: vec.append(1)
        else: vec.append(0)

        vec.append(600)
        
        asent = a.__dict__['text'].lower().split()
        bsent = b.__dict__['text'].lower().split()
        for li in ["each","times","total","together","more","less","add","divide","split","equal","equally"]:
            if li in asent:
                vec.append(1)
            else:
                vec.append(0)
            if li in bsent: vec.append(1)
            else: vec.append(0)

        #global
        problem = problem.lower()
        if "in all" in problem: vec.append(1)
        else: vec.append(0)
        if "end with" in problem: vec.append(1)
        else: vec.append(0)
        problem = problem.split()
        for li in ["each","times","total","together","more","less","add","divide","split","left","equal","equally","now"]:
            if li in problem:
                vec.append(1)
            else:
                vec.append(0)



        #exit()
        for k in texamples:
            if op == k:
                texamples[k][0].append(vec)
            else:
                texamples[k][1].append(vec)
    return texamples



            
        





if __name__ == "__main__":
    brown_ic = wordnet_ic.ic('ic-brown.dat')
    raw_counts = {x:" " for x in ["+","*"]}
    wps = open('mult.problems').readlines()
    addlen = len(wps)
    wps.extend([x for x in open('div.problems').readlines()])
    pos = []
    neg = []
    texamples = {x:([],[],[]) for x in ["+","*"]}
    for j in range(len(wps)):
        print(wps[j])
        problem = wps[j]

        #process question
        replacements = {" three":' 3',' four':' 4',' five':' 5',' six':' 6',' seven':' 7',' eight':' 8',' nine':'9',' ten':' 10',' eleven':' 11',' week':' 7 days',' dozen':' 12', ' half ':' 2 '}
        
        for r in replacements:
            problem = problem.replace(r,replacements[r])
        q= [x.replace(",","") for x in problem.split()]
        numbs = [float(x.replace("$","")) for x in q \
                if re.compile("[$]?[0-9]+(\.[0-9]*)?$").match(x) is not None]

        story = nlp.parse(problem)

        #Get Target Entity
        #allnumbs = {"x":entity("x","x",None)}
        allnumbs = {}
        
        for i,s in enumerate(story["sentences"]):
            #this whole thing is bad b/c it overwrites stuff, make it not do that
            snouns = getNouns(s)

            for n in snouns:
                if 'num' in snouns[n]:
                    #print(snouns[n]['num'])
                    num = snouns[n]['num']
                    allnumbs[snouns[n]['num']] = entity(num,n,snouns[n],s)
                    #print(n,snouns[n])
                elif 'prep_of' in snouns[n]:
                    if snouns[n]['prep_of'].isdigit():
                        #print("HAPPENING")
                        num = snouns[n]['prep_of']
                        allnumbs[num] = entity(num,n,snouns[n],s)
                elif 'amod' in snouns[n]:
                    if snouns[n]['amod'] in ['many','much']:
                        #target
                        allnumbs['x']= entity('x',n,snouns[n],s)

            #This just gets other numbers
            sentnumbs = [x for x in [z[0] for z in s['words']] if x.isdigit() and x not in allnumbs]
            for x in sentnumbs:
                allnumbs[x] = entity(x,"???",None)
        if 'x' not in allnumbs:
           allnumbs['x']=entity('x','???',None) 

        problem = problem.lower()
        for num,e in allnumbs.items():
            ent = e.ent
            if ent[-1]=='s':
                ent = ent[:-1]
            if ent[-1]=='e':
                ent=ent[:-1]
            print(ent)
            if "each "+ent in problem:
                e.each = True
                print("good")
            elif "each" in problem:
                print("missed")



        #print(allnumbs.keys())
        prblmnumbs = [int(x) for x in allnumbs if x.isdigit()]

        if len(prblmnumbs)<2: continue
        if j < addlen:
            equation = str(prblmnumbs[0])+" + "+str(prblmnumbs[1])+" = x"
        else:
            equation = str(prblmnumbs[0])+" * "+str(prblmnumbs[1])+" = x"

        #parse eq:
        old_op = None
        parens = False
        trips = []
        cmplx,simple = equation.split("=")
        simple = simple.strip()
        cmplx = cmplx.split()
        i=0
        state = []
        opstack = []
        print(cmplx)

        while i<len(cmplx):
            c = cmplx[i]
            #print(i,c,state)
            #raw_input()
            if state == [] and not (c.isdigit() or c=='x'): 
                i+=1; continue

            if state == [] and (c.isdigit() or c=='x'):
                state = [(c,allnumbs[c])]
                i+=1;continue

            if c in ["+","-","/","*"]:
                op = c
                c = state[-1]
                d = cmplx[i+1]
                if d == "(":
                    j=1
                    while not d.isdigit():
                        d = cmplx[i+j]
                        j+=1
                    opstack.append((op,state.index(c)))
                    trips.append(("No Operation",(d,allnumbs[d]),c))
                    state.append((d,allnumbs[d]))
                    i+=j
                else:
                    trips.append((op,(d,allnumbs[d]),c))
                    state = state[:-1]
                    state.append((c[0]+op+d,combine(c[1],allnumbs[d],op)))
                    #print(i,c,state)
                    i+=2
                    continue
            if c == ")":
                if opstack == []:
                    i+=1
                    continue
                else:
                    op,c = opstack.pop()
                    c = state[c]
                    d = state[-1]
                    # this is c,d rather than d,c above because 
                    # perhaps the operation is more based on the first sentence?
                    trips.append((op,c,d))
                    state = [x for x in state[:-1] if x!= c]
                    state.append((c[0]+op+d[0],combine(c[1],d[1],op)))
                    i+=1

        #deal with = sign
        '''
        print(state)
        op = "="
        c = state[-1]
        d = (simple, allnumbs[simple])
        trips.append((op,d,c))
        '''

        #print(trips)
        problem = problem.split(". ")[-1]
        tmpexamples = training(trips,problem,allnumbs['x'].ent)
        for k in texamples:
            texamples[k][0].extend(tmpexamples[k][0])
            texamples[k][1].extend(tmpexamples[k][1])
            texamples[k][2].append(unicode(problem,errors="replace"))


    #Do stuff with the training data
    f2 = open("data/3.6.mdexamples_allfeatures",'wb')
    pickle.dump(texamples,f2)
    #for 2.11 stuff, exit and run diff code:
    exit()
    #build_d(texamples)

    tfidf = TfidfVectorizer(stop_words='english')
    tfs = tfidf.fit_transform(raw_counts.values()).toarray()
    feature_names = tfidf.get_feature_names()
    for row in range(tfs.shape[0]):
        srt = sorted([(x,i) for i,x in enumerate(tfs[row,:])],reverse=True)
        for x in srt[:10]:
            print(x)
            print(x[0],feature_names[x[1]])

        print("bk")
        for x in srt[-10:]:
            print(x)
            print(x[0],feature_names[x[1]])

