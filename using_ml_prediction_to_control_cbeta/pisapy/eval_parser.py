import sys
#import re
#import numpy as np
#import matplotlib.pyplot as plt
class eval_parser:

   def __init__(self,filename,verbose):

      self.lines = []
      self.data_names = []
      self.data_param_strs = []
      self.data_dict = {}

      self.flags = {}
      self.paths = {}
      self.decs = {}
      self.objs = {}
      self.cons = {}

      if(verbose):
         print("\nInitializing file_data object: ")

      self.verbose=verbose
      self.file_name = filename
         
      if(verbose):
         print('\n   Reading input data file "'+self.file_name+'":',end="")

      self.read_data_file()

      if(verbose):
         print('done.')

   def read_data_file(self):

      # Read header line
      file_handle = open(self.file_name, 'r')
      inlines = file_handle.readlines()
      
      for line in inlines:
         line=line.strip()
         
         if (line!=""):
            line_split_on_comments = line.split("#")
            tokens = line_split_on_comments[0].split()
            #print tokens
            if not(tokens[0]==""):
               self.lines.append(line)
               self.data_dict[tokens[0]]=tokens[1:]
               self.data_names.append(tokens[0])
               self.data_param_strs.append(tokens[1:])
            elif(self.verbose): 
               print("Warning: skipping line: '"+tokens+"'.")

      file_handle.close()
   
      for ii in range(len(self.data_names)):
         data_name = self.data_names[ii]
         data_strs = self.data_param_strs[ii]
         if not data_strs:
            print("Warning: can't sort data name: '"+data_name+"'.")
         elif len(data_strs)>0:
            if (data_strs[0]=="F"): 
               self.flags[data_name]=int(data_strs[1])
            elif (data_strs[0]=="P"):
               self.paths[data_name]=data_strs[1]
            elif (data_strs[0]=="D"): 
               self.decs[data_name]=float(data_strs[1])
            elif (data_strs[0]=="O"): 
               self.objs[data_name]=float('nan')
            elif (data_strs[0]=="C"): 
               self.cons[data_name]=float('nan')

   def get_ID_number(self):
      return self.data_dict["ID"][1]

   def get_node_name(self):
      return self.data_dict["NODE"][1]

   def get_flag_dict(self):
      return self.flags

   def get_path_dict(self):
      return self.paths

   def get_decision_dict(self):
      return self.decs

   def get_objective_dict(self):
      return self.objs 

   def get_constraint_dict(self):
      return self.cons

   def get_DOC_dict(self):

     doc = {}
     doc["ID"] = self.get_ID_number()
     doc["decisions"] = self.get_decision_dict()
     doc["objectives"] = self.get_objective_dict()
     doc["constraints"] = self.get_constraint_dict()  

     return doc

   def print_eval(self,filename,doc):

      print('inside eval parser and the function is print eval')
      print('filename is',filename)

      f = open(filename,"w")

      for line in self.lines: 
         
         tokens = line.split()      
         if (tokens[1]=="O" and ( tokens[0] in doc["objectives"].keys() ) ):
            f.write(tokens[0]+"  O  "+str(doc["objectives"][tokens[0]])+"\n")
         elif (tokens[1]=="C" and ( tokens[0] in doc["constraints"].keys() ) ): 
            f.write(tokens[0]+"  C  "+str(doc["constraints"][tokens[0]])+"\n")
         else:
            f.write(line+"\n")

      f.close()

