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
    matrix={}
    spectra={}
    suspicious_value={}
    test_case_pof={}
    pof_tuple={}

    def load(self,url_m,url_s):
        matrix_file=open(url_m,'r')
        spectra_file=open(url_s,'r')
        for (lineNo,line) in enumerate(spectra_file):
            self.spectra[lineNo]=line

        for (case,line) in enumerate(matrix_file):
            pass_fail_info=line.split(' ')
            self.test_case_pof[case]=pass_fail_info[-1]
            self.matrix=pass_fail_info[0:-1]

        for key in self.spectra.keys:
            self.pof_tuple[key]=[0,0,0,0] #aef,aep,anf,anp
            for ts_key in self.test_case_pof.keys:
                if self.test_case_pof.keys[ts_key]=='+':
                    if self.spectra[key]=='0':
                        self.pof_tuple[key][3]+=1
                    else:
                        self.pof_tuple[key][1]+=1
                else:
                    if self.spectra[key]=='0':
                        self.pof_tuple[key][2]+=1
                    else:
                        self.pof_tuple[key][0]+=1

    def diffTestSuite(self,):
        print ""
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