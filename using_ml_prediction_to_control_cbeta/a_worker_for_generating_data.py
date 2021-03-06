#Remove decision variables with zero range from being a feature
#Generate training data for Neural Network
import paretoutil as PU
import numpy as np
import os
import pickle
import json
import time
import sys


#Helper Function
def MakeIndividual(total_run_index, accelerator_file_location, FileName, XDic, Number=0):
    # The number of individual from Xdic
    BaseFront = PU.GetAFront(1, AddPath=accelerator_file_location)  # Get an example front from output
    for feature in XDic:  # replace values
        BaseFront[feature][1] = XDic[feature][Number]
    PU.MakeFrontFileFromFront(FileName, BaseFront, ID_number=total_run_index, FileClean=0)


def main_for_generating_data(input_index,cwd):
    #the idea is that the input of GPT simulations will be based on results of 
    #machine learning algorithms. 
    #the input will not be random but carefully choosen by ML algorithms. 
    
    accelerator_file_location = '/nfs/acc/user/zh296/inopt/examples/cbetaDL/'

    Nsamples = 1
    DecDic = PU.MakeDecDic(accelerator_file_location + 'optconf/docs/decisions.enxy.qb')
    ObjDic = PU.MakeObjDic(accelerator_file_location + 'optconf/docs/objectives.enxy.qb')
    ConDic = PU.MakeObjDic(accelerator_file_location + 'optconf/docs/constraints')

    # Features=['total_charge','sigma_xy','t_ellips','t_slope'] #these decisions will be used to make random inputs for training data
    Features = [feature for feature in DecDic]  # OR Use this line to make all decisions a feature
    XDic = {}  # features go here
    RemoveZeroRangeFeatures = 1  # don't-remove=0, anyother value will result in removing
 
    #instead of generating random input, we are going to use numbers generated by ML
    ml_suggested_input_file_name='/nfs/acc/user/zh296/cbeta_ml/test_combined_ml_model/using_combined_ml_model_to_do_prediction/combined__ml_control_result.p'
    ml_suggested_input_file = pickle.load(open(ml_suggested_input_file_name,"rb"))

    print('the input index is',int(input_index))
    print('the input feature based on ml will be',ml_suggested_input_file[int(input_index),:])

    feature_index=0
    for feature in Features:
        f_min = DecDic[feature][0]
        f_max = DecDic[feature][1]
        if f_min != f_max or RemoveZeroRangeFeatures == 0:
            #XDic[feature] = [np.random.uniform(f_min, f_max, Nsamples)[0]]
            XDic[feature] = [ml_suggested_input_file[int(input_index),:][feature_index]]

            feature_index+=1

    #Now run GPT to get out objectives
    var_param_dir = accelerator_file_location + 'optconf/var_param'
    AddPath = accelerator_file_location
    func_eval_location = os.path.join(cwd,'trial_func_eval.py')
    json_file_location = accelerator_file_location + 'TmpInd'+str(input_index)+'.p'

    YDic = {}  # targets go here
    for obj in ObjDic:
        YDic[obj] = None
    for j in range(Nsamples):
        print('drawing sample j', j)

        FileName = accelerator_file_location + 'tmp_ind'+str(input_index)+'.txt'
        MakeIndividual(input_index, accelerator_file_location, FileName, XDic, j)
        os.system(
            'python ' + func_eval_location + ' -f ' + FileName + ' -s' + json_file_location + ' -p ' + accelerator_file_location)

        try:
            #try to open the pickle file    
            TmpDic = pickle.load(open(json_file_location, "rb"))

            for obj in ObjDic:
                print(obj)
                YDic[obj] = [TmpDic['docs']['objectives'][obj]]
        except:
            pass


    print('finished one round of generating data and the y dictionary looks like')
    print(YDic)

    ##Save data with pickle
    x_file_name = os.path.join(cwd,"X_training" + str(input_index) + ".p")
    y_file_name = os.path.join(cwd,"Y_training" + str(input_index) + ".p")
    pickle.dump(XDic, open(x_file_name, "wb"))
    pickle.dump(YDic, open(y_file_name, "wb"))


if __name__ == '__main__':
    input_index = sys.argv[1]
    cwd = sys.argv[2]
    main_for_generating_data(input_index,cwd)






