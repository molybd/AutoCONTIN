import os
from AutoCONTIN import autoContin
'''
this is a cmd interface for AutoCONTIN
can work in batch mode for multiple data files
'''

def singleMode():
    data_file = input('data file path (absolute path recommended): ')
    rename_index = input('rename data file? ([y]/n): ').lower()
    timestamp_index = input('add time stamp? ([y]/n): ').lower()
    
    gamma_min_input = input('  gamma min (defalt: 1): ')
    gamma_max_input = input('gamma max (defalt: 1e6): ')
    if gamma_min_input == '':
        gamma_min = 1
    else:
        gamma_min = float(gamma_min_input)
    if gamma_max_input == '':
        gamma_max = 1e6
    else:
        gamma_max = float(gamma_max_input)

    if rename_index == '' or rename_index == 'y':
        isrename = True
    else:
        isrename = False
    if timestamp_index == '' or timestamp_index == 'y':
        istimestamp = True
    else:
        istimestamp = False

    try:
        autoContin(data_file, full_auto=True, rename=isrename, addTimeStamp=istimestamp, gamma_min=gamma_min, gamma_max=gamma_max)
        print('done')
    except:
        print('Ooops, something went wrong...')

def batchMode():
    data_folder = input('data folder (absolute path recommended): ')
    rename_index = input('rename data file? ([y]/n): ').lower()
    timestamp_index = input('add time stamp? ([y]/n): ').lower()

    gamma_min_input = input('  gamma min (defalt: 1): ')
    gamma_max_input = input('gamma max (defalt: 1e6): ')
    if gamma_min_input == '':
        gamma_min = 1
    else:
        gamma_min = float(gamma_min_input)
    if gamma_max_input == '':
        gamma_max = 1e6
    else:
        gamma_max = float(gamma_max_input)

    if rename_index == '' or rename_index == 'y':
        isrename = True
    else:
        isrename = False
    if timestamp_index == '' or timestamp_index == 'y':
        istimestamp = True
    else:
        istimestamp = False

    try:
        file_list = os.listdir(data_folder)
        print('\n'+'='*20 + ' AutoCONTIN by LiMu ' + '='*20 + '\n')

        print('-----------------------------------------------')
        print('        Result        |      data file name')
        print('----------------------+------------------------')
        N_datafile = 0
        N_success = 0
        N_fail = 0
        for f in file_list:
            if f.split('.')[-1] == 'dat':
                N_datafile += 1
                try:
                    datafile_abspath = os.path.join(data_folder, f)
                    autoContin(datafile_abspath, full_auto=True, rename=isrename, addTimeStamp=istimestamp, gamma_min=gamma_min, gamma_max=gamma_max)
                    print(' - O - CONTIN success | {}'.format(f))
                    N_success += 1
                except:
                    print(' - X - CONTIN fail    | {}'.format(f))
                    N_fail += 1
        print('-----------------------------------------------')
        print('all done, {} in total, {} success, {} fail. Have a nice day!\n'.format(N_datafile, N_success, N_fail))
        #print('failed file:')
    except:
        print('Ooops, something went wrong...')

if __name__ == "__main__":
    exit = False

    while True:
        mode = input('\nSelect Mode: 1. Single file | 2. Batch mode (input 1 or 2): ')
        print()
        if mode == '1':
            right_input = True
            singleMode()
        elif mode == '2':
            right_input = True
            batchMode()
        else:
            print('please input 1 or 2 !')
            
            