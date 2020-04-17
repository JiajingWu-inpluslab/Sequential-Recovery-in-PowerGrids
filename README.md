# Sequential Recovery of Complex Networks 

This is a python implementation of sequential recovery strategy based on Sequential Recovery Graph (SRG) for  a damaged power grid, as described in our paper:

Jiajing Wu, Zhenhao Chen, Yihan Zhang, Yongxiang Xia, Xi Chen, Sequential Recovery of Complex Networks Suffering From Cascading Failure Blackouts

## Requirements
- python 2.7
- networkx
- numpy
- pypower

## Run the demo
For SAG:
```
python Recovery_SAG.py
```
For exhaustive search:
```
python Recovery_exhaustive.py
```
## Code Discription

- ```Graph.py```: implements the basic functions of power grids
- ```Power_Failure.py```: implements the cascading failure of power grids
- ```Grid_Recovery.py```: implements the grid recovery function, inherited from the Power_Failure class
- ```SAG.py```: implements the Sequential Recovery Graph (SRG) function
- ```Recovery_SAG.py```: implements the SRG-based power grid sequence recovery strategy
- ```Recovery_exhaustive.py```: implements the power grid sequence recovery function based on exhaustive search

## Data Discription
The original data of IEEE power grids (e.g., IEEE 57, IEEE 118 and IEEE 300 Bus Systems) is included in the pypower. The data of damaged power grids were generated from these original data.
- ```case24```:  The data of damaged power grids that were generated from IEEE 24 Bus System.
- ```case57```:  The data of damaged power grids that were generated from IEEE 57 Bus System.
- ```case118```:  The data of damaged power grids that were generated from IEEE 118 Bus System.
- ```case300```:  The data of damaged power grids that were generated from IEEE 300 Bus System.

Every ```TXT``` file decribes how a damaged power grid was generated:
- ```case24_cascade_attack_1_6.txt```: In IEEE 24 Bus System, we attacked node with bus id of 1 and finally, six nodes were failed after cascading failure process. 

## Cite
TBD
