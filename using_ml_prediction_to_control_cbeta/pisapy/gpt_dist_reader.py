import sys
import math
import re
import os
import numpy as np

from pisapy.tools import avg
from pisapy.tools import std
from pisapy.tools import var
from pisapy.tools import emitt

class gpt_dist_reader:

   def __init__(self,filenames,v2,s0,verbose,set_ref_data):
   
      if isinstance(filenames,str):
         filenames = [filenames]

      self.data_files=filenames
      self.tdata = []      # phase space data from tout
      self.tdata_ref = []  # phase space data in centroid coordinates
      self.pdata = []      # data from screens
      self.orbit = {}      # centroid orbit: (xvec, pvec), s, t, M [centroid ccs]
      self.verbose = verbose

      self.read_input_file()
      self.sort_screen_data()
      
      self.set_GB()
      self.set_avg_data()

      if(len(self.tdata)>0):
         self.set_orbit(v2,s0)

      if(set_ref_data):
         self.set_tdata_ref()
      
      self.set_std_data()
      #self.set_avg_data()
      self.set_twiss_data()

      self.gpt_units={}
      self.gpt_units["x"]="m"
      self.gpt_units["y"]="m"
      self.gpt_units["z"]="m"
  
      self.gpt_units["GBx"]="GB"
      self.gpt_units["GBy"]="GB"
      self.gpt_units["GBz"]="GB"

      self.gpt_units["t"]="s"

   def read_input_file(self):
      
      # Read in file:
      self.vprint("Reading data from files: ",0,True)
 
      for data_file in self.data_files:

         self.vprint("Reading data from file: "+data_file,1,True)
         file_handle = open(data_file, 'r') 
         lines = file_handle.readlines()
         file_handle.close()

         t_indices=[]
         p_indices=[]

         self.vprint("Saving wcs tout and ccs screen data structures: "+str(data_file)+": ",2,False)
         line_count = 0
         for line in lines:

            tokens = line.split()
            if (len(tokens)>0):
               if(tokens[0] == "position"):
                  p_indices.append(line_count)
               if(tokens[0]=="time"):
                  t_indices.append(line_count)
            line_count=line_count+1

         for ii in range(len(p_indices)):
            p_index = p_indices[ii]
            p_line = lines[p_indices[ii]]
            p_tokens = p_line.split()
            position = float(p_tokens[1])
          
            screen={}
            screen["number"]=ii
            screen["position"]=position

            stop_index = []
            if ii==len(p_indices)-1:
              stop_index = len(lines)-1
            else:
              stop_index = p_indices[ii+1]-1
         
            for jj in range(p_index+1,stop_index):

               line = lines[jj]
               tokens=line.split()
               if(jj==p_index+1):
                  headers = tokens
                  for token in tokens:
                    screen[token]=[]
               else:
                  for kk in range(len(headers)):
                     screen[headers[kk]].append(float(tokens[kk]))
         
            for param in screen.keys():
               screen[param]=np.array(screen[param])
 
            t = screen["t"]
            if len(t)<1:
               print("gpt_dist_reader::Warning -> screen at position " +str(screen["position"])+" had no data.")
         
            screen["time"]=avg(t,weights=screen["nmacro"])
            self.pdata.append(screen)

         for ii in range(len(t_indices)):

            t_index = t_indices[ii]
            t_line = lines[t_indices[ii]]
            t_tokens = t_line.split()
            time = float(t_tokens[1])
            #print time          

            tout={}
            tout["number"]=ii
            tout["time"]=time

            stop_index = []
            if ii==len(t_indices)-1:
               if(len(p_indices)>0):
                  stop_index = p_indices[0]-1
               else:
                  stop_index = len(lines)-1
            else:
               stop_index = t_indices[ii+1]-1
         
            headers=[]
            for jj in range(t_index+1,stop_index):

               line = lines[jj]
               tokens=line.split()
              
               if(jj==t_index+1):
                 
                  headers = tokens
                  for token in tokens:
                     tout[token]=[]
               elif(len(tokens)>0):
                  noff = len(headers) - len(tokens)
                  for kk in range(len(tokens)):
                     tout[headers[kk+noff]].append(float(tokens[kk]))

            for param in tout.keys():
               tout[param]=np.array(tout[param])
              
            tout["n"] = len(tout["x"])

            if(tout["n"]>0):
               self.tdata.append(tout) 

         self.vprint("done.",0,True)
      #print len(self.tdata)  

   def get_tout_by_t(self,t):

      t_tolerance=1e-6 
      for tout in self.tdata:
         if(t-tout["time"]==0):
            break
         elif(t != 0  and abs( (tout["time"]-t)/t) < t_tolerance):
            break

      return tout

   def get_tout_by_index(self,index):
      if(index <= len(self.tdata)-1):
         return self.tdata[index]
      else:
         return []

   def get_tout_data(self):
      return self.tdata

   def get_screen_by_pos(self,pos):

      pos_tolerance=1e-6 
      for screen in self.pdata:
         if(pos-screen["position"]==0):
            break
         elif(pos != 0  and abs( (screen["position"]-pos)/pos) < pos_tolerance):
            break

      return screen

   def get_screen_by_index(self,index):
      if(index <= len(self.pdata)-1):
         return self.pdata[index]
      else:
         return []

   def get_screen_data(self):
      return self.pdata

   def sort_screen_data(self):

      self.vprint("Sorting screen outputs by average time: ",0,False)

      ts=[]
      inds={}

      for screen in self.pdata:
         ts.append(screen["time"])

      ts_sorted = sorted(ts)
      pdata_temp=[]

      for t in ts_sorted:
         for screen in self.pdata:
            if(t == screen["time"]):
               pdata_temp.append(screen)
               
      self.pdata=pdata_temp
      self.vprint("done.",0,True)

   def set_GB(self):

      self.vprint("Computing normalized momenta:",0,False)

      for ii in range(len(self.tdata)):

         G  = self.tdata[ii]["G"]
         Bx = self.tdata[ii]["Bx"]
         By = self.tdata[ii]["By"]
         Bz = self.tdata[ii]["Bz"]

         self.tdata[ii]["GBx"]=G*Bx
         self.tdata[ii]["GBy"]=G*By
         self.tdata[ii]["GBz"]=G*Bz

      for ii in range(len(self.pdata)):

         G  = self.pdata[ii]["G"]
         Bx = self.pdata[ii]["Bx"]
         By = self.pdata[ii]["By"]
         Bz = self.pdata[ii]["Bz"]

         self.pdata[ii]["GBx"]=G*Bx
         self.pdata[ii]["GBy"]=G*By
         self.pdata[ii]["GBz"]=G*Bz
   
      self.vprint("done.",0,True)
      
   def set_avg_data(self):

      self.vprint("Computing averaged (avg) data...",0,True)

      if( len(self.tdata)>0 and ("avg" not in self.tdata[0].keys()) ):
         self.vprint("Computing averaged (avg) tout data:",1,False)   
         for ii in range(len(self.tdata)):
            if("avg" not in self.tdata[ii].keys()):   
               self.tdata[ii]["avg"]={}  
               for param in self.tdata[ii].keys():
                  if(param in ["x","y","z","Bx","By","Bz","GBx","GBy","GBz","G"]):
                     self.tdata[ii]["avg"][param]=avg(self.tdata[ii][param],weights=self.tdata[ii]["nmacro"])
         self.vprint("done.",0,True)
   
      if( len(self.tdata_ref)>0 and ("avg" not in self.tdata_ref[0].keys()) ):
         self.vprint("Computing averaged (avg) tout ref data:",1,False) 
         for ii in range(len(self.tdata_ref)):
            if("avg" not in self.tdata_ref[ii].keys()):       
               self.tdata_ref[ii]["avg"]={}  
               
               for param in self.tdata_ref[ii].keys():
                  if(param in ["x","y","z","Bx","By","Bz","GBx","GBy","GBz","G"]):
                     self.tdata_ref[ii]["avg"][param]=avg(self.tdata_ref[ii][param],weights=self.tdata_ref[ii]["nmacro"])
         self.vprint("done.",0,True)

      if( len(self.pdata)>0 and ("avg" not in self.pdata[0].keys()) ):
         self.vprint("Computing averaged (avg) screen data:",1,False)   
         for ii in range(len(self.pdata)):
            if("avg" not in self.pdata[ii].keys()):
               self.pdata[ii]["avg"]={} 
               for param in self.pdata[ii].keys():
                  if(param in ["x","y","z","Bx","By","Bz","GBx","GBy","GBz","G"]):
                     self.pdata[ii]["avg"][param]=avg(self.pdata[ii][param],weights=self.pdata[ii]["nmacro"])
         self.vprint("done.",0,True)

      self.vprint("...done.",0,True) 

   def set_std_data(self):
      
      self.vprint("Computing deviation (std) data:",0,False)

      for ii in range(len(self.tdata)):
         self.tdata[ii]["std"]={}  
         for param in self.tdata[ii].keys():
            if(param in ["x","y","z","Bx","By","Bz","GBx","GBy","GBz","G"]):
               self.tdata[ii]["std"][param]=std(self.tdata[ii][param],weights=self.tdata[ii]["nmacro"])

      for ii in range(len(self.tdata_ref)):
         
         self.tdata_ref[ii]["std"]={}  
         for param in self.tdata_ref[ii].keys():
            if(param in ["x","y","z","Bx","By","Bz","GBx","GBy","GBz","G"]):
               self.tdata_ref[ii]["std"][param]=std(self.tdata_ref[ii][param],weights=self.tdata_ref[ii]["nmacro"])

      for ii in range(len(self.pdata)):
         self.pdata[ii]["std"]={}   
         for param in self.pdata[ii].keys():
            if(param in ["x","y","z","Bx","By","Bz","GBx","GBy","GBz","G"]):
               self.pdata[ii]["std"][param]=std(self.pdata[ii][param],weights=self.pdata[ii]["nmacro"])

      self.vprint("done.",0,True)

   def set_twiss_data(self):

      self.vprint("Computing Twiss data: ",0,False)
      for ii in range(len(self.tdata)):

         weights = self.tdata[ii]["nmacro"]
         twiss_x = self.calc_twiss_parameters(self.tdata[ii]["x"],self.tdata[ii]["GBx"],self.tdata[ii]["GBz"],weights)
         twiss_y = self.calc_twiss_parameters(self.tdata[ii]["y"],self.tdata[ii]["GBy"],self.tdata[ii]["GBz"],weights)

         self.tdata[ii]["twiss"]={}
         self.tdata[ii]["twiss"]["x"]={}; self.tdata[ii]["twiss"]["y"]={}
         for param in twiss_x:
            self.tdata[ii]["twiss"]["x"][param] = twiss_x[param]
            self.tdata[ii]["twiss"]["y"][param] = twiss_y[param]
        
      for ii in range(len(self.tdata_ref)):

         weights = self.tdata_ref[ii]["nmacro"]
         twiss_x = self.calc_twiss_parameters(self.tdata_ref[ii]["x"],self.tdata_ref[ii]["GBx"],self.tdata_ref[ii]["GBz"],weights)
         twiss_y = self.calc_twiss_parameters(self.tdata_ref[ii]["y"],self.tdata_ref[ii]["GBy"],self.tdata_ref[ii]["GBz"],weights)

         self.tdata_ref[ii]["twiss"]={}
         self.tdata_ref[ii]["twiss"]["x"]={}; self.tdata_ref[ii]["twiss"]["y"]={}
         for param in twiss_x:
            self.tdata_ref[ii]["twiss"]["x"][param] = twiss_x[param]
            self.tdata_ref[ii]["twiss"]["y"][param] = twiss_y[param]

      for ii in range(len(self.pdata)):

         self.pdata[ii]["twiss"]={}

         weights = self.pdata[ii]["nmacro"]
         twiss_x = self.calc_twiss_parameters(self.pdata[ii]["x"],self.pdata[ii]["GBx"],self.pdata[ii]["GBz"],weights)
         twiss_y = self.calc_twiss_parameters(self.pdata[ii]["y"],self.pdata[ii]["GBy"],self.pdata[ii]["GBz"],weights)

         self.pdata[ii]["twiss"]["x"]={}; self.pdata[ii]["twiss"]["y"]={}
         for param in twiss_x:
            self.pdata[ii]["twiss"]["x"][param] = twiss_x[param]
            self.pdata[ii]["twiss"]["y"][param] = twiss_y[param]

      self.vprint("done.",0,True)

   def set_orbit(self,v2,s0):

      self.vprint("Computing centroid orbit in wcs: ",0,False)

      e2 = v2/np.sqrt(np.dot(v2,v2))
      self.orbit["M"]=[]
 
      N = len(self.tdata)
      for param in ["s","t","G","x","y","z","GBx","GBy","GBz"]:
         self.orbit[param]=np.zeros(N)

      for ii in range(len(self.tdata)):   

         #print self.tdata[ii]["avg"].keys()
         self.orbit["t"][ii]=self.tdata[ii]["time"]
         self.orbit["G"][ii]=self.tdata[ii]["avg"]["G"]

         self.orbit["x"][ii]=self.tdata[ii]["avg"]["x"] 
         self.orbit["y"][ii]=self.tdata[ii]["avg"]["y"] 
         self.orbit["z"][ii]=self.tdata[ii]["avg"]["z"]

         self.orbit["GBx"][ii]=self.tdata[ii]["avg"]["GBx"] 
         self.orbit["GBy"][ii]=self.tdata[ii]["avg"]["GBy"] 
         self.orbit["GBz"][ii]=self.tdata[ii]["avg"]["GBz"] 

         # Only 2D version so far:
         v3 = np.array([self.orbit["GBx"][ii], self.orbit["GBy"][ii], self.orbit["GBz"][ii]])
         e3 = v3/np.sqrt(np.dot(v3,v3))

         e1 = np.cross(e2,e3)
         self.orbit["M"].append(np.array([e1,e2,e3]))
         
      self.orbit["s"][0]=s0
      for ii in range(len(self.orbit["t"])-1):

            t1 = self.orbit["t"][ii];    t2 = self.orbit["t"][ii+1]
            G1 = self.orbit["G"][ii];    G2 = self.orbit["G"][ii+1]
            B1 = self.gamma_to_beta(G1); B2 = self.gamma_to_beta(G2)

            x1 = self.orbit["x"][ii]; x2 = self.orbit["x"][ii+1]
            y1 = self.orbit["y"][ii]; y2 = self.orbit["y"][ii+1]
            z1 = self.orbit["z"][ii]; z2 = self.orbit["z"][ii+1]

            if(np.absolute(G1-G2)<1e-5*G1):# Consider energy constant
               c = 299792458
               ds = c*(t2-t1)*(B1+B2)/2
            else:# Energy changing, assume straight line motion
               ds = np.sqrt( (x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2 )

            self.orbit["s"][ii+1] = self.orbit["s"][ii] + ds         

      for ii in range(len(self.tdata)):
         self.tdata[ii]["s"]=self.orbit["s"][ii]

      for ii in range(len(self.pdata)):
         self.pdata[ii]["s"]=np.interp(self.pdata[ii]["time"],self.orbit["t"],self.orbit["s"]) 
         #print("s:",self.pdata[ii]["s"],self.pdata[ii]["time"])

      self.vprint("done.",0,True)

   def set_tdata_ref(self):

      for ii in range(len(self.tdata)):

         tout_ref = {}
         
         for param in ["q","n","number","ID","s","G","nmacro","m","time"]:
            tout_ref[param]=self.tdata[ii][param]
  
         M = self.orbit["M"][ii]
         r0 = np.array([self.orbit["x"][ii],self.orbit["y"][ii],self.orbit["z"][ii]])
         r0.shape=(3,1)
         
         r = np.zeros(shape=(3,self.tdata[ii]["n"]))
         r[0,:] = self.tdata[ii]["x"]
         r[1,:] = self.tdata[ii]["y"]
         r[2,:] = self.tdata[ii]["z"]

         gb = np.zeros(shape=(3,self.tdata[ii]["n"]))
         gb[0,:] = self.tdata[ii]["GBx"]
         gb[1,:] = self.tdata[ii]["GBy"]
         gb[2,:] = self.tdata[ii]["GBz"]
         
         r_ref  = np.dot(M,r-r0)
         gb_ref = np.dot(M,gb)

         tout_ref["x"]=r_ref[0,:]
         tout_ref["y"]=r_ref[1,:]
         tout_ref["z"]=r_ref[2,:]

         tout_ref["GBx"]=gb_ref[0,:]
         tout_ref["GBy"]=gb_ref[1,:]
         tout_ref["GBz"]=gb_ref[2,:]

         tout_ref["Bx"]=self.GB_to_beta(tout_ref["GBx"])
         tout_ref["By"]=self.GB_to_beta(tout_ref["GBy"])
         tout_ref["Bz"]=self.GB_to_beta(tout_ref["GBz"]) 

         self.tdata_ref.append(tout_ref)

   def get_avg_tdata(self,param):

      data=[]
      for ii in range(len(self.tdata)):
         if(param in self.tdata[ii]["avg"].keys()):
            data.append(self.tdata[ii]["avg"][param])
         else:
            data.append(float("nan"))   

      data = np.array(data)  
      return data

   def get_std_tdata(self,param):

      data=[]
      for ii in range(len(self.tdata)):
         if(param in self.tdata[ii]["std"].keys()):
            data.append(self.tdata[ii]["std"][param])
         else:
            data.append(float("nan"))   

      data = np.array(data)  
      return data 

   def get_twiss_tdata(self,plane,param):

      data=[]
      for ii in range(len(self.tdata)):
         if(param in self.tdata[ii]["twiss"][plane].keys()):
            data.append(self.tdata[ii]["twiss"][plane][param])
         else:
            data.append(float("nan"))  

      data = np.array(data)  
      return data 

   def get_avg_tdata_ref(self,param):

      data=[]
      for ii in range(len(self.tdata_ref)):
         if(param in self.tdata_ref[ii]["avg"].keys()):
            data.append(self.tdata_ref[ii]["avg"][param])
         else:
            data.append(float("nan"))   

      data = np.array(data)  
      return data

   def get_std_tdata_ref(self,param):

      data=[]
      for ii in range(len(self.tdata_ref)):
         if(param in self.tdata_ref[ii]["std"].keys()):
            data.append(self.tdata_ref[ii]["std"][param])
         else:
            data.append(float("nan"))  

      data = np.array(data)  
      return data 

   def get_twiss_tdata_ref(self,plane,param):

      data=[]
      for ii in range(len(self.tdata_ref)):
         if(param in self.tdata_ref[ii]["twiss"][plane].keys()):
            data.append(self.tdata_ref[ii]["twiss"][plane][param])
         else:
            data.append(float("nan"))  

      data = np.array(data)  
      return data 

   def get_avg_pdata(self,param):

      data=[]
      for ii in range(len(self.pdata)):
         if(param in self.pdata[ii]["avg"].keys()):
            data.append(self.pdata[ii]["avg"][param])
         else:
            data.append(float("nan"))   

      data = np.array(data)  
      return data

   def get_std_pdata(self,param):
      
      data = np.zeros(len(self.pdata))
      s = np.zeros(len(self.pdata))
      for ii in range(len(self.pdata)):
         s[ii]=self.pdata[ii]["s"]
         if(param in self.pdata[ii]["std"].keys()):
            data[ii]=self.pdata[ii]["std"][param]
         else:
            data[ii]=float("nan")

      data = np.array(data)  
      return (data,s) 

   def get_twiss_pdata(self,plane,param):
      
      data = np.zeros(len(self.pdata))
      s = np.zeros(len(self.pdata))
      for ii in range(len(self.pdata)):
         s[ii]=self.pdata[ii]["s"]
         if(param in self.pdata[ii]["twiss"][plane].keys()):
            data[ii]=self.pdata[ii]["twiss"][plane][param]
         else:
            data[ii]=float("nan")

      data = np.array(data)  
      return (data,s) 

   def gamma_to_beta(self,gamma):
      return np.sqrt(1-1/gamma**2)

   def beta_to_gamma(self,beta):
      return 1/np.sqrt(1-beta**2)

   def gamma_to_GB(self,gamma):
      return np.sqrt(gamma**2-1)

   def GB_to_gamma(self,GB):
      return np.sqrt(GB**2+1)

   def GB_to_beta(self,GB):
      return GB/self.GB_to_gamma(GB)

   def calc_twiss_parameters(self,x,px,pz,weights):

      x0  = avg(x,weights)
      px0 = avg(px,weights)
      xp0 = avg(px/pz,weights)

      xp = px/pz
        
      x2  = var(x, weights);       
      px2 = var(px,weights); 
      xp2 = var(xp,weights);    
      xpx = avg( (x-x0)*(px-px0),weights);  
      xxp = avg( (x-x0)*(xp-xp0),weights);  

      if(x2>0 and px2>0):
         en  = np.sqrt( x2*px2 - xpx*xpx )
      else:
         en  = 0 
  
      if(x2>0 and xp2>0):
         eps = np.sqrt(x2*xp2 - xxp*xxp)
         beta  =  x2/eps
         alpha = -xxp/eps
         gamma =  xp2/eps
      else:
         eps = 0; beta = 0; alpha = 0; gamma = 0;     

      return {"en":en,"e":eps,"beta":beta,"alpha":alpha,"gamma":gamma}

   def vprint(self,string,Nindent,flush):

      indent=str("")
      base_indent =str("   ")
    
      for ii in range(Nindent):
         indent = indent + base_indent

      if(self.verbose):
         if(flush):
            print(indent+string,end="\n")
         else:
            print(indent+string,end="")

