import os
import pickle
from a_round_of_procedure import a_round_of_procedure

if __name__ == '__main__':

    #ml_suggested_input_file_name = '/nfs/acc/user/zh296/cbeta_ml/test_ml_model/test_ml_model_against_gpt/ml_control_result.p'
    #ml_suggested_input_file_name = '/nfs/acc/user/zh296/cbeta_ml/test_combined_ml_model/using_combined_ml_model_to_do_prediction/combined__ml_control_result.p'
    ml_suggested_input_file_name = '/nfs/acc/user/zh296/cbeta_ml/gpt_run_based_on_ml_prediction/callback_seperate_ml_control_result.p'
    ml_suggested_input_file = pickle.load(open(ml_suggested_input_file_name, "rb"))

    simultaneous_worker=ml_suggested_input_file.shape[0]

    #the first step we do is to generate the sh files
    cwd = os.getcwd()

    wait_minute=6


    target_data=50
    total_good_data_so_far=0


    while total_good_data_so_far<=target_data:

        total_good_data_so_far = a_round_of_procedure(cwd,simultaneous_worker,wait_minute)

        print('we are in main, and we are abount to begin another round of worker')
        print('our target is',target_data)
        print('so far, we have this many good data',total_good_data_so_far)
        print('finished percentage',total_good_data_so_far/target_data)

