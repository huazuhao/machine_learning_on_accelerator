# machine_learning_on_accelerator
Applying neural nets for a surrogate model of the cbeta particle accelerator.

A summary of the result is in the pdf file called control_cbeta_with_ml_summary.pdf.


First, we use simulation data to train a neural network.
The code for this step is in training_neural_nets.

Then, we use the trained neural network to simulate the control process of cbeta. 
The code for this second step is in using_ml_prediction_to_control_cbeta.

Lastly, we need to check the quality of the control process done by the neural network. 
The code for this third step is in test_ml_result.
