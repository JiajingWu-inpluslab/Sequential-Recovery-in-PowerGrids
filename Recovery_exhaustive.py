# -*- coding: utf-8 -*-
import numpy as np
from Power_Failure import Power_Failure
from Graph import Power_Graph
from Grid_Recovery import Grid_Recovery
from SAG import SAG
import copy
import random
import os
import networkx as nx
import matplotlib.pyplot as plt
from pypower.case14 import case14
from pypower.case57 import case57
from pypower.case30 import case30
from pypower.case39 import case39
from pypower.case118 import case118
from pypower.case300 import case300
from pypower.case24_ieee_rts import case24_ieee_rts
import Recovery_SAG




class Recovery_exhaustive(object):
    def __init__(self, steady_list, ini_graph, isolate_list = None):
        self.steady_list = steady_list
        self.ini_graph = ini_graph
        self.isolate_list = isolate_list





    def recovery_exhaustive(self, num):
        seq_dic = {}
        seq_list = []
        gr = Grid_Recovery(self.steady_list, self.ini_graph, None)
        candidate_bus_id = gr.connect_bus_list(self.steady_list)
        for bus in candidate_bus_id:
            tmp_list = self.dfs(bus, candidate_bus_id, num, [], [])
            seq_list.extend(tmp_list)

        for seq in seq_list:
            steady_list = copy.deepcopy(self.steady_list)
            grs = Grid_Recovery(steady_list, self.ini_graph, None)
            if num == 1:
                grs.recover_with_bus(seq[0])
                res_per = grs.cal_residual_power()
            else:
                res_per = grs.recover_with_sequence(seq)
            seq_dic[tuple(seq)] = res_per

        return seq_dic


    def dfs(self, current, candidates, num, seq, results):
        seq.append(current)
        if len(seq) == num:
            new_seq = copy.deepcopy(seq)
            seq.remove(current)
            results.append(new_seq)
            return results

        for bus in candidates:
            if bus not in seq:
                self.dfs(bus, candidates, num, seq, results)

        seq.remove(current)
        return results



def save_recovery_result():
    G0 = case24_ieee_rts()
    G1 = case39()
    G2 = case57()
    G3 = case118()
    G4 = Power_Graph.case_preprocess(case300())
    G = G2

    round = 5
    delete_num = 15
    ramp_rate = 0.3
    seq_len = 5

    path = 'exhaustive/case' + str(len(G['bus']))
    if os.path.exists(path) == False:
        os.mkdir(path)
    file_name = path + '/case' + str(len(G['bus'])) + '_exh2'  + '.txt'
    new_file = open(file_name, 'w')
    new_file.write('ramp_rate = ' + str(ramp_rate) + '\n')
    new_file.write('length of recovery seq ' + str(seq_len) + '\n')

    g = Power_Graph()
    g.init_by_case(G)
    g.set_ramp_rate(ramp_rate)
    delete_list = []
    while len(delete_list) != delete_num:
        ran_num = random.randint(1, len(G['bus']))
        if ran_num not in delete_list:
            delete_list.append(ran_num)

    #delete_list =  [66, 289, 298, 255, 72, 87, 263, 290, 83, 167, 241, 13, 225, 243, 232, 34, 147, 269, 132, 249, 122, 2, 37, 127, 94, 199, 202, 76, 156, 67, 131, 248, 188, 238, 15, 84, 44, 8, 220, 189, 206, 162, 169, 107, 17, 282, 164, 198, 115, 261]
    #delete_list = [44, 54, 11, 3, 6, 28, 2, 15, 30, 9]
    new_file.write('delete length '+ str(len(delete_list)) + '\n')
    new_file.write('delete list ' + str(delete_list) + '\n')

    for item in delete_list:
        g.delete_bus(item)
    cf = Power_Failure(g)
    for item in delete_list:
        cf.failed_bus_id.append(item)

    cf.failure_process()

    new_file.write('num of failed bus '+ str(len(cf.failed_bus_id)) + '\n')
    new_file.write('failed bus ' + str(cf.failed_bus_id) + '\n')
    steady_bus_num = 0
    steady_branch_num = 0
    for graph in cf.steady_list:
        steady_bus_num += len(graph.bus_id)
        steady_branch_num += len(graph.branch)
    new_file.write('num of steady bus ' + str(steady_bus_num) + '\n')
    new_file.write('num of steady branch ' + str(steady_branch_num) + '\n\n')


    ini_g = Power_Graph()
    ini_g.init_by_case(G)

    gr = Grid_Recovery(cf.steady_list, ini_g)
    candidate_num = len(gr.connect_bus_list(cf.steady_list))
    new_file.write('num of failed bus which can be recovered ' + str(candidate_num) + '\n')
    ini_residual_per = gr.cal_residual_power()
    new_file.write('residual power before recovery ' + str(ini_residual_per) + '\n\n')
    R_srg = Recovery_SAG.Recovery_SAG(cf.steady_list, ini_g)
    R_srg.initialize_param(44, 16, round)
    candidate_P_set = R_srg.cal_candidate_set()
    sorted_list = sorted(candidate_P_set.items(), key=lambda item: item[1], reverse=True)
    new_file.write('candidate P set '+ '\n')
    for item in sorted_list:
        new_file.write(str(item[0]) + ' ' + str(item[1]) + '\n')
    new_file.write('\n')


    R_ex = Recovery_exhaustive(cf.steady_list, ini_g)

    for num in range(1, seq_len+1):
        seq_dic = R_ex.recovery_exhaustive(num)
        sorted_list = sorted(seq_dic.items(), key=lambda item: item[1], reverse=True)
        new_file.write('exhaustive search recovery sequence length: ' + str(num) +'\n')
        for item in sorted_list:
            new_file.write(str(item[0]) + ' ' + str(item[1]) + '\n')

        new_file.write('\n')

    new_file.close()


if __name__ == '__main__':
    save_recovery_result()