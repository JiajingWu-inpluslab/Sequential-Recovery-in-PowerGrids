# -*- coding: utf-8 -*-
import numpy as np
from Power_Failure import Power_Failure
from Graph import Power_Graph
import random
import math
import  networkx as nx
import matplotlib.pyplot as plt
from pypower.case14 import case14
from pypower.case57 import case57
from pypower.case30 import case30
from pypower.case39 import case39
from pypower.case118 import case118
from pypower.case24_ieee_rts import case24_ieee_rts
from pypower.rundcpf import rundcpf
from time import clock
import copy

'''
继承Power_Failure类
'''
class Grid_Recovery(Power_Failure):
    '''
    graph_list: 电网经过级联失效后的一个或多个子网络
    ini_graph: 未经过失效的原始电网
    '''
    def __init__(self, graph_list, ini_graph, isolate_list = None):
        super(Grid_Recovery, self).__init__(ini_graph)
        self.ini_bus_dic = {}    #原始电网bus数据
        self.ini_bus_id = []     #原始电网bus id
        self.ini_m_bus = 0       #原始电网bus数目
        self.ini_gen_dic = {}      #原始电网generator数据
        self.ini_gen_id = []       #原始电网generator id
        self.ini_neigh_id = {}     #原始电网的节点邻居id
        self.ini_branch_dic = {}      #原始电网branch数据
        self.ini_load = {}             #原始电网节点负荷
        self.ini_degree = {}           #原始电网节点度
        self.failure_list = []         #在recovery过程中候选失效的子网络
        self.residual_percent = 0.0
        self.steady_list = graph_list      #在recovery中稳定状态的子网络
        if isolate_list != None:
            self.isolate_list = isolate_list
        self.init_by_ini_graph(ini_graph)


    '''
    根据原始电网数据初始化Grid_Recovery对象的参数
    '''
    def init_by_ini_graph(self, g):
        for item in g.bus:
            self.ini_bus_dic[int(item[0])] = item
        self.ini_bus_id = g.bus_id
        self.ini_m_bus = g.m_Bus

        for item in g.gens:
            self.ini_gen_dic[int(item[0])] = item
        self.ini_gen_id = g.gen_id

        for item in g.branch:
            tp = (int(item[0]), int(item[1]))
            self.ini_branch_dic[tp] = item

        for item in self.ini_branch_dic.keys():
            fr = item[0]
            to = item[1]
            if fr in self.ini_neigh_id.keys():
                self.ini_neigh_id[fr].append(to)
            else:
                self.ini_neigh_id[fr] = [to]
            if to in self.ini_neigh_id.keys():
                self.ini_neigh_id[to].append(fr)
            else:
                self.ini_neigh_id[to] = [fr]

        for item in self.ini_bus_id:
            flag = 0
            for graph in self.steady_list:
                if item in graph.bus_id:
                    flag = 1
                    break
            if flag == 0:
                self.failed_bus_id.append(item)

        for item in self.ini_branch_dic.keys():
            flag = 0
            for graph in self.steady_list:
                if item in graph.edge_list:
                    flag = 1
                    break
            if flag == 0:
                self.failed_branch.append(item)

        self.ini_load = g.load_bus
        self.ini_degree = g.degree


    def set_isolate_list(self, graph_list):
        self.isolate_list = graph_list


    def cal_residual_power(self):
        current_power = 0.0
        for graph in self.steady_list:
            for item in graph.load_bus.values():
                current_power += item

        self.residual_percent = current_power/self.total_power
        return self.residual_percent


    '''
    判断某个已经失效的节点fb_id在原始网络中是否与网络G有连边
    return:节点fb_id与网络G相连的节点列表
    '''
    def connect_to_graph(self, fb_id, G):
        neighbors = self.ini_neigh_id[fb_id]
        connected_bus = []
        for item in neighbors:
            if item in G.bus_id:
                connected_bus.append(item)
        return connected_bus

    '''
    根据原始网络数据，计算得到已失效的节点集failed_bus_id中，
    与子网络列表graph_list中的网络可以建立直接连边的节点集
    '''
    def connect_bus_list(self, graph_list):
        bus_list = []
        for item in self.failed_bus_id:
            neighbors =self.ini_neigh_id[item]
            flag = 0
            for graph in graph_list:
                for neigh in neighbors:
                    if neigh in graph.bus_id:
                        flag = 1
                        bus_list.append(item)
                        break
                if flag == 1:
                    break

        return bus_list


    def connect_branch_list(self, graph_list):
        branch_list = []
        for item in self.failed_branch:
            fr = item[0]
            to = item[1]
            for graph in graph_list:
                if fr in graph.bus_id or to in graph.bus_id:
                    branch_list.append((fr, to))
                    break

        return branch_list


    def connect_graph_list(self, fb_id, graph_list):
        candidate_graph_list = []
        for graph in graph_list:
            connected_bus = self.connect_to_graph(fb_id, graph)
            if len(connected_bus) > 0:
                candidate_graph_list.append(graph)

        return candidate_graph_list


    def connect_graph_list_2(self, branch, graph_list):
        candidate_graph_list = []
        fr = branch[0]
        to = branch[1]
        for graph in graph_list:
            if fr in graph.bus_id or to in graph.bus_id:
                candidate_graph_list.append(graph)

        return candidate_graph_list


    '''
    将子网络列表graph_list中的多个子网络，通过恢复已失效节点fb_id，
    并建立fb_id和多个子网络的连边，得到一个新的连通网络
    '''
    def merge_graph_by_bus(self, fb_id, graph_list):
        g = Power_Graph()

        g.bus_id.append(fb_id)
        g.bus = np.array([self.ini_bus_dic[fb_id]])
        if fb_id in self.ini_gen_id:
            g.gen_id.append(fb_id)
            g.gens = np.array([self.ini_gen_dic[fb_id]])
        for graph in graph_list:
            connected_bus = self.connect_to_graph(fb_id, graph)
            for neighbor in connected_bus:
                link = (fb_id, neighbor)
                if link not in self.ini_branch_dic.keys():
                    link = (neighbor, fb_id)
                if len(g.branch) > 0:
                    g.branch = np.append(g.branch, [self.ini_branch_dic[link]], axis=0)
                else:
                    g.branch = np.array([self.ini_branch_dic[link]])

        for graph in graph_list:
            g.bus_id.extend(graph.bus_id)
            g.bus = np.append(g.bus, graph.bus, axis=0)
            g.gen_id.extend(graph.gen_id)
            if len(g.gens) > 0:
                g.gens = np.append(g.gens, graph.gens, axis=0)
            else:
                g.gens = np.array([line for line in graph.gens])
            g.branch = np.append(g.branch, graph.branch, axis=0)

        g.m_Bus = self.ini_m_bus
        g.make_init()
        return g


    def merge_graph_by_branch(self, branch_list, graph_list_1, graph_list_2):
        g = Power_Graph()

        graph_list = []
        graph_list.extend(graph_list_1)
        graph_list.extend(graph_list_2)
        for graph in graph_list:
            g.bus_id.extend(graph.bus_id)
            if len(g.bus) > 0:
                g.bus = np.append(g.bus, graph.bus, axis = 0)
            else:
                g.bus = np.array([line for line in graph.bus])
            g.gen_id.extend(graph.gen_id)
            if len(g.gens) > 0:
                g.gens = np.append(g.gens, graph.gens, axis=0)
            else:
                g.gens = np.array([line for line in graph.gens])
            if len(g.branch) > 0:
                g.branch = np.append(g.branch, graph.branch, axis=0)
            else:
                g.branch = np.array([line for line in graph.branch])

        g.branch = np.append(g.branch, [self.ini_branch_dic[branch] for branch in branch_list], axis=0 )

        g.m_Bus = self.ini_m_bus
        g.make_init()
        return g


    '''
    恢复某个已经失效的节点fb_id
    '''
    def recover_with_bus(self, fb_id):
        graph_list = []
        graph_list = self.connect_graph_list(fb_id, self.steady_list)

        if len(graph_list) == 1:
            #print 'add new bus to existing steady graph', fb_id   #key test
            g = graph_list[0]
            bus_data = {}
            bus_data['bus'] = self.ini_bus_dic[fb_id]
            if fb_id in self.ini_gen_id:
                bus_data['gen'] = self.ini_gen_dic[fb_id]
            bus_data['branch'] = []
            connected_bus = self.connect_to_graph(fb_id, g)
            for neighbor in connected_bus:
                if (fb_id, neighbor) in self.ini_branch_dic.keys():
                    bus_data['branch'].append(self.ini_branch_dic[(fb_id, neighbor)])
                else:
                    bus_data['branch'].append(self.ini_branch_dic[(neighbor, fb_id)])
            g.add_bus(bus_data)
            self.failure_list.append(g)
        elif len(graph_list) > 1:
            print 'merge steady graphs by new bus', fb_id   #test
            new_graph = self.merge_graph_by_bus(fb_id, graph_list)
            self.failure_list.append(new_graph)
        else:
            print 'Bus:', fb_id, 'is not connected to steady graphs.'
            return

        for graph in graph_list:
            self.steady_list.remove(graph)

        self.failed_bus_id.remove(fb_id)

        self.failure_process()


    def recover_with_bus_2(self, fb_id):
        flag = 0
        isolate_graph_list = []
        for graph in self.isolate_list:
            if fb_id in graph.bus_id:
                flag = 1
                isolate_graph_list.append(graph)
                break

        if flag == 0:
            self.recover_with_bus(fb_id)
            return

        graph_list = []
        index = 0
        branch_list = []

        for graph in self.steady_list:
            connected_bus = self.connect_to_graph(fb_id, graph)
            if len(connected_bus) > 0:
                graph_list.append(graph)
                for bus in connected_bus:
                    if (fb_id, bus) in self.ini_branch_dic.keys():
                        branch_list.append((fb_id, bus))
                    else:
                        branch_list.append((bus, fb_id))

        if len(branch_list) > 0:
            print 'merge isolated graph and steady graphs by branch', fb_id
            new_graph = self.merge_graph_by_branch(branch_list, graph_list, isolate_graph_list)
            self.failure_list.append(new_graph)
        else:
            print 'Bus:', fb_id, 'is not connected to steady graphs.'
            return

        for graph in graph_list:
            self.steady_list.remove(graph)
        for graph in isolate_graph_list:
            self.isolate_list.remove(graph)

        self.failed_bus_id.remove(fb_id)
        '''
        for graph in self.failure_list:
            print 'testing...........', graph.bus_id
            print 'testing...........', graph.gen_id
            print 'testing...........', graph.edge_list
            print 'testing...........', graph.bus
            print 'testing...........', graph.gens
            print 'testing...........', graph.branch
        '''
        self.failure_process()


    def recover_with_branch(self, branch):
        graph_list = self.connect_graph_list_2(branch, self.steady_list)

        fr = branch[0]
        to = branch[1]
        bus_data = {}
        if len(graph_list) == 1:
            g = graph_list[0]
            if fr in g.bus_id and to in g.bus_id:
                branch_data = self.ini_branch_dic[(fr, to)]
                g.add_branch(branch_data)
            else:
                if fr in g.bus_id:
                    new_bus = to
                else:
                    new_bus = fr
                bus_data['bus'] = self.ini_bus_dic[new_bus]
                if new_bus in self.ini_gen_id:
                    bus_data['gen'] = self.ini_gen_dic[new_bus]
                bus_data['branch'] = []
                bus_data['branch'].append(self.ini_branch_dic[(fr, to)])
                g.add_bus(bus_data)
                #self.failed_bus_id.remove(new_bus)
            self.failure_list.append(g)
        elif len(graph_list) == 2:
            branch_list = []
            graph_list_1 = []
            graph_list_2 = []
            branch_list.append(branch)
            graph_list_1.append(graph_list[0])
            graph_list_2.append(graph_list[1])
            new_graph = self.merge_graph_by_branch(branch_list, graph_list_1, graph_list_2)
            self.failure_list.append(new_graph)
        else:
            print 'Branch:', branch, 'is not connected to steady graphs.'
            return

        for graph in graph_list:
            self.steady_list.remove(graph)
        self.failed_branch.remove(branch)
        self.failure_process()


    def recover_with_sequence(self, seq, pattern = 1):
        for item in seq:
            candidate_bus_id = self.connect_bus_list(self.steady_list)
            if item not in candidate_bus_id:
                continue
            if pattern == 1:
                self.recover_with_bus(item)
            elif pattern == 2:
                self.recover_with_bus_2(item)

        return self.cal_residual_power()


    '''
    使用度的策略对网络中的节点进行恢复
    '''
    def recovery_degree(self, num):
        seq = []
        while num > 0:
            candidate_bus_id = self.connect_bus_list(self.steady_list)
            degree_dic = {}
            for item in candidate_bus_id:
                degree_dic[item] = self.ini_degree[item]
            max_degree = 0
            candidate = 0
            for item in degree_dic.items():
                if item[1] > max_degree:
                    max_degree = item[1]
                    candidate = item[0]
            self.recover_with_bus(candidate)
            seq.append(candidate)
            num -= 1

        print 'degree based recovery seq', seq
        return self.cal_residual_power(), seq


    def recovery_degree_2(self, num):
        candidate_bus_id = self.connect_bus_list(self.steady_list)
        degree_dic = {}
        for item in candidate_bus_id:
            degree_dic[item] = self.ini_degree[item]

        sorted_list = sorted(degree_dic.items(), key = lambda item: item[1], reverse = True)
        seq = []
        for item in sorted_list:
            seq.append(item[0])
            if len(seq) == num:
                break

        print 'degree based recovery seq', seq
        return self.recover_with_sequence(seq), seq


    def recovery_low_degree_2(self, num):
        candidate_bus_id = self.connect_bus_list(self.steady_list)
        degree_dic = {}
        for item in candidate_bus_id:
            degree_dic[item] = self.ini_degree[item]

        sorted_list = sorted(degree_dic.items(), key = lambda item: item[1])
        seq = []
        for item in sorted_list:
            seq.append(item[0])
            if len(seq) == num:
                break

        print 'low degree based recovery seq', seq
        return self.recover_with_sequence(seq), seq


    '''
    使用负载的策略对网络中的节点进行恢复
    '''
    def recovery_load(self, num):
        seq = []
        while num > 0:
            candidate_bus_id = self.connect_bus_list(self.steady_list)
            load_dic = {}
            for item in candidate_bus_id:
                load_dic[item] = self.ini_load[item]
            max_load = 0
            candidate = 0
            for item in load_dic.items():
                if item[1] > max_load:
                    max_load = item[1]
                    candidate = item[0]
            self.recover_with_bus(candidate)
            seq.append(candidate)
            num -= 1

        print 'load based recovery seq', seq
        return self.cal_residual_power(), seq

    def recovery_load_2(self, num):
        candidate_bus_id = self.connect_bus_list(self.steady_list)
        load_dic = {}
        for item in candidate_bus_id:
            load_dic[item] = self.ini_load[item]

        sorted_list = sorted(load_dic.items(), key=lambda item: item[1], reverse=True)
        seq = []
        for item in sorted_list:
            seq.append(item[0])
            if len(seq) == num:
                break

        print 'load based recovery seq', seq
        return self.recover_with_sequence(seq), seq


    def recovery_low_load_2(self, num):
        candidate_bus_id = self.connect_bus_list(self.steady_list)
        load_dic = {}
        for item in candidate_bus_id:
            load_dic[item] = self.ini_load[item]

        sorted_list = sorted(load_dic.items(), key=lambda item: item[1])
        seq = []
        for item in sorted_list:
            seq.append(item[0])
            if len(seq) == num:
                break

        print 'low load based recovery seq', seq
        return self.recover_with_sequence(seq), seq


    def recovery_random(self, num):
        seq = []
        while num > 0:
            candidate_bus_id = self.connect_bus_list(self.steady_list)
            ran_num = random.randint(0, len(candidate_bus_id)-1)
            candidate = candidate_bus_id[ran_num]
            self.recover_with_bus(candidate)
            seq.append(candidate)
            num -= 1

        print 'random based recovery seq', seq
        return self.cal_residual_power(), seq


    '''
    使用随机策略对网络中的节点进行恢复
    '''
    def recovery_random_2(self, num):
        candidate_bus_id = self.connect_bus_list(self.steady_list)
        random.shuffle(candidate_bus_id)
        seq = []
        for item in candidate_bus_id:
            seq.append(item)
            if len(seq) == num:
                break

        print 'random based recovery seq', seq
        return self.recover_with_sequence(seq), seq







if __name__ == '__main__':

    G = case24_ieee_rts()
    #G = case118()
    g = Power_Graph()
    g.init_by_case(G)
    g.set_ramp_rate(0.3)

    g.draw_P_graph()
    print 'draw initial graph'
    #g.delete_branch(24, 70)
    g.delete_branch(2, 4)
    cf = Power_Failure(g)
    cf.failure_process()
    for graph in cf.steady_list:
        print 'steady graph', graph.bus_id
    cf.draw_graph()
    print 'draw steady graph before recovery'
#    for g in cf.steady_list:
#        g.draw_P_graph()
    Power_Graph.draw_graph_list(cf.steady_list)
    for graph in cf.isolate_list:
        print 'isolate graph', graph.bus_id

    ini_g = Power_Graph()
    ini_g.init_by_case(G)
    #gr = Grid_Recovery(cf.steady_list, ini_g)
    #gr.recover_with_bus(4)
    gr = Grid_Recovery(cf.steady_list, ini_g, cf.isolate_list)
    #gr.recover_with_bus(8)
    #gr.recover_with_bus(7)
    residual_per = gr.recover_with_sequence([8])
    print 'residual percent of power', residual_per
    fail_per, current = gr.cal_failure()
    print 'failure percent of power', fail_per

    for graph in gr.steady_list:
        print 'steady graph', graph.bus_id
    for graph in gr.isolate_list:
        print 'isolate graph', graph.bus_id
    print 'failed bus id', gr.failed_bus_id
    print 'draw steady graph after recovery'
    for graph in gr.isolate_list:
        graph.draw_P_graph()
    Power_Graph.draw_graph_list(gr.steady_list)

    #print 'end of recovering bus 8'
    #gr.recover_with_bus_2(7)
    #Power_Graph.draw_graph_list(gr.steady_list)



    '''
    case = case24_ieee_rts()
    case['bus'] = np.array([[   2.,      2.,      0. ,    20. ,     0.,      0.,      1.,      1.,      0.,
   138.,      1.,      1.05 ,   0.95],
 [   4.,      1.,     16.9,    15.,      0.,      0.,      1.,      1.,      0.,
   138.,      1.,      1.05,    0.95]])
    case['branch'] = np.array([[2,   4, 0.0328, 0.1267, 0.0343, 175, 208, 220, 0,    0, 1, -360, 360]])
    case['gen'] = np.array([[   2.,      16.9,      0.,      10.,       0.,       1.035,  100.,       1.,
    20.,      16.,       0.,       0.,       0.,       0.,       0.,       0.,
     0.,       0.,       0.,       0.,       0.   ]])
    del case['gencost']
    del case['areas']
    rundcpf(case)
    '''


