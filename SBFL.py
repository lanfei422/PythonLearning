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

getcontext().prec = 6


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
        susp_score = Decimal(self.aef) / Decimal(self.aef + self.aep + self.anf)
        return susp_score


class Ochiai(Formula):
    def calculate(self):
        susp_score = Decimal(self.aef) / Decimal(math.sqrt((self.aef + self.anf) * (self.aef + self.aep)))
        return susp_score


class Tarantula(Formula):
    def calculate(self):
        fz = Decimal(self.aef) / Decimal(self.aef + self.anf)
        fm = fz + Decimal(self.aep) / Decimal(self.aep + self.anp)
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
                tmp_dict[lineNo] = spectra
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
        print "----generate tuples----"
        tuples = {}
        for key in self.spectra.keys():
            tuples[key] = [0, 0, 0, 0]  # aef,aep,anf,anp
            for ts_key in self.caseInfo.keys():
                if self.caseInfo[ts_key].split('\n')[0] == '+':
                    if self.matrix[ts_key][key] == '0':
                        tuples[key][3] += 1
                    else:
                        tuples[key][1] += 1
                else:
                    if self.matrix[ts_key] == '0':
                        tuples[key][2] += 1
                    else:
                        tuples[key][0] += 1
        return tuples

    def calculateSusScore(self, tuples):
        print "----calculate suspicious scores----"
        tmp_dict = {}
        for (key,tuple) in tuples.items():
            tmp_dict[key] = self.calculate(tuple)
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
        print "open file to save the result:" + str(url)
        #print self.susScore
        cur_parent=os.path.join(url,self.version)
        if not os.path.exists(cur_parent):
            os.makedirs(cur_parent)
        cur_path=os.path.join(cur_parent,"result_original.txt")
        with open(cur_path,"w+") as sFile:
            sFile.truncate()
        with open(cur_path, "a") as sFile:
            for (key, value) in self.susScore.items():
                outputStr = str(key)
                for (kf, vf) in value.items():
                    outputStr += "," + str(kf) + "#" + str(vf)
                sFile.write(outputStr + "\n")


###using threadpool, taskqueue, resultqueue to increase the processing velocity.
class WorkThread(threading.Thread):
    """后台线程，真正的工作线程，从请求队列(requestQueue)中获取TestProgram info，build TestProgram object并将执行后的结果添加到结果队列(resultQueue)"""

    def __init__(self, taskQueue, resultQueue, poll_timeout=5, **kwds):
        threading.Thread.__init__(self, **kwds)
        self.setDaemon(True)
        self._taskQueue = taskQueue
        self._resultQueue = resultQueue
        self._poll_timeout = poll_timeout
        self._dismiss = threading.Event()
        self.start()

    def run(self):
        '''每个线程尽可能多的执行work，所以采用loop，只要线程可用，并且tasktQueue有work未完成，则一直loop'''
        while True:
            if self._dismiss.is_set():
                break
            task = None
            try:
                task = self._taskQueue.get(True, self._poll_timeout)
                print "----get task----:" + str(task.version)
            except Queue.Empty:
                continue
            else:
                '''之所以在这里再次判断dimissed，是因为之前的timeout时间里，很有可能，该线程被dismiss掉了'''
                if self._dismiss.is_set():
                    self._taskQueue.put(task)
                    break
                print "----processing the data----"
                tp = TestProgram(task.version, task.spectra_url, task.matrix_url)
                tuples = tp.genTuples()
                tp.calculateSusScore(tuples)
                try:
                    self._resultQueue.put((task, tp))
                except:
                    '''异常处理'''
                    print "----processing data error"
                    task.exception = True
                    errorTP = TestProgram(task.version, task.spectra_url, task.matrix_url)
                    errorTP.susScore["error"] = sys.exc_info()
                    self._resultQueue.put((task, errorTP))

    def dismiss(self):
        '''设置一个标志，表示完成当前work之后，退出'''
        self._dismiss.set()


class ThreadPool:
    def __init__(self, num_workers, t_size=0, r_size=0, poll_timeout=5):
        self._taskQueue = Queue.Queue(t_size)
        self._resultQueue = Queue.Queue(r_size)
        self.workers = []
        self.dismissedWorkers = []
        self.workTasks = {}
        self.createWorkers(num_workers, poll_timeout)

    def createWorkers(self, num_workers, poll_timeout=5):
        for i in range(num_workers):
            self.workers.append(WorkThread(self._taskQueue, self._resultQueue, poll_timeout=poll_timeout))

    def dismissWorkers(self, num_workers, do_join=False):
        dismiss_list = []
        for i in range(min(num_workers, len(self.workers))):
            worker = self.workers.pop()
            worker.dismiss()
            dismiss_list.append(worker)
        if do_join:
            for worker in dismiss_list:
                worker.join()
        else:
            self.dismissedWorkers.extend(dismiss_list)

    def joinAllDismissedWorkers(self):
        '''join 所有停用的thread'''
        # print len(self.dismissedWorkers)
        for worker in self.dismissedWorkers:
            worker.join()
        self.dismissedWorkers = []

    def putTask(self, task, block=True, timeout=5):
        print "----put task----"
        assert isinstance(task, Task)
        '''当queue满了，也就是容量达到了前面设定的q_size,它将一直阻塞，直到有空余位置，或是timeout'''
        self._taskQueue.put(task, block, timeout)
        self.workTasks[task.version] = task

    def poll(self, save_url, block=False):
        print "----poll----"
        while True:
            if not self.workTasks:
                raise NoResultsPending
            elif block and not self.workers:
                raise NoWorkersAvailable
            try:
                '''默认只要resultQueue有值，则取出，否则一直block'''
                task, result = self._resultQueue.get(block=block)
                result.saveToFile(save_url)
                return (task,result)
            except Queue.Empty:
                break

    def wait(self):
        while True:
            try:
                self.poll(True)
            except NoResultsPending:
                break

    def workersize(self):
        return len(self.workers)

    def stop(self):
        '''join 所有的thread,确保所有的线程都执行完毕'''
        self.dismissWorkers(self.workersize(), True)
        self.joinAllDismissedWorkers()


class TaskProducer:
    def __init__(self, url, threadPool):
        self.url = url
        self.threadPool = threadPool

    def genTask(self, spectra_name, matrix_name):
        counter=0
        print "----generate task----"
        for parent, dirnames, filenames in os.walk(self.url):
            for dirname in dirnames:
                print "task's url is " + str(os.path.join(parent, dirname, spectra_name)) + "\n"
                task = Task(dirname, os.path.join(parent, dirname, spectra_name),
                            os.path.join(parent, dirname, matrix_name))
                self.threadPool.putTask(task)
                counter+=1
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

def finalStep(result_queue):
    for (kr,vr) in result_queue:
        cur=vr.susScore
        for (kc,vc) in cur.items():
            for (kf,vf) in vc.items():
                if kc in vr.bias.keys():
                    cur[kc][kf]=vf-vr.bias[kc][kf]


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
    if len(sys.argv)!=5:
        print "input arguments number is error.example python SBFL.py project_path tmp_result_path result_path"
    else:
        project_path=sys.argv[2]
        tmp_result_path=sys.argv[3]
        result_path=sys.argv[4]


        tpool = ThreadPool(9, 200, 300, 5)
        tproducer = TaskProducer(project_path, tpool)
        pd_counter=tproducer.genTask('spectra', 'matrix')

        sbfl_result=[]

        while True:
            if len(sbfl_result)==pd_counter:
                break
            try:
                time.sleep(0.5)
                sbfl_result.append(tpool.poll(tmp_result_path,True))
            except NoResultsPending:
                print "no pending results"
                break

        sbfl_result.sort(lambda x,y:cmp(x[0].version,y[0].version))
        calculateY(sbfl_result,pd_counter)
        finalStep(sbfl_result)
        writeResult2File(sbfl_result,result_path)
        tpool.stop()
        print "Stop"
