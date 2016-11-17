# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from decimal import *
import math
getcontext().prec = 6

class Formula:
    aef=""
    aep=""
    anf=""
    anp=""
    def __init__(self,tuple):
        aef=tuple[0]
        aep=tuple[1]
        anf=tuple[2]
        anp=tuple[3]
    def calculate(self):
        print ""
class Wong2(Formula):
    def calculate(self):
        susp_score=self.aef-self.aep

class Op2(Formula):
    def calculate(self):
        susp_score=Decimal(self.aef)-Decimal(self.aep)/Decimal(self.aef+self.anf+1)
        return susp_score

class Jaccard(Formula):
    def calculate(self):
        susp_score=Decimal(self.aef)/Decimal(self.aef+self.aep+self.anf)
        return susp_score

class Ochiai(Formula):
    def calculate(self):
        susp_score=Decimal(self.aef)/Decimal(math.sqrt((self.aef+self.anf)*(self.aef+self.aep)))
        return susp_score

class Tarantula(Formula):
    def calculate(self):
        fz=Decimal(self.aef)/Decimal(self.aef+self.anf)
        fm=fz+Decimal(self.aep)/Decimal(self.aep+self.anp)
        susp_score=fz/fm
        return susp_score
class Ochiai2(Formula):
    def calculate(self):
        fz=self.aef*self.anp
        fm=Decimal(math.sqrt((self.aef+self.aep)*(self.anp+self.anf)*(self.aef+self.anf)*(self.aep+self.anp)))
        susp_score=fz/fm
        return susp_score

class CalculateSBFL:
    version=-1

    # matrix={}   #pass or fail info ,each row is a test case.
    # suspicious_value={} #store entity's suspicious value
    # test_case_pof={}    #indicate which case is failed.
    # pof_tuple={}    #aef,aep,anf,anp
    # suspicious_value_remain={}  #bias suspiciousness

    spectra={}  #map every item in matrix to source code line.

    @classmethod
    def loadSpectra(url):
        spectra_file = open(url, 'r')
        for (lineNo, line) in enumerate(spectra_file):
            CalculateSBFL.spectra[lineNo] = line

    def __init__(self,version):
        self.version=version

    def load(self,url_m):
        matrix_file=open(url_m,'r')
        for (case,line) in enumerate(matrix_file):
            pass_fail_info=line.split(' ')
            self.test_case_pof[case]=pass_fail_info[-1]
            self.matrix=pass_fail_info[0:-1]

        self.pof_tuple=self.genTuple(CalculateSBFL.spectra,self.test_case_pof)

    def genTuple(self,spectra,testInfo):
        tuples={}
        for key in spectra.keys():
            tuples[key]=[0,0,0,0]
            for ts_key in testInfo.keys:
                if testInfo[ts_key]=='+':
                    if spectra[key]=='0':
                        tuples[key][3]+=1
                    else:
                        tuples[key][1]+=1
                else:
                    if spectra[key]=='0':
                        tuples[key][2]+=1
                    else:
                        tuples[key][0]+=1
        return tuples

    def diffTestSuite(self,cbfl):
        test_case_remain=[]
        cur_test_case=self.test_case_pof
        other_test_case=cbfl.test_case_pof
        for (ct,ot) in zip(cur_test_case.items(),other_test_case.items()):
            if ct[1]=='-' and ct[0]==ot[0] and ct[1]==ot[1]:
                continue
            test_case_remain.append(ot)
        tmp={}
        for (key,val) in test_case_remain:
            tmp[key]=val

        remainTuples=self.genTuple(CalculateSBFL.spectra,tmp)
        sus_value={}
        for (k,v) in remainTuples:
            sus_value[k]=self.calculate(v)
        self.suspicious_value_remain[cbfl.version]=sus_value

    def calculate(self,tuple):
        wong=Wong2(tuple)
        op2=Op2(tuple)
        jaccard=Jaccard(tuple)
        ochiai=Ochiai(tuple)
        taran=Tarantula(tuple)
        ochiai2=Ochiai2(tuple)
        formulas={}
        formulas["Wong2"]=wong
        formulas["Op2"]=op2
        formulas["Jaccard"]=jaccard
        formulas["Ochiai"]=ochiai
        formulas["Tarantula"]=taran
        formulas["Ochiai2"]=ochiai2

        results={}
        for (key,val) in formulas.items():
            results[key]=val.calculate()
        return results
