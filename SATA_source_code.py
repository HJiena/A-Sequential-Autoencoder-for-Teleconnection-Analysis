
"""
© 2020 Jiena He and J. Ronald Eastman

"""

import os
import shutil
import numpy as np
import pandas as pd
from osgeo import gdal
import win32com.client
from natsort import natsorted
from tensorflow.keras import layers
from tensorflow.keras import models 
from tensorflow.keras import Sequential
from tensorflow.keras import optimizers 
from tensorflow.keras import constraints 


###### Autoencoedr Part ######
def SATA_autoencoder(train_data,encoding_dim,k,input_dim,nodename,SATA_out,epochs):
  
    encoded = layers.Dense(encoding_dim, 
                activation="linear",
                input_shape=(input_dim,), 
                use_bias=False, 
                name ='layer1') 

    decoded =layers.Dense(input_dim,
                activation="linear",
                use_bias = False,
                kernel_constraint=constraints.UnitNorm(axis=1),
                name='layer2')
    autoencoder = Sequential()
    autoencoder.add(encoded)
    autoencoder.add(decoded)

    optimizer = optimizers.Adam(lr = 0.0001,beta_1=0.99, beta_2=0.999)
    autoencoder.compile(optimizer, loss='MSE')

    autoencoder.summary()

    history = autoencoder.fit(train_data, train_data,
                              epochs=epochs,
                              batch_size=32,
                              shuffle=True)

    #%matplotlib inline
    import matplotlib.pyplot as plt
    loss = history.history['loss']
    epochs = range(1, len(loss) + 1)
    plt.plot(epochs, loss, 'b', label='Training loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
    encoder = autoencoder.get_layer('layer1')
    encoder = models.Model(inputs = autoencoder.input, outputs = encoder.output)
    encoded_imgs = encoder.predict(train_data)
    print(encoded_imgs.shape)


    decoded_imgs = autoencoder.predict(train_data)
    print(decoded_imgs.shape)

    # how many digits will display
    n_nodes = encoding_dim 
    n = encoded_imgs.shape[0]
    print(n)
    dict_encode = {}

    for i in range(encoding_dim):
        y = []
        for j in range(n):
            y.append(encoded_imgs[j][i])
            dict_encode[i] = y
            squence = np.arange(1,train_data.shape[0]+1,1)
            squence = squence.tolist()

    fig, ax = plt.subplots(1,n_nodes,figsize=(20,10))
    if n_nodes < 2:
        x =range(0,n) 
        plt.plot(x, dict_encode[i], 'r', label='N'+str(i+1))
        dataframe = pd.DataFrame({'1':squence,'2':dict_encode[i]})
        dataframe.to_csv(SATA_out +".csv",header = 0,index =0, date_format = '%d %.12f')
        plt.legend()
    return 


###### Call TerrSet ######
def Call_TerrSet(node_path, residual_prefix,TimrSeries_name):
    
    ###### Step 1 ######
    ### Command line for CSVtoAVL Module: Convert .csv file to .avl file
    comd_csv2avl = '2' + '*' +'1'+'*'+ node_path + ".csv" +'*' + node_path +'.avl'
    IDRISI32.RunModule('CSV2AVL',comd_csv2avl,1,'','','','',1 )


    ###### Step 2 ######
    ### Command line for R square and R in CORRELATE Module
    comd_cor_rsqrt =  TimrSeries_name +'*'+ node_path +'*'+node_path +'*'+'11'+'*'+'1'+'*'+'none'   
    IDRISI32.RunModule('CORRELATE',comd_cor_rsqrt,1,'','','','',1 )

    ###### Step 3 ######
    ### Command line for TOPRANK Module
    comd_top = node_path + '_R2' +'*'+ 'none' +'*'+ '2' +'*'+'0.5'+'*'+node_path+ '_top'+'*'+'2'                  
    IDRISI32.RunModule('TOPRANK',comd_top,1,'','','','',1)

    ###### Step 4 ######
    ### Command line for PROFILE Module
    comd_prof = '2'+'*'+node_path+ '_top'  +'*'+  TimrSeries_name  +'*'+ '1 ' +'*'+ 'y'+'*'+ node_path +'_profiledottsf'  +'*'+  '1' + '*' + node_path + '_R.rst'
    IDRISI32.RunModule('PROFILE', comd_prof,1,'','','','',1)
  
    ###### Step 5 ######
    ### Command line for creating Residual series in CORRELATE Module
    comd_resid = TimrSeries_name +'*'+ node_path + '_profile' +'*'+  residual_prefix +'*'+'10000' +'*' + '1' +'*'+ 'none'       
    IDRISI32.RunModule('CORRELATE',comd_resid,1,'','','','',1)
    return 


###### Read Data ######
def readTiff(file_root,fileName):
    directory = os.path.join(file_root ,fileName )
    dataset = gdal.Open(directory)
    if dataset == None:
        print(directory + " doesn't exist")
        return 
    data = gdal.Open(directory)
    data = data.ReadAsArray()
    return data

def get_orgfileName(directory):
    f_listorg = os.listdir(directory)
    f_list = natsorted(f_listorg)

    all_file =[]
    for i in f_list:     
        if (os.path.splitext(i)[1] == '.rst') or(os.path.splitext(i)[1] == '.tif'):    
            all_file.append(i)
    return all_file


def read_residual_filename(path,name_prefix):
    files = [i for i in os.listdir(path) if os.path.isfile(os.path.join(path,i)) and name_prefix in i]
    f_list = natsorted(files)
    all_file =[]
    for i in f_list:     
        # os.path.splitext(): split filename and extension
        if (os.path.splitext(i)[1] == '.rst') or(os.path.splitext(i)[1] == '.tif'):    
            all_file.append(i)
    return all_file


###### Name part - the user needs to modify this part ######
# The number of SATA components   
node_num = 10

epochs =500

# number of hidden nodes 
encoding_dim = 1

###The inputs and outputs should be in the same folder

# Working folder 
workingFolder = r"E:\gpu_work\New Data Test\Auto_10nodes"
# Input time series data
input_data = r"E:\gpu_work\New Data Test\Auto_10nodes"   

# The original time series name - file name with .rgf extension
input_seriesname = 'x2molzsst_anom'

# Prefix of residual file name 
out_residual_prefix = 'X2_SATA500_10noderesidual_'

# Prefix of SATA component name 
nodename_prefix = 'X2_SATA500_10node_'
  
# Launch TerrSet 
IDRISI32 = win32com.client.Dispatch('IDRISI32.IdrisiAPIServer')
IDRISI32.SetWorkingDir(workingFolder)

###### Create .tsf file - This will use in TerrSet ######
TimeSeries_name = os.path.join(workingFolder, input_seriesname)
    
for file in os.listdir(workingFolder):
    if file.endswith('.tsf'):
        file_path = os.path.join(workingFolder, file)
        file_name, file_extend = os.path.splitext(file)
        for n in range (1,node_num +1):
            new_name = out_residual_prefix + str(n) + '_Resid' + file_extend
            newfile_path = os.path.join (workingFolder, new_name)
            shutil.copyfile(file_path,newfile_path)
             
###### Main code ######
for k in range(1, node_num +1):
    if k ==1:
        directory = input_data 
        filenames = get_orgfileName(directory) 
        all_data =[]
        for filename in filenames:
            data =  readTiff(directory, filename)
            all_data.append(data)
        all_data = np.array(all_data)
  
        x_train = all_data
        x_train = x_train.reshape(len(x_train),-1)  
        
        input_dim = x_train.shape[1]
        residual_prefix = out_residual_prefix + str(k) 
        nodename = nodename_prefix +str(k)
        SATA_out = os.path.join ( workingFolder ,nodename )   
        
        SATA_autoencoder(x_train,encoding_dim,k,input_dim,nodename,SATA_out,epochs)
        Call_TerrSet(SATA_out,residual_prefix, TimeSeries_name)
        
    else:   
        residual_prefix = out_residual_prefix + str(k-1)
        TimeSeries_name = os.path.join (workingFolder ,residual_prefix + '_Resid' )   
        directory = workingFolder 
        filenames = read_residual_filename(directory, residual_prefix)
        
        all_data =[]
        for filename in filenames:
            data =  readTiff(directory, filename)
            all_data.append(data)
        all_data = np.array(all_data)
           
        x_train = all_data
        x_train = x_train.reshape(len(x_train),-1)  
        
        input_dim = x_train.shape[1]
        residual_prefix = out_residual_prefix + str(k) 
        nodename = nodename_prefix +str(k)
        SATA_out = os.path.join (workingFolder, nodename)    
        SATA_autoencoder(x_train,encoding_dim,k,input_dim,nodename,SATA_out,epochs)
        Call_TerrSet(SATA_out,residual_prefix, TimeSeries_name)

