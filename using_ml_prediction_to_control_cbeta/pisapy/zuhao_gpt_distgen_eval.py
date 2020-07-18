import sys
import math
import re
import os
from optparse import OptionParser

from pisapy.eval_parser import eval_parser 
from pisapy.inputfile_writer import inputfile_writer
from pisapy.gpt_dist_reader import gpt_dist_reader
from pisapy.gpt_phasing import gpt_phasing
from pisapy.tools import vprint

import time
import numpy 
import shutil
import subprocess

# Default example, for testing only
TEMP_DIR = "./test"
TEMPLATE_DIR = "/nfs/acc/temp/cg248/inopt/templates/dcgun/"

def user_merit_fun(variables,data):

   merits = {}
   merits["error"]=False

   try:

      # We the need merit function computation here...for now, will just do the minimum work
      # Analyze last screen phase space output

      screen = data.pdata[-1] 
      stdx = screen["std"]["x"]
      stdy = screen["std"]["y"] 
      enx = screen["twiss"]["x"]["en"]*1e6   		# [um]
      eny = screen["twiss"]["y"]["en"]*1e6   		# [um]
      stdxy = 0.5*(stdx + stdy)*1e3    			# [mm]
      qb = numpy.abs(variables["total_charge"])		# [pC]

      print('we are inside merits fun in the distgen eval')
      print('those are the available options')
      for keys in screen.keys():
         print(keys)
            
      merits = {}
      merits["qb"] = qb
      merits["max_enxy"] = numpy.max([enx,eny])
      merits["stdxy"] = stdxy

   except Exception as ex:
      print('ERROR occured in user_merit_fun:',str(ex))
      merits["error"]=True

   return merits

#******************************************************************************************
# The main function is called by the APISA optimizer, here this is for testing 
#******************************************************************************************
def main():
 
   #---------------------------------------------------------------------------------------
   # Parse Input Content
   #---------------------------------------------------------------------------------------
   parser = OptionParser()
   parser.add_option("-f", "--file", dest="filename", default="", 
                      help="write report to FILE", metavar="FILE")
   parser.add_option("-v",dest="verbose", default=False,help="Print short status messages to stdout")

   (options, args) = parser.parse_args()

   eval_file = options.filename
   verbose = int(options.verbose)      
   #---------------------------------------------------------------------------------------


   #--------------------------------------------------------------------------------------- 
   # Form the individual from file
   #---------------------------------------------------------------------------------------
   vprint("Loading evaluation input file '" + eval_file +"': ", verbose>0, 0, False)
   eval_file_data = eparser.eval_parser(eval_file, False)  # Parse evaluation input file
   docs = eval_file_data.get_DOC_dict()            # retrieve the ID & dec/obj/con data  
   vprint("done.", verbose>0, 0, True)   

   ind={}
   ind["docs"]=docs
   ind["ID"]=docs["ID"]       
   ind["NODE"]=eval_file_data.get_node_name()     
   ind["FLAGS"]=eval_file_data.get_flag_dict()
   ind["PATHS"]=eval_file_data.get_path_dict()

   clean_up = False
   if("FILE_CLEANUP" in ind["FLAGS"].keys()):
     clean_up = bool(ind["FLAGS"]["FILE_CLEANUP"])

   temp_dir = ind["PATHS"]["TEMP_DIR"]
   template_dir = ind["PATHS"]["TEMPLATE_DIR"]
   work_dir = temp_dir + "eval."+ind["ID"]

   id_num_str = "%09d" % int(ind["ID"])
   id_str = id_num_str +"."+ind["NODE"]
   #---------------------------------------------------------------------------------------


   #--------------------------------------------------------------------------------------- 
   # Run the GPT evaluation, retrieve data and send back to optimizer
   #---------------------------------------------------------------------------------------
   output = gpt_distgen_eval(ind["docs"]["decisions"], autophase = True, workdir=work_dir, template_dir=template_dir, verbose=verbose, do_cleanup=clean_up)
   docs_update = docs;
   if(not output["error"]): # If no errors, update the docs 
      
      for name in output["merits"].keys():
         if(name in docs_update["objectives"].keys()):
            docs_update["objectives"][name] = output["merits"][name]
         if(name in docs_update["constraints"].keys()):
            docs_update["constraints"][name] = output["merits"][name]
      
   # print the return file to optimizer
   eval_file_data.print_eval(temp_dir+"eval."+id_str+".done.txt",docs_update)
   #---------------------------------------------------------------------------------------


def gpt_distgen_eval(variables,                  # Specifies the individual genes to simulate
                     autophase = True,           # Phase RF cavities in the GPT file
                     workdir="./test/",          # Work area to create eval folder(s)
                     template_dir="template",    # GPT/Distgen template folder
                     verbose=1,                  # Verbose printing to screen, 1 -> verbose; 2 -> very verbose
                     do_cleanup=True,            # Remove all temp files for run
                     merit_fun=user_merit_fun,   # Pointer to user merit function
                     gpt_exe="gpt",              # Can specify an absolute path, default assumes gpt in your path 
                     distgen_exe="distgen",      # Can specify an absolute path, default assumes distgen in your path
                     get_time_of_flight=True,    # Performs single particle tracking through the GPT file to get an estimate of the time needed for tracking to the last user specified screen
                     data_archive=None,          # Path to desired data archive
                     timeout=None
                     ):
   print('inside gpt_distgen_eval of zuhao gpt distgen_eval')
   if(timeout is None): # If not supplied, default to infinity
     timeout=1e9

   # Get the path where the funcion is called
   home_dir = os.path.dirname(os.path.realpath(__file__))  

   vprint("GPT w/distgen Evaluation...", verbose>0, 0, True)

   # General GPT/Distgen paths/files:
   output={}
   output["error"]=False
   output["verbose"]=verbose
   output["template_dir"]= template_dir
   output["run_directory"] = workdir
   output["data_archive"]=data_archive
   output["distgen"] = distgen_exe
   output["gpt"] = gpt_exe
  
   #output["auto_phase"]=True
   output["distgen_on"]=True
   output["run_on"]=True
   error_flag = False

   vprint("Copying template dir '"+template_dir+"': ", verbose>0, 1, False)
   try:
     print('inside zuhao gpt distgen eval and we are trying to make tmp directory')
     print('template_dir is',template_dir)
     print('workdir is',workdir)
     shutil.copytree(template_dir, workdir, symlinks=True)
     print('finished the step of shutil.copytree')
     vprint("done", verbose>0, 0, True)
   except Exception as ex:
     vprint("Could not make working directory, directory already exists?", True, 1, True)
   
   # Change work directory to the temp folder
   os.chdir(workdir)

   #***************************************************************************************
   # RUN EVALUATION
   #***************************************************************************************
   # Make new input files
   output["distgen_input_file"] = "distgen.in"
   output["gpt_template_file"] = "gpt.in"
   output["gpt_output_file_base"] = "gpt.out."
   output["distgen_input_file"]="distgen.in"
   output["gpt_input_file"]="gpt.in"

   # Update the input files...
   distgen_writer = inputfile_writer(output["distgen_input_file"],True,["#"," "," "])                                # read in and store distgen template file   
   gpt_writer = inputfile_writer(output["gpt_template_file"],True,["#","=",";"])                                     # read in and store gpt template file   
   distgen_writer,gpt_writer,error_flag=update_input_file_settings(variables,distgen_writer,gpt_writer)           # update all general variable settings
   
   # Write files, save them to output structure
   output["distgen.in"] = distgen_writer.print_new_file(output["distgen_input_file"])
   output["gpt.in"] = gpt_writer.print_new_file(output["gpt_template_file"])

   #----------------------------------------------
   # CALL DISTGEN EXECUTIBLE:
   #----------------------------------------------
   if not error_flag:
      vprint("Running distgen with '" + output["distgen_input_file"] +"': ", verbose>0, 1, False) 

      if(output["verbose"]==2):
         distgen_cmd = output["distgen"]+" -gpt -v "+output["distgen_input_file"]
      else:
         distgen_cmd = output["distgen"]+" -gpt "+output["distgen_input_file"]
  
      try:
         distgen_call = os.system(distgen_cmd)
         vprint("done.", verbose>0, 0, True) 
      except Exception as ex:
         vprint("Exception occured while running distgen: "+str(ex), True, 0 ,True)
         output["error"]=True
         output["exception"]=str(ex)
         return output
   #----------------------------------------------


   #----------------------------------------------
   # PHASE THE GPT FILE
   #----------------------------------------------
   print('we are in the phase gpt file part')
   if(autophase and not error_flag):
      try:
         tstart = time.time()  
         output["gpt.phased.in"]=gpt_phasing(output["gpt_template_file"], path_to_gpt_bin="", verbose=(verbose>0), debug_flag=False)
         output["gpt_phased_file"]="gpt.phased.in" 
         tstop = time.time()
         vprint("Time phasing: "+"{0:.2f}".format(tstop-tstart) + " sec.",verbose>0,1,True)
      except Exception as ex:
         vprint("Exception occured during phasing routine: "+str(ex), True, 0 ,True)
         output["error"]=True
         output["exception"]=str(ex)
         return output
   #----------------------------------------------

   if(get_time_of_flight):

      output["gpt_tof_file"] = "gpt.phased.tof.in"
      output["gpt_tof_batch_file"]="run."+output["gpt_tof_file"]+".sh" 
      output["gpt_tof_output_file_base"] = "gpt.phased.tof.out."
 
      vprint("",True, 0 ,True)
      vprint("Computing time of flight to last screen using single particle tracking:", verbose>0, 1 ,True)
      gpt_writer = inputfile_writer(output["gpt_phased_file"],True,["#","=",";"])  
  
      output["gpt_tof_file"] = output["gpt_phased_file"][:-3] + ".tof.in"
      output["gpt_tof_output_file_base"] = output["gpt_tof_file"][:-3]+".out."

      gpt_writer.set_variable_assignment("single_particle",1)
      gpt_writer.set_variable_assignment("space_charge",0)
      output[output["gpt_tof_file"]] = gpt_writer.print_new_file(output["gpt_tof_file"])
     
      try:
         vprint("Writing new gpt batch file -> '" + output["gpt_tof_batch_file"], verbose, 1, True)
         # Force verbose, so that run_gpt can catch all output
         output[output["gpt_tof_batch_file"]] = write_gpt_batch_file(gpt_exe, output["gpt_tof_file"], output["gpt_tof_batch_file"],verbose=True)
      except Exception as ex:
         print("Exception occured while writing the time of flight gpt batch file: "+str(ex),True, 0 ,True)
         output["error"]=True
         output["exception"]=str(ex) 
         return output
      
      try:
         
         error_tof = run_gpt(output["gpt_tof_batch_file"],kill_on_warning=True,verbose=verbose,timeout=timeout)
         data = gpt_dist_reader([output["gpt_tof_output_file_base"]+"txt"],[0,1,0],0,verbose>1,True)
         tof = data.pdata[-1]["t"].mean()
         vprint("Time of flight to last user defined screen: "+str(tof)+" sec.",verbose>0,1,True)

      except Exception as ex:
         print("Exception occured while running GPT: "+str(ex), True, 0 ,True)
         output["error"]=True
         output["exception"]=str(ex)
         return output 
      vprint("...done.", verbose>0, 1 ,True)

   if(not output["error"]): # Do the run

      #----------------------------------------------
      # RUN GPT
      #----------------------------------------------
      print('we are in the run gpt part')
      output["gpt_batch_file"]="run.gpt.in.sh"

      gpt_writer = inputfile_writer(output["gpt_phased_file"],True,["#","=",";"]) 
      if(get_time_of_flight):
         gpt_writer.set_variable_assignment("tmax",tof*1.2)

      output["gpt.in"] = gpt_writer.print_new_file(output["gpt_input_file"]) 
      vprint("Writing new gpt batch file -> '" + output["gpt_batch_file"] +"': ", verbose, 1, False)

      try:
         print('checking 1')
         output["gpt_input_batch_file"] = "run."+output["gpt_input_file"]+".sh"
          # Force verbose, so that run_gpt can catch all output
         output[output["gpt_batch_file"]] = write_gpt_batch_file(gpt_exe, output["gpt_input_file"], output["gpt_input_batch_file"],verbose=True)
         vprint("done.", verbose>0, 0, True)
      except Exception as ex:
         print('checking 2')
         print("Exception occured while writing the gpt batch file: "+str(ex),True, 0 ,True)
         output["error"]=True
         output["exception"]=str(ex) 
         return output
   
      try:
         print('checking 3')
         run_time,gpt_exception = run_gpt(output["gpt_batch_file"],kill_on_warning=True,verbose=verbose,timeout=timeout)
         output["gpt_run_time"]=run_time
         if(gpt_exception is not None):
           print('there is some gpt exception, and the exceptions are')
           print(gpt_exception)
           output["error"]=True
           output["exception"]=gpt_exception
           print('checking 4')
           return output
      except Exception as ex:
         print('checking 5')
         print("Exception occured while running GPT: "+str(ex), True, 0 ,True)
         output["error"]=True
         output["exception"]=str(ex)
         return output 
      #---------------------------------------------- 


      #------------------------------------------------
      # LOAD GPT DATA AND COMPUTE MERITS
      #------------------------------------------------
      print(' we are in the load gpt data and compute merits part')
      if(not output["error"]):
         data = gpt_dist_reader([output["gpt_output_file_base"]+"txt"],[0,1,0],0,verbose>1,True)
         output["merits"] = merit_fun(variables,data)
         #print('we are inside zuhao gpt distgen eval and the load gpt data and compute merits part')
         #print(output["merits"])
      #----------------------------------------------
   

   #----------------------------------------------
   # ARCHIVE DATA AND DO ALL FILE CLEAN UP
   #----------------------------------------------
   if(data_archive is not None):
 
      current_path = os.getcwd()
      run_folder = os.path.basename(os.path.normpath(current_path))
      new_dir = data_archive + run_folder
      vprint("Archiving run data -> '" + new_dir +"': ", verbose>0, 1, True)
      try: 
         shutil.copytree(current_path, new_dir, symlinks=True)
         vprint("...done.", verbose>0, 1, True) 
      except Exception as ex:
        print("Warning, could not archive data -> "+str(ex))


   if(do_cleanup):  # Delete all run files:
      vprint("Removing workdir tree '" + workdir +"'", verbose>0, 1, False) 
      subprocess.call(["rm","-rf",workdir])
      vprint("done.", verbose>0, 0, True)
   #----------------------------------------------

   # Return the CWD 
   os.chdir(home_dir)

   # Finished $
   return output
  
# Helper functions
def write_gpt_batch_file(gpt_exe,gpt_file, batch_file_name, gpt="gpt", verbose=False):
   if(gpt_exe != "gpt"):
      gpt_path = gpt_exe[:-3]   
   else:
      gpt_path = ""

   gpt_output_file_base = gpt_file[:-3]+".out."
   batch_file = [] 

   if(verbose):
      batch_file.append(gpt_exe + " -v -j1 -o "+gpt_output_file_base+"gdf "+gpt_file +"\n")
   else: 
      batch_file.append(gpt_exe + " -j1 -o "+gpt_output_file_base+"gdf "+gpt_file+"\n")

   batch_file.append(gpt_path+"gdf2a -w 16 "+gpt_output_file_base+"gdf"+" > "+gpt_output_file_base+"txt"+"\n")

   f=open(batch_file_name,'w')
   f.writelines(batch_file)
   f.close()

   return batch_file

def get_gpt_variable_names():

      gpt_var_names = {}
      gpt_var_names["p"]="position numpar Q avgG avgp avgx avgy avgz stdx stdy stdz stdG stdt nemixrms nemiyrms nemizrms CSalphax CSbetax CSgammax CSalphay CSbetay CSgammay CSalphaz CSbetaz CSgammaz angref stdxref stdyref stdzref stdBxref stdByref stdBzref nemixrmsref nemiyrmsref nemizrmsref maxnemixyrmsref dispx dispy dispz dispBx dispBy dispBz"

      gpt_var_names["t"]="time Q numpar avgG avgp avgx avgy avgz stdx stdy stdz nemixrms nemiyrms nemizrms stdG CSalphax CSbetax CSgammax CSalphay CSbetay CSgammay CSalphaz CSbetaz CSgammaz avgBx avgBy avgBz stdBx stdBy stdBz angref stdxref stdyref stdzref stdBxref stdByref stdBzref nemixrmsref nemiyrmsref nemizrmsref maxnemixyrmsref dispx dispBx dispy dispBy dispz dispBz"
      return gpt_var_names

def update_input_file_settings(replacements,distgen_writer,gpt_writer):

   error_flag = False
   for var in replacements.keys():

      variable_in_gpt_file = gpt_writer.check_for_parameter(var)
      variable_in_distgen_file = distgen_writer.check_for_parameter(var)

    #  if (variable_in_gpt_file & variable_in_distgen_file):
    #     vprint("update_input_file_settings::ERROR -> decision variable '"+ var +"' found in both the gpt and distgen input files, returning null evaluation!",True,1,True)# output["verbose"],0,True)
    #     error_flag = True
    #     break
      if not (variable_in_gpt_file or variable_in_distgen_file):
         vprint("update_input_file_settings::ERROR -> decision variable '"+ var +"' not found in either the gpt and distgen input files, returning null evaluation!",True,1,True)#, output["verbose"],0,True)
         error_flag = True
         break
   
      if variable_in_gpt_file:
         gpt_writer.set_variable_assignment(var,replacements[var])
      if variable_in_distgen_file:
         distgen_writer.set_variable_assignment(var,replacements[var])

   return (distgen_writer,gpt_writer,error_flag)

def run_gpt(batch_file,kill_on_warning=True,verbose=False,timeout=1e6):

   vprint("Running GPT...", verbose>0, 1, True)
   tstart = time.time()
   
   exception = None
   run_time = 0
   all_good = True 

   gpt_warnings = ["gpt: Spacecharge3Dmesh:", "Error:"];
   gpt_batch_cmd = ["sh", batch_file];
   process = subprocess.Popen(gpt_batch_cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)

   while(all_good):

      pout = (process.stderr.readline()).decode("utf-8")
      if(pout !="" and verbose>1):
         print(pout.strip()) 

      if(pout == '' and process.poll() is not None):
         break

      if(time.time()-tstart > timeout): 
        process.terminate()
        exception = "run timed out"
        break

      if(kill_on_warning):
         for warning in gpt_warnings:
            if(warning in pout):
               process.terminate()
               exception = pout               
               break

   rc = process.poll()

   tstop = time.time()
   vprint("done. Time ellapsed: "+"{0:.2f}".format(tstop-tstart) + " sec.", verbose>0, 1, True)  
   run_time=tstop-tstart

   return run_time,exception

# ---------------------------------------------------------------------------- 
#   This allows the main function to be at the beginning of the file
# ---------------------------------------------------------------------------- 
if __name__ == '__main__':
    main()


