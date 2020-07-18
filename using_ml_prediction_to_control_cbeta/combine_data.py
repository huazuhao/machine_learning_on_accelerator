
import pickle
import os
import numpy as np
import subprocess


def combine_data(max_worker):

    print('we begin to combine the new data into the old data')

    # try to open the data pickle file
    try:
        # this is where we usually do the appending
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

                    # print('we are trying to find the first success output file')
                    # print(temp)
                    # print('type is',type(temp))
                    # print('this type should be a float')

                    if np.isnan(temp).all() == False:

                        success_index = index
                        # print('we have found a success output file')
                        # print('the index is',index)
                        break

                    else:
                        break

                #now, I need to do some type of data structure engineering
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

                    #print('we are in combine data')
                    #print('the file name is',new_y_name)
                    #print('the stuff inside is',new_y_data)

                    record_this_data=True
                    for key in total_data_y.keys():
                        temp = total_data_y[key]

                        # print('we are trying to retrieve a new data')
                        # print('this data is called',key)
                        # print('data type is',type(new_y_data[key]))
                        # print('this data type should be a list')
                        # print('this data actually is',new_y_data[key])

                        if np.isnan(new_y_data[key]).all()==False:
                            # print('we found a good data and the file name is',new_y_name)
                            #
                            # print('temp is',temp)
                            # print('type of temp is',type(temp))
                            # print('the above type should be a list')
                            # print('the new stuff is',new_y_data[key])
                            # print('type of new_y_data[key] is',type(new_y_data[key]))

                            temp.append(new_y_data[key])

                            #print('after concatenating the data, the data looks like')
                            #print(temp)

                            total_data_y[key] = temp
                        else:
                            record_this_data=False

                    if record_this_data==True:
                        #print('we are now trying to append the x data for the first time')
                        for key in total_data_x.keys():
                            temp = total_data_x[key]
                            #print('the x data before appending is',temp)
                            #print('the type of the data right now should be a list and it is',type(temp))
                            #print('the new x data is',new_x_data[key])
                            temp.append(new_x_data[key])
                            #print('the x data after appending is',temp)
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