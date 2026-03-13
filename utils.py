# This file is part of the iaif_utils package
#  mt5se home: https://github.com/paulo-al-castro/iaif_utils
# Author: Paulo Al Castro
# Date: 2026-03-02

##########################################

import numpy as np
import pandas as pd


# X is an array of arrays with values 
def ts2Dataset(X,timeFrame):
    ds=np.array()
    for line in range(len(X)-timeFrame):
        for x in X:
            for i in range(timeFrame):
                ds=ds.append(x[line+i])

    n_fields=len(X)
    size=len(ds)
    ds.reshape(size/(n_fields*timeFrame),n_fields*timeFrame)
    return ds
# From bars to dataset
def bars2Dataset(bars,target,timeFrame,horizon=1):
	ds=pd.DataFrame()
	lines=len(bars)
	for time in range(timeFrame):
		for s in bars.keys():
			aux=bars[s][time:lines-horizon-timeFrame+time]
			aux=aux.reset_index(drop=True)
			#del aux['index']
			#print('aux type=',type(aux))
			ds[s+str(time)]=aux
	#print(bars[target][timeFrame+horizon:].shift(-timeFrame),' timeF=',timeFrame,' h=',horizon  )
	aux=bars[target][timeFrame+horizon-1:]
	aux=aux.reset_index(drop=True)
	#del aux['index']
	ds['target']=aux
	return ds

def fromDs2NpArrayAllBut(ds,fieldList):
	all=ds.keys()
	for f in fieldList:
		all=all.drop(f)
	fieldList=[]
	for f in all:
		fieldList.append(f)
	return fromDs2NpArray(ds,fieldList)

# se.ai_utils.get_X( dataframe,features list, time frame ) -> returns a np array
# From bars to dataset
def get_X(df,attr_list,timeFrame,horizon):
	ds=pd.DataFrame()
	lines=len(df)
	for time in range(timeFrame):
		for s in df.keys():
			if s in attr_list:
				aux=df[s][time:lines-timeFrame-horizon+time]
				aux=aux.reset_index(drop=True)
				#del aux['index']
				#print('aux type=',type(aux))
				ds[s+str(time)]=aux
	#print(bars[target][timeFrame+horizon:].shift(-timeFrame),' timeF=',timeFrame,' h=',horizon  )
	#aux=aux.reset_index(drop=True)
	#del aux['index']
	return np.array(ds)


# se.ai_utils.get_X( dataframe,features list, time frame ) -> returns a np array
# From bars to dataset
def get_Y(df,target,timeFrame,horizon):
	Y=pd.DataFrame()
	lines=len(df)
	aux=df[target][timeFrame+horizon:]
	aux=aux.reset_index(drop=True)
	#del aux['index']
	Y['target']=aux

	return np.array(Y)

def get_XY(df,feature_list,target,timeFrame,horizon):
	return get_X(df,feature_list,timeFrame,horizon),get_Y(df,target,timeFrame,horizon)

def fromDs2NpArray(ds,fieldList=[]):
	nfields=len(fieldList)
	#print('nfields=',nfields)
	if nfields==0:
		return None
	elif nfields==1:
		return np.array(ds[fieldList[0]])
	else:
		a=np.array(ds[fieldList[0]])
	
	for i in range(1,nfields):
		a=np.column_stack((a,np.array(ds[fieldList[i]])))
	return a



def discTarget(discretizer,target):
	x=np.array(target)
	x=x.reshape(-1,1)
	dx=discretizer.fit_transform(x) 
	return dx
	
def y(y,timeFrame):
    return y[-timeFrame:]



