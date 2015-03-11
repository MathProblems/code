from __future__ import print_function
import sys
import json
import jsonrpclib

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()

def getTarget(problem):

    #extract question
    question = problem.split(".")[-1]
    if len(question)<3:
        print(question)
        return -1

    #parse question
    try:
        parse = nlp.parse(question.lower())
        deps = parse['sentences'][0]['indexeddependencies']
        howdep = [x for x in deps if 'how-' in x[2]][0]
        unitdep = howdep[1].split("-")[0]
        if unitdep == 'many':
            manydep = [x for x in deps if 'many-' in x[2]][0]
            target = manydep[1].split("-")[0]
        if unitdep == 'much':
            manydep = [x for x in deps if 'many-' in x[2]][0]
            target = manydep[1].split("-")[0]
        else:
            #unit is something more complicated that needs to be dealt with 
            #in another way
            return -1
        return target
    except:
        return -1

if __name__=="__main__":
    getTarget("Albert has two snakes. The garden snake is 10 inches long. The boaconstrictor is 7 times longer than the garden snake. How many inches is the boaconstrictor?")
