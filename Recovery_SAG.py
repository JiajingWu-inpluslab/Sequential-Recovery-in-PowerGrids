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


class Recovery_SAG(object):
    def __init__(self, steady_list, ini_graph, isolate_list = None):
        self.candidate_num = 0   #P
        self.selected_num = 0    #R
        self.round = 0
        self.RRC_set = {}
        self.candidate_set = {}
        self.ini_graph = ini_graph
        self.steady_list = steady_list
        self.SAG = SAG()
        self.isolate_list = isolate_list


    def initialize_param(self, P, R, round):
        self.candidate_num = P
        self.selected_num = R
        self.round = round


    def cal_candidate_set(self):
        bus_recovery_dic = {}
        gr = Grid_Recovery(self.steady_list, self.ini_graph, self.isolate_list)
        bus_recovery_id = gr.connect_bus_list(self.steady_list)
        for bus in bus_recovery_id:
            steady_list = copy.deepcopy(self.steady_list)
            if self.isolate_list != None:
                isolate_list = copy.deepcopy(self.isolate_list)
            else:
                isolate_list = None
            gr = Grid_Recovery(steady_list, self.ini_graph, isolate_list)
            if isolate_list != None:
                gr.recover_with_bus_2(bus)
            else:
                gr.recover_with_bus(bus)
            residual_per = gr.cal_residual_power()
            bus_recovery_dic[bus] = residual_per

        sorted_list = sorted(bus_recovery_dic.items(), key = lambda item: item[1], reverse = True)

        for item in sorted_list:
            #print item   #test
            self.candidate_set[item[0]] = item[1]
            if len(self.candidate_set) == self.candidate_num:
                break

        return self.candidate_set


    def cal_RRC_set(self):
        self.cal_candidate_set()
        bus_list_dic = {}
        sorted_list = sorted(self.candidate_set.items(), key=lambda item: item[1], reverse=True)
        for item in sorted_list:
            tmp_list = (item[0],)
            bus_list_dic[tmp_list] = item[1]
            if len(bus_list_dic) == self.selected_num:
                break
        self.RRC_set['RRC_1'] = bus_list_dic

        current_round = 1
        while current_round < self.round:
            current_dic = {}
            key = 'RRC_' + str(current_round)
            bus_list_dic = self.RRC_set[key]
            for bus_list in bus_list_dic.items():
                for candidate in self.candidate_set.items():

                    if candidate[0] in bus_list[0]:
                        continue

                    seq = []
                    seq.extend(list(bus_list[0]))
                    seq.append(candidate[0])
                    steady_list = copy.deepcopy(self.steady_list)
                    if self.isolate_list != None:
                        isolate_list = copy.deepcopy(self.isolate_list)
                        pattern = 2
                    else:
                        isolate_list = None
                        pattern = 1
                    gr = Grid_Recovery(steady_list, self.ini_graph, isolate_list)
                    residual_per = gr.recover_with_sequence(seq, pattern)
                    seq = tuple(seq)
                    current_dic[seq] = residual_per

            sorted_list = sorted(current_dic.items(), key = lambda item: item[1], reverse = True)
            selected_list_dic = {}
            for item in sorted_list:
                selected_list_dic[item[0]] = item[1]
                if len(selected_list_dic) == self.selected_num:
                    break

            current_round += 1
            key = 'RRC_' + str(current_round)
            self.RRC_set[key] = selected_list_dic

        return self.RRC_set

    def construct_SAG(self):
        for item in self.RRC_set.items():
            if item[0] == 'RRC_1':
                continue
            bus_list_dic = item[1]
            r = int(item[0][4:])
            weight = 2.0 / (r*(r-1))
            for seq in bus_list_dic.keys():
                for i in range(len(seq)):
                    for j in range(i+1, len(seq)):
                        edge = (seq[i], seq[j])
                        self.SAG.add_node(seq[i])
                        self.SAG.add_node(seq[j])
                        self.SAG.add_edge(edge, weight)

        #self.SAG.draw_graph()


    def cal_SAG_recovery_seq(self, num):
        max_EOF = 0.0
        recovery_seq = []
        for source in self.SAG.node_list:
            #print 'source', source    #test
            print source,'run into dfs'      #test
            Paths = self.SAG.dfs_from(source, num-1, [], [])
            print source,'run out of dfs', len(Paths)     #test
            for path in Paths:
                current_EOF = 0.0
                for i in range(len(path)-1):
                    edge = (path[i], path[i+1])
                    current_EOF += self.SAG.edge_dic[edge]

                if current_EOF > max_EOF:
                    max_EOF = current_EOF
                    recovery_seq = path
                    #print 'seq', recovery_seq, current_EOF
                #print 'path', path, current_EOF


        return recovery_seq


    def cal_SAG_recovery_seq_2(self, num):
        max_EOF = 0.0
        recovery_seq = []
        for source in self.SAG.node_list:
            print source, 'run into dfs'
            path = self.SAG.max_path_dfs_from(source, num-1, [], {})
            print source, 'run out of dfs', path
            if len(path) == 0:
                continue
            item = path.popitem()
            if item[1] > max_EOF:
                max_EOF = item[1]
                recovery_seq = list(item[0])

        return recovery_seq


def save_recovery_result():
    G0 = case24_ieee_rts()
    G1 = case39()
    G2 = case57()
    G3 = case118()
    G4 = Power_Graph.case_preprocess(case300())
    G_list = [G0, G1, G2, G3, G4]
    G = G2

    P = 16
    R = 10
    round = 9
    delete_num = 15
    iter_times = 20
    ramp_rate = 0.3
    seq_len = 9
    random_rep_num = 50

    for i in range(1, iter_times):

        path = 'test/case' + str(len(G['bus'])) + '_9'
        if os.path.exists(path) == False:
            os.mkdir(path)
        file_name = path + '/case' + str(len(G['bus'])) + '_setup_' + str(i+1)  + '.txt'
        new_file = open(file_name, 'w')
        new_file.write('ramp_rate = ' + str(ramp_rate) + '\n')
        new_file.write('P=' + str(P) + ' , ' + 'R=' + str(R) + ' , ' + 'round=' + str(round) + '\n')
        new_file.write('length of recovery seq ' + str(seq_len) + '\n')

        g = Power_Graph()
        g.init_by_case(G)
        g.set_ramp_rate(ramp_rate)
        delete_list = []
        while len(delete_list) != delete_num:
            ran_num = random.randint(1, len(G['bus']))
            if ran_num not in delete_list:
                delete_list.append(ran_num)
        #delete_list=[66, 289, 298, 255, 72, 87, 263, 290, 83, 167, 241, 13, 225, 243, 232, 34, 147, 269, 132, 249, 122, 2, 37, 127, 94, 199, 202, 76, 156, 67, 131, 248, 188, 238, 15, 84, 44, 8, 220, 189, 206, 162, 169, 107, 17, 282, 164, 198, 115, 261]
        #delete_list=[
            #70, 4, 289, 110, 186, 6, 196, 192, 129, 164, 281, 252, 156, 7, 172, 100, 183, 9, 135, 51, 157, 96, 267, 95, 137, 233, 167, 87, 12, 211, 291, 248, 176, 255, 1, 198, 212, 163, 19, 98, 104, 57, 99, 29, 78, 141, 73, 53, 249, 147]
        #delete_list=[154, 197, 4, 90, 100, 195, 244, 27, 170, 229, 221, 33, 151, 110, 118, 49, 66, 248, 127, 172, 64, 224, 277, 265, 211, 256, 116, 99, 155, 89, 198, 133, 62, 214, 55, 267, 159, 25, 150, 95, 193, 129, 136, 278, 111, 294, 157, 185, 208, 22, 177, 51, 96, 81, 230, 79, 67, 184, 153, 141]
        #delete_list =  [277, 213, 101, 82, 36, 161, 140, 51, 171, 114, 23, 88, 198, 236, 137, 242, 194, 64, 287, 156, 125, 206, 80, 185, 190, 59, 286, 258, 69, 192, 172, 166, 167, 115, 181, 243, 224, 261, 126, 148, 251, 150, 179, 105, 189, 15, 239, 297, 207, 25]
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
        R_SAG = Recovery_SAG(cf.steady_list, ini_g)
        R_SAG.initialize_param(P, R, round)
        candidate_set = R_SAG.cal_candidate_set()
        if len(candidate_set) < seq_len + 1:
            continue

        RRC_set = R_SAG.cal_RRC_set()
        RRC_seq = {}
        RRC_residual_per = {}
        for i in range(1, seq_len+1):
            RRC_residual_per[i] = 0.0
        for item in RRC_set.items():
            # print item
            new_file.write(str(item[0]) + '\n')
            current_set = item[1]
            sorted_list = sorted(current_set.items(), key = lambda item: item[1], reverse = True)
            for k, v in sorted_list:
                new_file.write(str(k) + ' ' + str(v) +'\n')
                if v > RRC_residual_per[len(k)]:
                    RRC_seq[len(k)] = k
                    RRC_residual_per[len(k)] = v
        new_file.write('\n')

        R_SAG.construct_SAG()
        new_file.write('node num of SRG ' + str(len(R_SAG.SAG.node_list)) + '\n\n')

        for current in range(2, seq_len+1):
            SAG_seq = R_SAG.cal_SAG_recovery_seq_2(current)
            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            ini_residual_per = gr.cal_residual_power()
            SRG_residual_per = gr.recover_with_sequence(SAG_seq)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            degree_residual_per, degree_seq = gr.recovery_degree_2(current)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            low_degree_residual_per, low_degree_seq = gr.recovery_low_degree_2(current)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            load_residual_per, load_seq = gr.recovery_load_2(current)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            low_load_residual_per, low_load_seq = gr.recovery_low_load_2(current)

            sum = 0.0
            for i in range(0, random_rep_num):
                steady_list = copy.deepcopy(cf.steady_list)
                gr = Grid_Recovery(steady_list, ini_g)
                residual_per, seq = gr.recovery_random_2(current)
                sum += residual_per
            aver_residual_per = sum / random_rep_num

            new_file.write('current length of seq: ' + str(current) + '\n')
            new_file.write('SRG recovery seq ' + str(SAG_seq) +'\n')
            new_file.write('RRC recovery seq ' + str(RRC_seq[current]) +'\n')
            new_file.write('high degree based recovery seq ' + str(degree_seq) + '\n')
            new_file.write('low degree based recovery seq ' + str(low_degree_seq) + '\n')
            new_file.write('high load based recovery seq ' +  str(load_seq) + '\n')
            new_file.write('low load based recovery seq ' +  str(low_load_seq) + '\n')
            new_file.write('\n')

            new_file.write('residual percent of power before recovery '+ str(ini_residual_per) + '\n')
            new_file.write('residual percent of power after SRG recovery ' + str(SRG_residual_per) + '\n')
            new_file.write('residual percent of power after RRC recovery ' + str(RRC_residual_per[current]) + '\n')
            new_file.write('residual percent of power after high degree based recovery ' + str(degree_residual_per) + '\n')
            new_file.write('residual percent of power after low degree based recovery ' + str(low_degree_residual_per) + '\n')
            new_file.write('residual percent of power after high load based recovery ' + str(load_residual_per) + '\n')
            new_file.write('residual percent of power after low load based recovery ' + str(low_load_residual_per) + '\n')
            new_file.write('average residual percent of power after random based recovery ' + str(aver_residual_per) + '\n')
            new_file.write('\n\n')

        new_file.close()



def save_recovery_result_2():
    G0 = case24_ieee_rts()
    G1 = case39()
    G2 = case57()
    G3 = case118()
    G4 = Power_Graph.case_preprocess(case300())
    G_list = [G0, G1, G2, G3, G4]
    G = G4

    P = 30
    R = 16
    round = 9
    delete_num = 15
    #iter_times = 11
    ramp_rate = 0.3
    seq_len = 9
    random_rep_num = 50
    ramp_arr = np.arange(0.1, 1.1, 0.1)
    P_arr = np.arange(10, 32, 2)
    R_arr = np.arange(2, 32, 2)

    for p in P_arr:

        path = 'recovery_result4/case' + str(len(G['bus'])) + '_0.3'
        if os.path.exists(path) == False:
            os.mkdir(path)
        file_name = path + '/case' + str(len(G['bus'])) + '_setup_' + str(p)  + '.txt'
        new_file = open(file_name, 'w')
        new_file.write('ramp_rate = ' + str(ramp_rate) + '\n')
        new_file.write('P=' + str(p) + ' , ' + 'R=' + str(R) + ' , ' + 'round=' + str(round) + '\n')
        new_file.write('length of recovery seq ' + str(seq_len) + '\n')

        g = Power_Graph()
        g.init_by_case(G)
        g.set_ramp_rate(ramp_rate)
        delete_list = []
        while len(delete_list) != delete_num:
            ran_num = random.randint(1, len(G['bus']))
            if ran_num not in delete_list:
                delete_list.append(ran_num)
        delete_list=[66, 289, 298, 255, 72, 87, 263, 290, 83, 167, 241, 13, 225, 243, 232, 34, 147, 269, 132, 249, 122, 2, 37, 127, 94, 199, 202, 76, 156, 67, 131, 248, 188, 238, 15, 84, 44, 8, 220, 189, 206, 162, 169, 107, 17, 282, 164, 198, 115, 261]
        #delete_list=[192, 27, 15, 153, 198, 189, 171, 33, 256, 265, 25, 218, 284, 6, 261, 155, 131, 260, 97, 93, 55, 95, 124, 69, 37, 34, 94, 201, 12, 144, 1, 254, 193, 83, 59, 230, 289, 9, 200, 264, 277, 246, 143, 179, 100, 232, 233, 91, 151, 170]
        #delete_list=[105, 49, 69, 110, 28, 62, 31, 41, 96, 15, 108, 67, 63, 115, 79, 101, 83, 76, 61, 75, 45, 12, 32, 113, 98, 111, 91, 95, 68, 9]
        #delete_list = [74, 45, 51, 1, 106, 3, 82, 67, 90, 114, 81, 30, 7, 17, 79, 103, 95, 46, 115, 118, 40, 117, 96, 116, 88, 27, 57, 110, 28, 21]
        #delete_list=[25, 17, 8, 32, 37, 24, 9, 28, 47, 15]
        #delete_list = [37, 18, 31, 20, 1, 35, 15, 57, 54, 2, 17, 6, 51, 3, 55]
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
        R_SAG = Recovery_SAG(cf.steady_list, ini_g)
        R_SAG.initialize_param(p, R, round)
        candidate_set = R_SAG.cal_candidate_set()
        RRC_set = R_SAG.cal_RRC_set()
        RRC_seq = {}
        RRC_residual_per = {}
        for i in range(1, seq_len+1):
            RRC_residual_per[i] = 0.0
        for item in RRC_set.items():
            # print item
            new_file.write(str(item[0]) + '\n')
            current_set = item[1]
            sorted_list = sorted(current_set.items(), key = lambda item: item[1], reverse = True)
            for k, v in sorted_list:
                new_file.write(str(k) + ' ' + str(v) +'\n')
                if v > RRC_residual_per[len(k)]:
                    RRC_seq[len(k)] = k
                    RRC_residual_per[len(k)] = v
        new_file.write('\n')

        R_SAG.construct_SAG()
        new_file.write('node num of SRG ' + str(len(R_SAG.SAG.node_list)) + '\n\n')

        for current in range(2, seq_len+1):
            SAG_seq = R_SAG.cal_SAG_recovery_seq_2(current)
            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            ini_residual_per = gr.cal_residual_power()
            SRG_residual_per = gr.recover_with_sequence(SAG_seq)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            degree_residual_per, degree_seq = gr.recovery_degree_2(current)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            low_degree_residual_per, low_degree_seq = gr.recovery_low_degree_2(current)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            load_residual_per, load_seq = gr.recovery_load_2(current)

            steady_list = copy.deepcopy(cf.steady_list)
            gr = Grid_Recovery(steady_list, ini_g)
            low_load_residual_per, low_load_seq = gr.recovery_low_load_2(current)

            sum = 0.0
            for i in range(0, random_rep_num):
                steady_list = copy.deepcopy(cf.steady_list)
                gr = Grid_Recovery(steady_list, ini_g)
                residual_per, seq = gr.recovery_random_2(current)
                sum += residual_per
            aver_residual_per = sum / random_rep_num

            new_file.write('current length of seq: ' + str(current) + '\n')
            new_file.write('SRG recovery seq ' + str(SAG_seq) +'\n')
            new_file.write('RRC recovery seq ' + str(RRC_seq[current]) +'\n')
            new_file.write('high degree based recovery seq ' + str(degree_seq) + '\n')
            new_file.write('low degree based recovery seq ' + str(low_degree_seq) + '\n')
            new_file.write('high load based recovery seq ' +  str(load_seq) + '\n')
            new_file.write('low load based recovery seq ' +  str(low_load_seq) + '\n')
            new_file.write('\n')

            new_file.write('residual percent of power before recovery '+ str(ini_residual_per) + '\n')
            new_file.write('residual percent of power after SRG recovery ' + str(SRG_residual_per) + '\n')
            new_file.write('residual percent of power after RRC recovery ' + str(RRC_residual_per[current]) + '\n')
            new_file.write('residual percent of power after high degree based recovery ' + str(degree_residual_per) + '\n')
            new_file.write('residual percent of power after low degree based recovery ' + str(low_degree_residual_per) + '\n')
            new_file.write('residual percent of power after high load based recovery ' + str(load_residual_per) + '\n')
            new_file.write('residual percent of power after low load based recovery ' + str(low_load_residual_per) + '\n')
            new_file.write('average residual percent of power after random based recovery ' + str(aver_residual_per) + '\n')
            new_file.write('\n\n')

        new_file.close()



if __name__ == '__main__':
    save_recovery_result_2()
    exit()
    #G = case24_ieee_rts()
    #G = case39()
    #G = case57()
    #G = case118()

    G = Power_Graph.case_preprocess(case300())
    g = Power_Graph()
    g.init_by_case(G)
    g.set_ramp_rate(0.3)

    g.draw_P_graph()
    print 'draw initial graph'

    #num = 80
    delete_list = [30, 279, 264, 138, 143, 9, 56, 202, 225, 90, 140, 256, 173, 247, 185, 60, 144, 33, 171, 91, 63, 97, 74, 122, 258, 134, 166, 62, 51, 54, 48, 165, 43, 36, 42, 101, 178, 257, 170, 286, 148, 119, 208, 283, 260, 273, 81, 151, 44, 167, 133, 154, 244, 92, 201, 194, 16, 251, 252, 175]
    '''
    while len(delete_list) != num:
        ran_num = random.randint(1, 300)
        if ran_num not in delete_list:
            delete_list.append(ran_num)
    '''
    for item in delete_list:
        g.delete_bus(item)


    cf = Power_Failure(g)
    for item in delete_list:
        cf.failed_bus_id.append(item)

    cf.failure_process()
    for graph in cf.steady_list:
        print 'steady graph', graph.bus_id
    print 'failed bus', cf.failed_bus_id
    Power_Graph.draw_graph_list(cf.steady_list)


    ini_g = Power_Graph()
    ini_g.init_by_case(G)
    R_SAG = Recovery_SAG(cf.steady_list, ini_g)
    R_SAG.initialize_param(P = 30, R = 16, round = 15)
    candidate_set = R_SAG.cal_candidate_set()
    #print 'candidate set'
    #for k, v in candidate_set.items():
    #    print k, v

    RRC_set = R_SAG.cal_RRC_set()
    for item in RRC_set.items():
        #print item
        print item[0]
        current_set = item[1]
        for k, v in current_set.items():
            print k, v

    R_SAG.construct_SAG()
    R_SAG.SAG.save_graph('case300_SRG.csv')
    SAG_seq = R_SAG.cal_SAG_recovery_seq(15)
    print 'SAG recovery seq', SAG_seq

    steady_list = copy.deepcopy(cf.steady_list)
    gr = Grid_Recovery(steady_list, ini_g)
    residual_per = gr.cal_residual_power()
    print 'residual percent of power before recovery', residual_per
    residual_per = gr.recover_with_sequence(SAG_seq)
    print 'residual percent of power after SRG recovery', residual_per

    '''
    steady_list = copy.deepcopy(cf.steady_list)
    gr = Grid_Recovery(steady_list, ini_g)
    residual_per, seq = gr.recovery_degree_2(5)
    print 'residual percent of power after degree based recovery', residual_per

    steady_list = copy.deepcopy(cf.steady_list)
    gr = Grid_Recovery(steady_list, ini_g)
    residual_per, seq = gr.recovery_load_2(5)
    print 'residual percent of power after load based recovery', residual_per

    print 'delete list', delete_list
    '''

    #save_recovery_result()





