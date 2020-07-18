import numpy as np
import math

def check_weights(ws,verbose=False):

  if(ws is None):
    weights = None
  elif(np.sum(ws)==0):
    weights = None
    if(verbose):
      print("Warning::weighting factors sum to zero -> ignoring weights") 
  elif(not np.all(ws)):
    weights = None
  else:
    weights = ws/np.sum(ws)

  return weights

def avg(values,weights=None):
  weights=check_weights(weights)
  return float(np.average(values,weights=weights))

def var(values,weights=None):
 
  weights=check_weights(weights)
  if(weights is None):
    return np.std(values)
  else:
    average = np.average(values,weights=weights)
    return float(np.average((values-average)**2, weights=weights))

def std(values,weights=None):

  weights=check_weights(weights)
  if(weights is None):
    return np.std(values)
  else:
    return float(math.sqrt(var(values,weights)))

def emitt(x,p,weights):
 
  x0 = avg(x,weights)
  p0 = avg(p,weights)
  xx = var(x,weights)
  pp = var(p,weights)
  xp = avg( (x-x0)*(p-p0), weights)
  
  return math.sqrt( xx*pp - xp*xp )

# HELPER FUNCTIONS:
def vprint(out_str,verbose,indent_number,new_line):

   indent="   "
   total_indent = ""

   for x in range(0,indent_number):
      total_indent = total_indent + indent

   if(verbose):
      if(new_line):
         print(total_indent+out_str,end="\n")
      else:
         print(total_indent+out_str,end="")
