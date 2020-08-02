import sys
import math
import re
import os
from optparse import OptionParser
import json

# import pisapy
from pisapy.eval_parser import eval_parser
from pisapy.zuhao_gpt_distgen_eval import gpt_distgen_eval
from pisapy.tools import vprint
from pisapy.gpt import calc_statistical_data

import time
import numpy
import shutil
import subprocess
import pickle

# ******************************************************************************************
# This is the user defined MERIT function (Objectives, Constraints), edit here
# ******************************************************************************************
def user_merit_fun(variables, data):
    print('we are in the merits function part of the trial func eval')
    print('line 0')
    merits = {}
    merits["error"] = False

    NSTART = variables["particle_count"]  # Number of particles at the start of tracking

    try:
        print('we are in the merits function part of the trial func eval')
        print('line 1')
        # We the need merit function computation here...for now, will just do the minimum work
        # Analyze last screen phase space output

        HSLIT_z = 12.35187788493322  # screen Position, this screen only cares about x direction stuff
        VSLIT_z = 12.41949269277345  #for y direction stufff

        screenHslit = None
        screenVslit = None

        for screen in data.pdata:
            z = screen["z"]
            if (numpy.abs(z.mean() - HSLIT_z) < 1e-6):
                screenHslit = screen
            if (numpy.abs(z.mean() - VSLIT_z) < 1e-6):
                screenVslit = screen


        if (screenHslit is None or screenVslit is None):
            raise ValueError("Could not find the phase space measurements screens")

        enx = screenHslit["twiss"]["x"]["en"] * 1e6  # [um]
        eny = screenVslit["twiss"]["y"]["en"] * 1e6  # [um]

        stdtx = screenHslit["t"].std() * 1e12
        stdty = screenVslit["t"].std() * 1e12

        stdxy = 0.5 * (screenVslit["x"].std() + screenVslit["y"].std()) * 1e3  # [mm]
        qb = numpy.abs(variables["total_charge"])  # [pC]

        print('those are the settings in the twiss x of screen x ')
        for keys in screenHslit['twiss']["x"].keys():
            print(keys)

        print(' ')
        print('those are the options in the screen')
        for keys in screenHslit.keys():
            print(keys)

        merits = {}
        merits["qb"] = qb
        merits["max_enxy"] = numpy.max([enx, eny])
        merits["max_stdt"] = numpy.max([stdtx, stdty])
        merits["stdxy"] = stdxy

        NSTART = variables["particle_count"]
        NLOST = NSTART - len(screenVslit["t"])
        merits["NLOST"] = NLOST

        # Compute statistical data as a function of t,s
        tstat, pstat = calc_statistical_data(data, "./", use_ref=True, s_interpolation=True)
        merits["tstat"] = tstat
        merits["pstat"] = pstat

        #here, Zuhao add some feature
        merits["twiss_x_alpha"] = screenHslit["twiss"]["x"]["alpha"]
        merits["twiss_x_beta"] = screenHslit["twiss"]["x"]["beta"]
        merits["twiss_x_gamma"] = screenHslit['twiss']["x"]["gamma"]

        merits["twiss_y_alpha"] = screenVslit["twiss"]["y"]["alpha"]
        merits["twiss_y_beta"] = screenVslit["twiss"]["y"]["beta"]
        merits["twiss_y_gamma"] = screenVslit['twiss']["y"]["gamma"]

        merits["x"] = screenHslit['x']
        merits["px"] = screenHslit['GBx']
        merits["y"] = screenVslit['y']
        merits["py"] = screenVslit['GBy']

        print('we are in the trial func eval and we just want to make sure the merits funtions are not empty')
        print('this is merits of twiss x alpha',merits["twiss_x_alpha"])


    except Exception as ex:
        print('ERROR occured in user_merit_fun:', str(ex))
        merits["error"] = True


    return merits


# ******************************************************************************************
# The main function is called by the APISA optimizer (User should not modify)
# ******************************************************************************************
def main():
    # ---------------------------------------------------------------------------------------
    # Parse Input Content
    # ---------------------------------------------------------------------------------------
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", default="",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-v", dest="verbose", default=False, help="Print short status messages to stdout")
    parser.add_option("-s", dest="save_ind", default=None, help="Save the individial to a json file")
    parser.add_option("-p", dest="add_path", default=None, help="additional path info can be inserted into here")

    (options, args) = parser.parse_args()

    eval_file = options.filename
    verbose = int(options.verbose)
    save_ind_file = options.save_ind

    # Get the path where the funcion is called
    home_dir = os.path.dirname(os.path.realpath(__file__))
    # ---------------------------------------------------------------------------------------


    # ---------------------------------------------------------------------------------------
    # Form the individual from file
    # ---------------------------------------------------------------------------------------
    vprint("Loading evaluation input file '" + eval_file + "': ", verbose > 0, 0, False)
    eval_file_data = eval_parser(eval_file, False)  # Parse evaluation input file
    docs = eval_file_data.get_DOC_dict()  # retrieve the ID & dec/obj/con data
    vprint("done.", verbose > 0, 0, True)

    ind = {}
    ind["docs"] = docs
    ind["ID"] = docs["ID"]
    ind["NODE"] = eval_file_data.get_node_name()
    ind["FLAGS"] = eval_file_data.get_flag_dict()
    ind["PATHS"] = eval_file_data.get_path_dict()

    clean_up = False
    if ("FILE_CLEANUP" in ind["FLAGS"].keys()):
        clean_up = bool(ind["FLAGS"]["FILE_CLEANUP"])

    if ("TEMP_DIR" not in ind["PATHS"].keys()):
        ind["PATHS"]["TEMP_DIR"] = "tmp/"
    temp_dir = ind["PATHS"]["TEMP_DIR"]

    if ("TEMPLATE_DIR" not in ind["PATHS"].keys()):
        ind["PATHS"]["TEMPLATE_DIR"] = "template/"

    try:
        template_dir = options.add_path + ind["PATHS"]["TEMPLATE_DIR"]
    except:
        template_dir = ind["PATHS"]["TEMPLATE_DIR"]

    try:
        work_dir = options.add_path + temp_dir + "eval." + ind["ID"]
    except:
        work_dir = temp_dir + "eval." + ind["ID"]

    id_num_str = "%09d" % int(ind["ID"])
    id_str = id_num_str + "." + ind["NODE"]
    # ---------------------------------------------------------------------------------------


    # ---------------------------------------------------------------------------------------
    # Run the GPT evaluation, retrieve data and send back to optimizer
    # ---------------------------------------------------------------------------------------
    print('begin to do the zuhao gpt_distgen_eval')
    output = gpt_distgen_eval(ind["docs"]["decisions"],
                              autophase=True,
                              workdir=work_dir,
                              template_dir=template_dir,
                              verbose=verbose,
                              do_cleanup=clean_up,
                              merit_fun=user_merit_fun,
                              get_time_of_flight=True, )

    docs_update = docs;
    if (not output["error"]):  # If no errors, update the docs

        for obj in docs_update["objectives"].keys():
            obj_found = False
            if obj in output["merits"].keys():
                docs_update["objectives"][obj] = output["merits"][obj]
                obj_found = True
            if (not obj_found):
                raise ValueError("Objective " + obj + " was not found in the function merits.")

        for con in docs_update["constraints"]:
            con_found = False
            if con in output["merits"].keys():
                docs_update["constraints"][con] = output["merits"][con]
                con_found = True
            if (not con_found):
                raise ValueError("Constraint " + con + " was not found in the function merits.")


    # print the return file to optimizer
    os.chdir(home_dir)  # in case a relative path to temporary directory was specified
    print('inside trial func eval and temp_dir is',temp_dir)
    try:
        eval_file_data.print_eval(options.add_path + temp_dir + "eval." + id_str + ".done.txt", docs_update)
    except:
        eval_file_data.print_eval(temp_dir + "eval." + id_str + ".done.txt", docs_update)
    # ---------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------
    # Save the ind to json
    print('inside trial func eval and save_ind_file is', save_ind_file)

    if (save_ind_file is not None):
        vprint("Saving individual to json file 'template/ind.template.json': ", verbose > 0, 1, False)
        pickle.dump(ind, open(save_ind_file, "wb"))
        vprint("done.", verbose > 0, 0, True)


# ----------------------------------------------------------------------------
#   This allows the main function to be at the beginning of the file
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    main()


