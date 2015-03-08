import sys, re
if __name__ == "__main__":
    wps = open('mas.problems').readlines()
    answs = open('mas.answers').readlines()
    for j in range(len(wps)):
        #print(wps[j])
        problem = wps[j]
        answ = answs[j]

        #process question
        replacements = {" three":' 3',' four':' 4',' five':' 5',' six':' 6',' seven':' 7',' eight':' 8',' nine':'9',' ten':' 10',' eleven':' 11',' week':' 7 days',' dozen':' 12', ' half ':' 2 '}
        for r in replacements:
            problem = problem.replace(r,replacements[r])
        q= [x.replace(",","") for x in problem.split()]
        numbs = [float(x.replace("$","")) for x in q \
                if re.compile("[$]?[0-9]+(\.[0-9]*)?$").match(x) is not None]
        numbs.insert(0,float(answ))
        for x in numbs:
            print(x,end = " ")
        print()


