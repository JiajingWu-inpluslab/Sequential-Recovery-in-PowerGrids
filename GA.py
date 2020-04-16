# -*- coding: utf-8 -*-
import sys
import random
import math
import os  
import  networkx as nx
import matplotlib.pyplot as plt
import copy
from Graph import Power_Graph
from Grid_Recovery import Grid_Recovery
from Power_Failure import Power_Failure
from pypower.case14 import case14
from pypower.case57 import case57
from pypower.case30 import case30
from pypower.case39 import case39
from pypower.case118 import case118
from pypower.case300 import case300
from pypower.rundcpf import rundcpf
from time import clock
import  numpy as np
import copy
import Queue
from pypower.case24_ieee_rts import case24_ieee_rts
recover_branch=1
recover_bus=2
class GA():
	def __init__(self,type):
		self.type=type #边修复或点修复
		self.gr = self.init_gr() #grid recover 参数
		print 'init power ',self.gr.cal_residual_power()
		print len(self.gr.failed_bus_id),self.gr.failed_bus_id
		self.ini_power=self.gr.cal_residual_power()
		self.pop_size=200 #种群大小
		self.chrom_len=2  #修复序列大小
		self.pc=0.8 #交叉概率
		self.pm=0.01 #变异概率
		self.popula=self.gen_ini_pop() #种群个体
		self.values=np.zeros(self.pop_size) #种群个体适应值
		self.newpop=copy.deepcopy(self.popula) #每一代种群个体交叉变异后的新一代
		self.iter=0 #当前迭代数
		#self.best=0
		#self.best_chrom=[]
		self.show_value=np.zeros(self.pop_size)
		self.maxiter=250 #最大迭代数

	#随机生成初始种群个体
	def gen_ini_pop(self):
		res=self.memset(self.pop_size,self.chrom_len)
		if self.type==recover_bus:
			candidate_list=self.gr.connect_bus_list(self.gr.steady_list)
		elif self.type==recover_branch:
			candidate_list=self.gr.connect_branch_list(self.gr.steady_list)
		
		print 'ini candi bus',candidate_list
		num_candi=len(candidate_list)
		for k in range(self.pop_size):
			index = np.random.permutation(range(0,num_candi))[:self.chrom_len]  
			for i in range(self.chrom_len):
				res[k][i]=candidate_list[index[i]] 

		return res

	#分配一个二维数组，因为边修复中数组元素是元组
	def memset(self,v1,v2):
		re=[]
		for i in range(v1):
			temp=[]
			for j in range (v2):
				if self.type==recover_bus:
					temp.append(0)
				elif self.type==recover_branch:
					temp.append((0,0))
			re.append(temp)
		return re
	#初始化电网信息
	def init_gr(self):
		#G = case24_ieee_rts()
		#G = case57()
		#G = case118()
		#G = case39()
		G = case300()

		g = Power_Graph()
		new_case = g.case_preprocess(G)
		g.init_by_case(new_case)
		g.set_ramp_rate(0.3)

		g.draw_P_graph()
		print 'draw initial graph'
		delete_list=[66, 289, 298, 255, 72, 87, 263, 290, 83, 167, 241, 13, 225, 243, 232, 34, 147, 269, 132, 249, 122, 2, 37, 127, 94, 199, 202, 76, 156, 67, 131, 248, 188, 238, 15, 84, 44, 8, 220, 189, 206, 162, 169, 107, 17, 282, 164, 198, 115, 261]
		for bus in delete_list:
			g.delete_bus(bus)
		#g.delete_branch(10, 32)
		#g.delete_branch(29, 38)

		cf = Power_Failure(g)
		cf.failure_process()
		#print cf.steady_list
		#cf.draw_graph()
		print 'draw steady graph'
		Power_Graph.draw_graph_list(cf.steady_list)

		

		ini_g = Power_Graph()
		ini_g.init_by_case(G)
		return Grid_Recovery(cf.steady_list, ini_g, cf.isolate_list)

	#def save_max(self):
	#	cur_size=len(self.newpop)
	#	maxit=self.values.argmax()
	#	temp=self.values[maxit]
	#	self.values[maxit]=self.values[cur_size-1]
	#	self.values[cur_size-1]=temp
#
	#	temp=self.newpop[maxit]
	#	self.newpop[maxit]=self.newpop[cur_size-1]
	#	self.newpop[cur_size-1]=temp

	#计算每个个体的适应值
	def cal_pop_values(self):
		cur_size=len(self.newpop)
		self.values=np.zeros(cur_size)
		for i in range(cur_size):
			temp_gr=copy.deepcopy(self.gr)
			for k in self.newpop[i]:
				if self.type==recover_bus:
					temp_gr.recover_with_bus(k)
				elif self.type==recover_branch:
					temp_gr.recover_with_branch(k)
			self.values[i]=temp_gr.cal_residual_power()
		#self.save_max()

	#选择适应值最优的前150个个体
	def select_best(self):
		argx=np.argsort(-self.values)
		for i in range(self.pop_size):
			self.popula[i]=self.newpop[argx[i]]
			self.show_value[i]=self.values[argx[i]]
		self.newpop=copy.deepcopy(self.popula)

	#轮盘赌
	#def select_newpop(self):
	#	cur_size=len(self.newpop)
	#	#淘汰
	#	for i in range(cur_size):
	#		if self.values[i] < self.ini_power:
	#			self.values[i]=0
	#	#轮盘赌
	#	probtrans = copy.deepcopy(self.values)
	#	#计算概率累积分布
	#	cumsumprobtrans = (probtrans/sum(probtrans)).cumsum()  
	#	
	#	for i in range(self.pop_size-1):
	#		temp_cumsum=copy.deepcopy(cumsumprobtrans)
	#		temp_cumsum -= np.random.rand()  
	#		for t in range(temp_cumsum.shape[0]):
	#			if temp_cumsum[t]>0:
	#				self.popula[i]=self.newpop[t]
	#				break;
	#	self.popula[self.pop_size-1]=self.newpop[cur_size-1]
	#	self.newpop=copy.deepcopy(self.popula)
	
	#非法解合法化
	def correct(self,new,old,start,end):
		re=copy.deepcopy(new)
		for i in range(self.chrom_len):
			if i<start or i>end:
				flag=True
				temp=re[i]
				while flag:
					for j in range(start,end+1):
						if re[j]==temp:
							re[i]=old[j]
							temp=re[i]
							break
						if j==end:
							flag=False

		return re

	#交叉
	def cross(self):

		for i in range(self.pop_size-1):
			if np.random.rand() < self.pc:
				j=np.random.randint(self.pop_size-1)
				c1=np.random.randint(self.chrom_len)
				c2=np.random.randint(self.chrom_len)
				start=min(c1,c2)
				end=max(c1,c2)
				old1=self.newpop[i]
				old2=self.newpop[j]
				new1=[]
				new2=[]
				for k in range(self.chrom_len):
					if start<=k and k<=end:
						new1.append(old2[k])
						new2.append(old1[k])
					else:
						new1.append(old1[k])
						new2.append(old2[k])
				new1=self.correct(new1,old1,start,end)
				new2=self.correct(new2,old2,start,end)
				self.newpop.append(new1)
				self.newpop.append(new2)

	#变异
	def mutate(self):

		for i in range(self.pop_size-1):
			if np.random.rand() < self.pm:
				c1=np.random.randint(self.chrom_len)
				c2=np.random.randint(self.chrom_len)
				new_s=copy.deepcopy(self.newpop[i])
				temp=new_s[c1]
				new_s[c1]=new_s[c2]
				new_s[c2]=temp
				self.newpop.append(new_s)

	#输出每一代的代数，最优解的个数，最优适应值，最优解，平均适应值
	def show(self):
		#temp_values=self.values[:self.pop_size]
		#cur_size=len(self.values)
		print 'iter',self.iter
		#print self.values.max(), self.newpop[self.values.argmax()]
		#print self.values[cur_size-1], self.newpop[cur_size-1]
		sum=0
		for i in self.show_value:
			if i == self.show_value.max():
				sum+=1
		print 'max',sum,self.show_value.max()
		print 'mean',self.show_value.mean()
		print self.popula[0]
		#print self.show_value

	def run(self):
		ave_per_iter=[]
		max_num=[]
		while self.iter < self.maxiter:
			self.cal_pop_values() #计算适应度
			self.select_best()#选择
			#self.select_newpop()
			self.show()
			self.cross()#交叉
			self.mutate()#变异
			self.iter+=1
			max_num.append(sum)
			ave_per_iter.append(self.values.mean())

			#print self.values
		print 'max',max_num
		print 'mean',ave_per_iter

if __name__ == '__main__':
	ex=GA(recover_branch)
	ex.run()