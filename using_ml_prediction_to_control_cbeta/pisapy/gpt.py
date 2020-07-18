import numpy as np 
from collections import OrderedDict as odict
import math
from pisapy.tools import avg
from pisapy.tools import std
from pisapy.tools import emitt

def calc_statistical_data(data,print_path = None, use_ref = True, s_interpolation=True):

   # Compute statistical data as a function of t
   tstat = odict()
   tstat["s"]=[]
   tstat["t"]=[]

   stat_func = ["avg","std","min","max"]
   stat_vars = ["x","y","z","GBx","GBy","GBz","G"]
   for svar in stat_vars:
      for sfun in stat_func:
         tstat[sfun+"_"+svar]=[]
 
   emitt_vars = ["x","y","z"]
   for vstr in emitt_vars:
      tstat["en"+vstr]=[]

   if(use_ref):
      tdata = data.tdata_ref
   else:
      tdata = data.tdata

   for tout in tdata:
 
      weights = tout["nmacro"]/np.sum(tout["nmacro"])  

      tstat["t"].append(tout["time"])
      tstat["s"].append(tout["s"])

      # Compute statistical data
      for svar in stat_vars:
         tstat["avg_"+svar].append( avg(tout[svar],weights) )
         tstat["std_"+svar].append( std(tout[svar],weights) )
         tstat["min_"+svar].append(tout[svar].min())
         tstat["max_"+svar].append(tout[svar].max())

      # Compute the emittances
      emit_vars = ["x","y","z"]
      for vstr in emit_vars:
         tstat["en"+vstr].append( emitt(tout[vstr],tout["GB"+vstr],weights) )

   # Compute statistical data as at screens
   pstat = odict()
   pstat["s"]=[]
   pstat["t"]=[]
    
   stat_func = ["avg","std","min","max"]
   stat_vars = ["x","y","t","GBx","GBy","GBz","G"]
   for svar in stat_vars:
      for sfun in stat_func:
         pstat[sfun+"_"+svar]=[]

   emitt_vars = ["x","y"]
   for vstr in emitt_vars:
      pstat["en"+vstr]=[]

   #print(data.pdata[0])
   for screen in data.pdata:

      weights = screen["nmacro"]/np.sum(screen["nmacro"])    

      pstat["t"].append(screen["time"])
      pstat["s"].append(screen["s"])
      for svar in stat_vars:
         pstat["avg_"+svar].append(avg(screen[svar],weights))
         pstat["std_"+svar].append(std(screen[svar],weights))
         pstat["min_"+svar].append(screen[svar].min())
         pstat["max_"+svar].append(screen[svar].max()) 

      # Compute the emittances
      emit_vars = ["x","y"]
      for vstr in emit_vars:
         pstat["en"+vstr].append(emitt(screen[vstr],screen["GB"+vstr],weights))

   if(s_interpolation):  
      
      smin = tstat["s"][0]
      smax = tstat["s"][-1]
      #print(smin,smax)
      ss = np.linspace(smin,smax,len(tstat["s"]))

      stdata = tstat["s"]
      for v in tstat.keys():
         if(v!="s"):
            tstat[v] = np.interp(ss, stdata, tstat[v])

   if(print_path is not None):

      try:
         header_line = ""
         for header in tstat.keys():
            header_line = header_line + "   " + header
 
         fid1 = open(print_path+"gpt.tout.stat.txt",'wt') 
         fid1.write(header_line+"\n")
         for ii in range(len(tstat["t"])):
            line = ""
            for v in tstat.keys():
               line = line + "   "+str(tstat[v][ii])
            fid1.write(line+"\n")
         fid1.close()

         header_line = ""
         for header in pstat.keys():
            header_line = header_line + "   " + header

         fid2 = open(print_path+"gpt.screen.stat.txt",'wt') 
         fid2.write(header_line+"\n")
         for ii in range(len(pstat["s"])):
            line = ""
            for v in pstat.keys():
               line = line + "   " + str(pstat[v][ii])
            fid2.write(line+"\n")
         fid2.close()

      except Exception as ex:
         print("Exception occured writing tout stat file: "+str(ex))

   return (tstat,pstat)

