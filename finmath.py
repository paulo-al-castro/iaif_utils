# This file is part of the iaif_utils package
#  mt5se home: https://github.com/paulo-al-castro/iaif_utils
# Author: Paulo Al Castro
# Date: 2026-03-02

##########################################
import pandas as pd 
import numpy as np 
from math import sqrt
import statistics 
"""
    calcGeoAvgReturn(returns::Array{Float64} [,n::Int] ) 
 returns the geometric average return of the series of the n first returns returns. If n is not informed the whole array is used 
"""
def calcGeoAvgReturn(returns,n=None):
   ret=1
   if n==None:
      n=len(returns)
   for  i in range(n): 
      ret*=(1+returns[i])
   
   return ret**(1.0/n)-1

 

 
"""
    calcTotalReturn(returns::Array{Float64}) 
   returns the Total return of a series of returns
   If the size is provided it considers just 'size' more recent (more to the right) returns
   left - 0 - (size-1) - right
"""
def calcTotalReturn(returns,size=None):
   ret=1
   s=len(returns)
   if size==None:
      size=0
   elif size<s:
      size=s-size
   else: 
      size=0 # it gets in maximum the return of the total number of elements
   for  i in range(s-1,size-1,-1): 
      ret*=(1+returns[i])
   return ret-1

def changedSignal(returns):
   s=len(returns)
   if s==None or s==1:
      return False
   for i in range(s-1):
      if returns[i]*returns[i+1]<0:
         return True
   return False


"""
    calcAvgReturn(returns::Array{Float64}) 
    returns the arithmetic average return of the series of returns
"""
def calcAvgReturn(returns):
   sum=float(0)
   s=len(returns)
   for  i in range(s): 
      sum+=returns[i]
   return sum/s


"""
    calcAnnualReturn(returns::Array{Float64}, numberOfDays)  
    returns the equivalent annual return for the given serie of returns. The numberOfDays informs the number of working days in the serie, and it
         can have more or less than a year. One year is assumed to have 252 [working] days.
"""
def calcAnnualReturn(returns, numberOfDays):
   gReturn=calcTotalReturn(returns)
   return (1+gReturn)**(252.0/numberOfDays)-1



"""
    calcAnnualSR(returns::Array{Float64}, riskfree, numberOfDays)
    returns the equivalent annual sharpe ratio (SR) for the given serie of returns and risk free rate. The numberOfDays informs the number of working days in the serie, and it
         can have more or less than a year. One year is assumed to have 252 [working] days.
"""
def calcAnnualSR(returns, riskfree, numberOfDays):
   # implemented according paper: Andrew W Lo},The Statistics of Sharpe Ratios, journal = {Financial Analysts Journal}, 2003

   return sqrt(252)*calcSR(returns,riskfree)


"""
    calcStdDev(x::Array{Float64}) 
    return the standard deviation of a sample
"""
def calcStdDev(x):
   return statistics.stdev(x)


"""
    calcSR(returns::Array{Float64}, riskfree)
    returns the Sharpe ratio (SR) for the given serie of returns and risk free rate. 
"""
def calcSR(returns, riskfree):
   avg=calcAvgReturn(returns)
   sigma=calcStdDev(returns)
   if sigma!=0:
       return (avg-riskfree)/sigma
   return -1



"""
    calculates a serie of return given a serie of prices as argument
    return[i]=price[i]/price[i-1]-1
    the serie of returns has length equal to the price serie lenth minus 1.
"""
def calcReturns(serie):
    x=[]
    for i in range(len(serie)-1): # calculates the serie of returns
        x.append(serie[i+1]/serie[i]-1)
    return x


"""
   gives the standard deviation of returns given a serie of prices
"""
def calcStdDevFromPrice(x):
    returns=calcReturns(x)
    return calcStdDev(returns)

"""
   gives the average returns given a serie of prices
"""
def calcAvgReturnFromPrice(x):
    returns=calcReturns(x)
    return calcAvgReturn(returns)

# This file is part of the mt5se package
#  mt5se home: https://github.com/paulo-al-castro/mt5se
# Author: Paulo Al Castro
# Date: 2020-11-17

import pandas as pd 
import numpy as np 
import mt5se.mt5se as se
from scipy import stats



def rsi(returns):
    """
    	Returns the RSI (Relative Strengh Index) of a given serie of returns.
            if the parameter is a pandas.DataFrame it uses the function mt5se.get_return() to get the
            serie of returns
    """
    if type(returns)==pd.core.frame.DataFrame:
        returns=se.get_returns(returns)
    u=0.0
    uc=0
    d=0.0
    dc=0
    for r in returns:
        if r>=0:
            u=u+r
            uc=uc+1
        else:
            d=d+abs(r)
            dc=dc+1
    if uc>0:
        u=u/uc
    if dc>0:
        d=d/dc   
    if d==0:
        d=1.0
    ifr=100*( 1 - 1/(1+u/d))
    return ifr


def slope(serie):
    """
    	Returns the angular coefficient of linear regression (slope)
          for a serie of prices in regular intervals
    """
    x=np.array(range(len(serie)))
    #y=np.array(serie)
    s=stats.linregress(x,serie)
    return s.slope

# equals to slope
def trend(serie):
    """
      	Returns the angular coefficient of linear regression (slope)
          for a serie of prices in regular intervals 
          Same as function slope()
    """
    return slope(serie)

def ma(serie,length=10):
    """"
        Returns the moving average of lenght points.
            In the fist points (0-length), it calculcates the average from 0 to index.
            So, the first ma is equal to the first number of the serie, the second is the average between the first and second numbers of the serie, and so on
    """
    mov_avg=[]
    for i in range(len(serie)):
        if i <=length:
            mov_avg.append(np.mean(serie[0:i+1]))
        else:
            mov_avg.append(np.mean(serie[i-9:i+1]))
    return mov_avg

    