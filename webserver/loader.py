import os
from collections import Counter

import numpy as np
from keras.engine.saving import load_model


def load_local_model(model_path):
    model = load_model(model_path)
    return model


def predict_class_audio(MFCCs):
    '''
    Predict class based on MFCC samples
    :param MFCCs: Numpy array of MFCCs
    :param model: Trained model
    :return: Predicted class of MFCC segment group
    '''
    global model
    MFCCs = MFCCs.reshape(MFCCs.shape[0], MFCCs.shape[1], MFCCs.shape[2], 1)
    y_predicted = model.predict_classes(MFCCs, verbose=0)
    return Counter(list(y_predicted)).most_common(1)[0][0]


EXP_TYPE = "usa_english_speakers"
# EXP_NUM = "4089305544804f5689faf7cce3e84258"
EXP_NUM = "d2225d2dd7af486cb08ea10bc127bf09"

# load once for the application
model_path = os.path.join("../saved_models",
                          EXP_TYPE, EXP_NUM, "model.h5")

model = load_local_model(model_path)

# BUG fix - initializing the modle with an empty vector
model.predict(np.zeros((1, 13, 30, 1)))