import random
import math
import networkx as nx
import  numpy as np
import matplotlib.pyplot as plt


def draw_seqlen():
    f = open('data_analysis/case300_seqlen.txt')
    lines = f.readlines()

    List = []

    for i in range(0, len(lines)):
        item = lines[i].strip().split('\t')
        print item
        if i == 0:
            List.append([float(val)  for val in item])
        else:
            List.append([float(val)*100 for val in item])

    print List
    x = List[0]
    SRG = List[1]
    HD = List[2]
    LD = List[3]
    HL = List[4]
    LL = List[5]
    RD = List[6]

    f.close()
    m_size = 10
    #plt.figure(figsize=(4,3))
    font_dict = {'size': 20}
    font_dict2 = {'size': 16}
    plt.xlabel('sequence length m', font_dict)
    plt.ylabel('residual power RP (%)', font_dict)
    plt.plot(x, SRG, marker='s', markersize = m_size)
    plt.plot(x, HD, marker='v', markersize = m_size)
    plt.plot(x, LD, marker='o', markersize = m_size)
    plt.plot(x, HL, marker='d', markersize = m_size)
    plt.plot(x, LL, marker='^', markersize = m_size)
    plt.plot(x, RD, marker='p', markersize = m_size)
    #case118: bbox_to_anchor=(0.6, 0.35)
    plt.legend(('SRG', 'high degree', 'low degree', 'high load', 'low load', 'random'), prop = font_dict2, loc = 0 ,  ncol = 1)
    plt.xlim(1.8, 9.2)   #case57:1.8,5.2        case118:1.8,9.2         case300:1.8,2       case57_9: 1.8,9.2
    plt.ylim(55, 90)     #case57:0.45, 0.7          case118:-0.05,0.8         case300:0.55,0.9        case57_9: 0.65,0.95
    plt.xticks(np.arange(2, 10, 1), fontsize =20)         #case57:2,6,1       case118:2,10,1      case300:2,10,1       case57_9: 2,10,1
    plt.yticks(np.arange(55, 90.1, 5), fontsize = 20)       #case57:0.45,0.75,0.05          case118:0,0.85,0.1        case300:0.55,0.9,0.05    case57_9: 0.65,1,0.05
    plt.show()


def draw_ramp():
    f = open('data_analysis/case300_ramp.txt')
    lines = f.readlines()

    List = []

    for i in range(0, len(lines)):
        item = lines[i].strip().split('\t')
        print item
        if i == 0:
            List.append([float(val)  for val in item])
        else:
            List.append([float(val)*100 for val in item])

    print List
    x = List[0]
    SRG = List[1]
    HD = List[2]
    LD = List[3]
    HL = List[4]
    LL = List[5]
    RD = List[6]
    IN = List[7]

    f.close()
    m_size = 10
    #plt.figure(figsize=(4,3))
    font_dict = {'size': 20}
    font_dict2 = {'size': 16}
    plt.xlabel(r'ramp rate $\rho$', font_dict)
    plt.ylabel('residual power RP (%)', font_dict)
    plt.plot(x, SRG, marker='s', markersize = m_size)
    plt.plot(x, HD, marker='v', markersize = m_size)
    plt.plot(x, LD, marker='o', markersize = m_size)
    plt.plot(x, HL, marker='d', markersize = m_size)
    plt.plot(x, LL, marker='^', markersize = m_size)
    plt.plot(x, RD, marker='p', markersize = m_size)
    plt.plot(x, IN, marker='*', markersize = m_size)


    plt.legend(('SRG', 'high degree', 'low degree', 'high load', 'low load', 'random', 'initial'), prop = font_dict2, loc = 0, ncol = 2)
    plt.xlim(0.05, 1.05)         #0.05, 1.05
    plt.ylim(39, 90)         #case57:-0.05,0.95            case118:-0.05,0.75        case300:0.42,0.9       case57_9: 0.6,0.95
    plt.xticks(np.arange(0.1, 1.1, 0.1), fontsize =20)          #0.1,1.1,0.1
    plt.yticks(np.arange(40, 90.1, 5), fontsize = 20)         #case57:0,1,0.1     case118:0,0.8,0.1       case300:0.45,0.9,0.05      case57_9: 0.6,0.95,0.05
    plt.show()




def draw_P():
    f = open('data_analysis/case300_P_2.txt')
    lines = f.readlines()

    List = []

    for i in range(0, len(lines)):
        item = lines[i].strip().split('\t')
        print item
        if i == 0:
            List.append([float(val)  for val in item])
        else:
            List.append([float(val)*100 for val in item])

    print List
    x = List[0]
    SRG_3 = List[1]
    SRG_5 = List[2]
    SRG_7 = List[3]

    f.close()
    m_size = 10
    #plt.figure(figsize=(4,3))
    font_dict = {'size': 20}
    font_dict2 = {'size': 16}
    plt.xlabel('K', font_dict)
    plt.ylabel('residual power RP (%)', font_dict)
    plt.plot(x, SRG_3, marker='s', markersize = m_size)
    plt.plot(x, SRG_5, marker='v', markersize = m_size)
    plt.plot(x, SRG_7, marker='o', markersize = m_size)


    plt.legend((r'$\rho$=0.3', r'$\rho$=0.5', r'$\rho$=0.7'), prop = font_dict2, loc = 0, ncol = 1)
    plt.xlim(9, 31)
    plt.ylim(84, 87)
    plt.xticks(np.arange(10, 32, 2), fontsize =20)
    plt.yticks(np.arange(84, 87.1, 0.5), fontsize = 20)
    plt.show()



def draw_R():
    f = open('data_analysis/case300_R_2.txt')
    lines = f.readlines()

    List = []

    for i in range(0, len(lines)):
        item = lines[i].strip().split('\t')
        print item
        if i == 0:
            List.append([float(val)  for val in item])
        else:
            List.append([float(val)*100 for val in item])

    print List
    x = List[0]
    SRG_3 = List[1]
    SRG_5 = List[2]
    SRG_7 = List[3]

    f.close()
    m_size = 10
    #plt.figure(figsize=(4,3))
    font_dict = {'size': 20}
    font_dict2 = {'size': 16}
    plt.xlabel('T', font_dict)
    plt.ylabel('residual power RP (%)', font_dict)
    plt.plot(x, SRG_3, marker='s', markersize = m_size)
    plt.plot(x, SRG_5, marker='v', markersize = m_size)
    plt.plot(x, SRG_7, marker='o', markersize = m_size)



    plt.legend((r'$\rho$=0.3', r'$\rho$=0.5', r'$\rho$=0.7'), prop = font_dict2, loc = 0, ncol = 1)
    plt.xlim(0, 31)
    plt.ylim(83, 87)
    plt.xticks(np.arange(0, 32, 2), fontsize =20)
    plt.yticks(np.arange(83, 87.1, 0.5), fontsize = 20)
    plt.show()





#top=0.93
#left=0.12
#right=0.93
#bottom=0.1
if __name__ == '__main__':
    #draw_seqlen()
    #draw_ramp()
    #draw_P()
    draw_R()