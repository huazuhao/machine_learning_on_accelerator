
import time
from write_sh_files import write_sh_file_and_submit
import numpy as np
import pickle
import os
import subprocess
from combine_data import combine_data

def one_round_of_simulation(cwd,simultaneous_worker,wait_minute):

    #the first step we do is to generate the sh files
    write_sh_file_and_submit(simultaneous_worker,cwd)

    #the second step is to check whether the final data is generated
    start_time = int(time.time())
    finished_generating_data=False
    succeed=np.zeros((simultaneous_worker,1))

    while not finished_generating_data:
        for index in range(simultaneous_worker):
            x_file_name = os.path.join(cwd, "X_training" + str(index) + ".p")
            y_file_name = os.path.join(cwd, "Y_training" + str(index) + ".p")

            try:
                #try to open those files
                #as sometimes the files can still not be generated
                pickle.load(open(x_file_name, "rb"))
                pickle.load(open(y_file_name, "rb"))

                succeed[index,0]=1

            except:
                pass

        time.sleep(15)

        if sum(sum(succeed))==simultaneous_worker:
            finished_generating_data=True
            print('finished this round of simulation in normal end')
            print(' ')

        print('for this round of simulation, the time has elapsed this much',int(time.time())-start_time,'seconds')

        if int(time.time())-start_time>60*wait_minute:
            print('stop this round of simulation because time constraint')
            subprocess.call('qdel -u zh296', shell=True)
            finished_generating_data = True

    #the third step is to increase the data
    # append new data to the total pickle file
    total_good_data_so_far = combine_data(simultaneous_worker)

    return total_good_data_so_far
