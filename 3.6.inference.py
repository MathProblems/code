from __future__ import print_function
import pickle
import sys
import re
import json
import jsonrpclib

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()

if __name__=="__main__":
    wps = open("3.6.problems").readlines()
    for prblm in wps:
        # preprocess prblm
        # first pass: extract entities, bare numbers. Resolve pronouns, barenumbers
        # process each sentence. Sentences can explain an operation, modify a container,
        # or explain a proportion relationship between entities.



