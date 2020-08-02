
import pickle
import os
import numpy as np
import subprocess


def combine_data(max_worker):

    print('we begin to combine the new data into the old data')

    # try to open the data pickle file
    try:
        # this is where we usually do the appending step
        # we want to combine data so we append new data to the end
        file_name_x = 'X_trainingAll.p'
        file_name_y = 'Y_trainingAll.p'

        total_data_x = pickle.load(open(file_name_x, "rb"))
        total_data_y = pickle.load(open(file_name_y, "rb"))

        for index in range(0, max_worker):
            cwd = os.getcwd()

            try:
                new_x_name = os.path.join(cwd, "X_training" + str(index) + ".p")
                new_y_name = os.path.join(cwd, "Y_training" + str(index) + ".p")

                new_x_data = pickle.load(open(new_x_name, "rb"))
                new_y_data = pickle.load(open(new_y_name, "rb"))

                record_this_data=True
                for key in total_data_y.keys():
                    temp = total_data_y[key]

                    if np.isnan(new_y_data[key]).all() == False:
                        temp.append(new_y_data[key])
                        total_data_y[key] = temp
                    else:
                        record_this_data=False

                if record_this_data==True:
                    for key in total_data_x.keys():
                        temp = total_data_x[key]
                        temp.append(new_x_data[key])
                        total_data_x[key] = temp


            except:
                pass

        # now, I save the data
        file_name_x = os.path.join(cwd, 'X_trainingAll.p')
        file_name_y = os.path.join(cwd, 'Y_trainingAll.p')

        pickle.dump(total_data_x, open(file_name_x, "wb"))
        pickle.dump(total_data_y, open(file_name_y, "wb"))



    except:
        # we only need to do this once at the very beginning

        success_index=None
        for index in range(0,max_worker):
            try:
                #check existence

                cwd = os.getcwd()
                file_name_x = os.path.join(cwd, "X_training"+str(index)+".p")
                file_name_y = os.path.join(cwd, "Y_training"+str(index)+".p")

                #we need to make sure the pickle is not empty
                total_data_x = pickle.load(open(file_name_x, "rb"))
                total_data_y = pickle.load(open(file_name_y, "rb"))

                for key in total_data_y.keys():
                    temp = total_data_y[key][0]


                    if np.isnan(temp).all() == False:

                        success_index = index
                        break

                    else:
                        break

                #now, we want to turn the data structure into a dictionary
                #with the appropriate keys. 
                for key in total_data_x.keys():
                    temp = total_data_x[key]
                    temp = [temp]
                    total_data_x[key]=temp
                for key in total_data_y.keys():
                    temp = total_data_y[key]
                    temp = [temp]
                    total_data_y[key]=temp

                if success_index!=None:
                    break


            except:
                pass

        print('success index is',success_index)

        if success_index!=None:

            for index in range(success_index+1, max_worker):
                try:
                    new_x_name = os.path.join(cwd, "X_training" + str(index) + ".p")
                    new_y_name = os.path.join(cwd, "Y_training" + str(index) + ".p")

                    new_x_data = pickle.load(open(new_x_name, "rb"))
                    new_y_data = pickle.load(open(new_y_name, "rb"))


                    record_this_data=True
                    for key in total_data_y.keys():
                        temp = total_data_y[key]

                        if np.isnan(new_y_data[key]).all()==False:

                            temp.append(new_y_data[key])

                            total_data_y[key] = temp
                        else:
                            record_this_data=False

                    if record_this_data==True:
                        for key in total_data_x.keys():
                            temp = total_data_x[key]
     
                            temp.append(new_x_data[key])
                            total_data_x[key] = temp

                except:
                    pass

        # now, I save the data
        file_name_x = os.path.join(cwd, 'X_trainingAll.p')
        file_name_y = os.path.join(cwd, 'Y_trainingAll.p')

        pickle.dump(total_data_x, open(file_name_x, "wb"))
        pickle.dump(total_data_y, open(file_name_y, "wb"))

    for index in range(0,max_worker):
        individual_x_name = os.path.join(cwd, "X_training" + str(index) + ".p")
        individual_y_name = os.path.join(cwd, "Y_training" + str(index) + ".p")

        subprocess.call('rm '+individual_x_name, shell=True)
        subprocess.call('rm '+individual_y_name, shell=True)


    #lastly, I will measure how many data points we have right now
    total_data_x = pickle.load(open(file_name_x, "rb"))
    total_data_y = pickle.load(open(file_name_y, "rb"))

    counter=0
    for key in total_data_y.keys():
        temp = total_data_y[key]
        counter=len(temp)
        break

    print('inside combine_data and the counter for good data is',counter)

    return counter