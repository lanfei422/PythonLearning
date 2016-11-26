# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor
This is a temporary script file.
"""
from decimal import Decimal
from decimal import getcontext
import math
import sys
import threading
import Queue
import traceback
import os
import os.path
from threading import Lock
getcontext().prec = 6

lock=Lock()
# 定义一些Exception，用于自定义异常处理

class NoResultsPending(Exception):
    """All works requests have been processed"""
    pass


class NoWorkersAvailable(Exception):
    """No worket threads available to process remaining requests."""
    pass


def _handle_thread_exception(request, exc_info):
    """默认的异常处理函数，只是简单的打印"""
    traceback.print_exception(*exc_info)


# calculate formulas

class Formula:
    def __init__(self, tuple):
        self.aef = tuple[0]
        self.aep = tuple[1]
        self.anf = tuple[2]
        self.anp = tuple[3]

    def calculate(self):
        print ""


class Wong2(Formula):
    def calculate(self):
        susp_score = self.aef - self.aep
        return susp_score


class Op2(Formula):
    def calculate(self):
        susp_score = Decimal(self.aef) - Decimal(self.aep) / Decimal(self.aef + self.anf + 1)
        return susp_score


class Jaccard(Formula):
    def calculate(self):
        susp_score = Decimal(self.aef) / Decimal(self.aef + self.aep + self.anf+1)
        return susp_score


class Ochiai(Formula):
    def calculate(self):
        susp_score = Decimal(self.aef) / Decimal(math.sqrt((self.aef + self.anf) * (self.aef + self.aep)+1))
        return susp_score


class Tarantula(Formula):
    def calculate(self):
        fz = Decimal(self.aef) / Decimal(self.aef + self.anf+1)
        fm = fz + Decimal(self.aep) / Decimal(self.aep + self.anp+1)
        susp_score = fz / fm
        return susp_score


class Ochiai2(Formula):
    def calculate(self):
        fz = self.aef * self.anp
        fm = Decimal(
            math.sqrt((self.aef + self.aep) * (self.anp + self.anf) * (self.aef + self.anf) * (self.aep + self.anp))+1)
        susp_score = fz / fm
        return susp_score


###load spectra and matrix,and calculate sus_score.
class Task:
    def __init__(self, version, spectra_url, matrix_url):
        self.exception=False
        self.version = version
        self.spectra_url = spectra_url
        self.matrix_url = matrix_url


class TestProgram:
    def __init__(self, version, spectra_url, matrix_url):
        self.version = version
        self.spectra = self.loadSpectra(spectra_url)
        self.matrix = self.loadMatrix(matrix_url)
        self.caseInfo = self.loadCaseInfo(matrix_url)
        self.susScore = {}
        self.bias={}

    def loadSpectra(self, url):
        tmp_dict = {}
        with open(url, 'r') as Spectras:
            for (lineNo, spectra) in enumerate(Spectras):
                tmp_dict[lineNo] = spectra.rstrip()
        return tmp_dict

    def loadMatrix(self, url):
        tmp_dict = {}
        with open(url, 'r') as Matrixs:
            for (caseNo, raw_case) in enumerate(Matrixs):
                case = raw_case.split(' ')[0:-1]
                tmp_dict[caseNo] = case
        return tmp_dict

    def loadCaseInfo(self, url):
        tmp_dict = {}
        with open(url, 'r') as CaseInfos:
            for (caseNo, raw_info) in enumerate(CaseInfos):
                info = raw_info.split(' ')[-1]
                tmp_dict[caseNo] = info
        return tmp_dict

    def genTuples(self):
        print "----generate tuples----\n"
        tuples = {}
        for key in self.spectra.keys():
            tuples[self.spectra[key]] = [0, 0, 0, 0]  # aef,aep,anf,anp
            for ts_key in self.caseInfo.keys():
                if self.caseInfo[ts_key].split('\n')[0] == '+':
                    if self.matrix[ts_key][key] == '0':
                        tuples[self.spectra[key]][3] += 1
                    else:
                        tuples[self.spectra[key]][1] += 1
                else:
                    if self.matrix[ts_key] == '0':
                        tuples[self.spectra[key]][2] += 1
                    else:
                        tuples[self.spectra[key]][0] += 1
        return tuples

    def calculateSusScore(self, tuples):
        print "----calculate suspicious scores----\n"
        tmp_dict = {}
        for (key,tuple) in tuples.items():
            try:
                tmp_dict[key] = self.calculate(tuple)
            except:
                print "calculate error\n"
                tmp_dict[key]=0
        self.susScore = tmp_dict

    def calculate(self, tuple):
        print "----in calculate----" + str(tuple[0]) + " " + str(tuple[1]) + " " + str(tuple[2]) + " " + str(tuple[3])
        wong2 = Wong2(tuple)
        op2 = Op2(tuple)
        jaccard = Jaccard(tuple)
        ochiai = Ochiai(tuple)
        taran = Tarantula(tuple)
        ochiai2 = Ochiai2(tuple)
        formulas = {}
        formulas["Wong2"] = wong2
        formulas["Op2"] = op2
        formulas["Jaccard"] = jaccard
        formulas["Ochiai"] = ochiai
        formulas["Tarantula"] = taran
        formulas["Ochiai2"] = ochiai2

        results = {}
        print "----before calculate----"
        for (key, val) in formulas.items():
            results[key] = val.calculate()
            print "the sus value is " + str(results[key])
        return results

    def saveToFile(self, url):
        #print self.susScore
        cur_parent=os.path.join(url,self.version)
        if not os.path.exists(cur_parent):
            os.makedirs(cur_parent)
        cur_path=os.path.join(cur_parent,"result_original.txt")
        print "open file to save the result:" + str(cur_path)+"\n"
        with open(cur_path,"w+") as sFile:
            sFile.truncate()
        with open(cur_path, "a") as sFile:
            for (key, value) in self.susScore.items():
                outputStr = str(key)
                for (kf, vf) in value.items():
                    outputStr += "," + str(kf) + "#" + str(vf)
                sFile.write(outputStr + "\n")




class TaskProducer:
    def __init__(self, url):
        self.url = url
        self.threadPool = []

    def genTask(self, spectra_name, matrix_name):
        counter=0
        print "----generate task----\n"
        for parent, dirnames, filenames in os.walk(self.url):
            for dirname in dirnames:
                print "task's url is " + str(os.path.join(parent, dirname, spectra_name)) + "\n"
                task = Task(dirname, os.path.join(parent, dirname, spectra_name),
                            os.path.join(parent, dirname, matrix_name))
                self.threadPool.append(task)
                lock.acquire()
                counter+=1
                lock.release()
        return counter


def calculateY(result_queue,stop):
    for i in range(1,stop):
        cur=result_queue[i][1].susScore
        bias={}
        for j in range(i):
            iter=result_queue[j][1].susScore
            for key in iter.keys():
                bias[key]={}
                for (k,v) in iter[key].items():
                    if k in bias[key].keys():
                        bias[key][k]+=v
                    else:
                        bias[key][k]=v
        for key in bias.keys():
            for k in bias[key].keys():
                bias[key][k]= bias[key][k]/(i)

        result_queue[i][1].bias=bias

def finalStep(result_queue,path):
    for (kr,vr) in result_queue:
        cur=vr.susScore

        cur_parent = os.path.join(path, kr.version)
        if not os.path.exists(cur_parent):
            os.makedirs(cur_parent)
        cur_path = os.path.join(cur_parent, "result.txt")
        with open(cur_path, 'w+') as file:
            file.truncate()
        with open(cur_path, 'a') as file:
            for (kc,vc) in cur.items():
                outputStr=str(kc)
                for (kf,vf) in vc.items():
                    outputStr+=","+str(kf)
                    if kc in vr.bias.keys():
                        print "original value is "+str(vf)+"###bias is "+str(vr.bias[kc][kf])
                        cur[kc][kf]=vf-vr.bias[kc][kf]
                        outputStr+="#"+str(cur[kc][kf])
                        print "result is "+str(cur[kc][kf])+"####"+str(vr.susScore[kc][kf])
                    else:
                        outputStr+="#"+str(vf)
                print outputStr
                file.write(outputStr+"\n")


def writeResult2File(result_queue,path):
    for (kr,vr) in result_queue:
        cur_version=kr.version
        cur_parent=os.path.join(path,cur_version)
        if not os.path.exists(cur_parent):
            os.makedirs(cur_parent)
        cur_path=os.path.join(cur_parent,"result.txt")
        print cur_path
        with open(cur_path, 'w+') as file:
            file.truncate()
        with open(cur_path,'a') as file:
            for (kc,vc) in vr.susScore.items():
                outputStr=str(kc)
                for (kf,vf) in vc.items():
                    outputStr+=","+str(kf)+"#"+str(vf)
                file.write(outputStr+"\n")

import time

if __name__ == "__main__":
    if len(sys.argv)!=4:
        print "input arguments number is error.example python SBFL.py project_path tmp_result_path result_path\n"
    else:
        project_path=sys.argv[1]
        tmp_result_path=sys.argv[2]
        result_path=sys.argv[3]


        #tpool = ThreadPool(4, 200, 300, 5)
        tproducer = TaskProducer(project_path)
        pd_counter=tproducer.genTask('spectra', 'matrix')
        sbfl_result=[]

        for task in tproducer.threadPool:
            tp = TestProgram(task.version, task.spectra_url, task.matrix_url)
            tuples = tp.genTuples()
            tp.calculateSusScore(tuples)
            tp.saveToFile(tmp_result_path)
            sbfl_result.append((task,tp))

        sbfl_result.sort(lambda x,y:cmp(x[0].version,y[0].version))

        calculateY(sbfl_result,pd_counter)
        finalStep(sbfl_result,result_path)
        # writeResult2File(sbfl_result,result_path)
        # tpool.stop()
        print "Stop"
