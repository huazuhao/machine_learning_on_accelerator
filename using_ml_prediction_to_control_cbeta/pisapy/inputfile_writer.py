import sys
import re

class inputfile_writer:

   def __init__(self,filename,verbose,delimiters):
      # Example delimiters : ["#","=",";"]

      self.file_name = filename
      self.verbose = verbose
      self.comment_delimiter = delimiters[0]
      self.equals_delimiter = delimiters[1]
      self.endline_delimiter = delimiters[2]
      self.lines=[]
      self.print_lines=[]
      self.read_input_file()
      
   def read_input_file(self):

      # Read header line
      file_handle = open(self.file_name, 'r') 
      self.lines = file_handle.readlines()
      self.print_lines = self.lines
      file_handle.close()

   def print_new_file(self,filename):

      file_handle = open(filename,'w')
      file_handle.writelines(self.print_lines)
      file_handle.close()

      return self.print_lines
     
   def set_variable_assignments(self,var_dict):
      
      for name in var_dict.keys():
        error_flag =  self.set_variable_assignment(name,var_dict[name])
        if not error_flag:
           return error_flag
      
      return error_flag

   def set_string_variable(self,name,str_val):

      if not self.check_for_parameter(name): 
         if self.verbose:
            print("inputfile_writer["+self.file_name+"]::set_variable_assignment -> WARNING: could not find parameter '"+ name + "'.")
         error_flag = True
         return error_flag

      assignment_line_indices =  self.find_assignment_lines(name)
      
      if len(assignment_line_indices)>1:
         if self.verbose:
            print("inputfile_writer::set_variable_assignment: ERROR -> Mutliple assignment calls for variable '"+name+"'.")
         error_flag = True
         return error_flag
      line = self.lines[assignment_line_indices[0]]
      line_split_on_comment = line.split(self.comment_delimiter)
      
      original_comment = "\n"
      if len(line_split_on_comment)>1:
         line_split_on_comment[1]=line_split_on_comment[1].replace("\n","")
         original_comment = " "+self.comment_delimiter+" "+line_split_on_comment[1]+"\n"

      tokens = line_split_on_comment[0].split()


   def get_variable_assignment(self,name):

      error_flag = False
   
      if not self.check_for_parameter(name): 
         if self.verbose:
            print("inputfile_writer["+self.file_name+"]::set_variable_assignment -> WARNING: could not find parameter '"+ name + "'.")
         error_flag = True
         return error_flag

      assignment_line_indices =  self.find_assignment_lines(name)

      if len(assignment_line_indices)>1:
         if self.verbose:
            print("inputfile_writer::set_variable_assignment: ERROR -> Mutliple assignment calls for variable '"+name+"'.")
         error_flag = True
         return error_flag

      line = self.lines[assignment_line_indices[0]]
      line_split_on_comment = line.split(self.comment_delimiter)

      tokens = line_split_on_comment[0].split(self.equals_delimiter)
      val_tokens = tokens[1].split(self.endline_delimiter)

      return float(val_tokens[0])

   def set_variable_assignment(self,name,value):

      error_flag = False
   
      if not self.check_for_parameter(name): 
         if self.verbose:
            print("inputfile_writer["+self.file_name+"]::set_variable_assignment -> WARNING: could not find parameter '"+ name + "'.")
         error_flag = True
         return error_flag
 
      assignment_line_indices =  self.find_assignment_lines(name)
      #print(assignment_line_indices,value)  
 
      if len(assignment_line_indices)>1:
         if self.verbose:
            print("inputfile_writer::set_variable_assignment: ERROR -> Multiple assignment calls for variable '"+name+"'.")
         error_flag = True
         return error_flag

      line = self.lines[assignment_line_indices[0]]

      #print("line(" + str(assignment_line_indices[0]) + ") = " + line)

      line_split_on_comment = line.split(self.comment_delimiter)

      original_comment = "\n"
      if len(line_split_on_comment)>1:
         line_split_on_comment[1]=line_split_on_comment[1].replace("\n","")
         original_comment = " "+self.comment_delimiter+" "+line_split_on_comment[1]+"\n"

      tokens =line_split_on_comment[0].split()
      
      # Search for units before comment [used by distgen]
      units = ""
      for token in tokens:
         if token[0]=="[" and token[len(token)-1]=="]":
           units = token 

      old_variable_assignment = tokens[0]
      name_index = old_variable_assignment.find(name)
      name_preffix =  old_variable_assignment[:name_index]

      if isinstance(value,str):
         new_variable_assignment = name_preffix + name + " " + self.equals_delimiter + " " +  value + self.endline_delimiter + " " + units + " " + original_comment
      else:
         new_variable_assignment = name_preffix + name + " " + self.equals_delimiter + " " + str(value) + self.endline_delimiter + " " + units + " " + original_comment

      #self.print_lines = self.lines   
      self.print_lines[assignment_line_indices[0]] = new_variable_assignment
      #print("updated:", self.print_lines[assignment_line_indices[0]])
      #print(new_variable_assignment) 
 
      return error_flag

   def string_replace(self, old_string, new_string):

      error_flag = False
      variable_line_indices =  self.find_variable_lines(old_string)

      if (len(variable_line_indices)>1) or (not variable_line_indices):
         if self.verbose:
            print("inputfile_writer::string_replace: ERROR -> Could not replace string '"+old_string+"' in the input file '"+self.file_name+"'.")
         error_flag = True
         return error_flag 

      old_line = self.lines[variable_line_indices[0]]
      new_line = old_line.replace(old_string,new_string)

      self.print_lines[variable_line_indices[0]]=new_line

      return error_flag

   def find_variable_lines(self, name):
      indices = []
      for ii in range(len(self.lines)):
         line = self.lines[ii].strip()
         if len(line)>0: 
            if not (line[0]==self.comment_delimiter):
               
               line_split_on_comment = line.split(self.comment_delimiter)
               if (line_split_on_comment[0].find(name)!=-1):
                  indices.append(ii)
       
      return indices      

   def find_assignment_lines(self,name):
      """Determine if the variable 'name' is assigned on a line. If so, record and return the indices 
      """
      
      variable_line_indices =  self.find_variable_lines(name)
      assignment_line_indices = []
      if not variable_line_indices:
         return assignment_line_indices
      
      for ii in range(len(variable_line_indices)):
         line = self.lines[variable_line_indices[ii]].strip()
         rename=self.update_name(name) #Deal with parenthesis in parameter names
         match = re.search(rename + "[\s]*" + self.equals_delimiter + "[^" + self.equals_delimiter + "]", line)
         
         if(match and name == line[:len(name)]):
            assignment_line_indices.append(variable_line_indices[ii])

      return assignment_line_indices
  
   def check_for_parameter(self,name):
      var_indices = self.find_assignment_lines(name)
      if not var_indices:
         return False
      else:
         return True

   def update_name(self,name):
      """Function to read in a name that we are searching for and alter the name if it contains (.
 
      Example: ASTRA has a field Emax(1). However the () tells the re.search method to capture that data.
      What we really want is Emax\(1\) which would properly identify the name string
      """
   
      newname=name
      index1=name.find('(') 
      index2=name.find(')')
      
      if (index1>0 and index2>0): 
         #This name has parenthesis that we should deal with 
         newname=name[:index1] + '\('+name[index1+1:index2]+'\)'+name[index2+1:]
      
      #print("This is the name I am returning: " + newname)

      return newname    














