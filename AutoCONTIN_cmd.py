import os
from AutoCONTIN import autoContin
'''
this is a cmd interface for AutoCONTIN
can work in batch mode for multiple data files
'''

def singleMode():
    data_file = input('data file path (absolute path recommended): ')
    try:
        autoContin(data_file, full_auto=True, rename=True)
        print('done')
    except:
        print('Ooops, something went wrong...')

def batchMode():
    data_folder = input('\ndata folder (absolute path recommended): ')
    print('\n'+'='*20 + ' AutoCONTIN by LiMu ' + '='*20 + '\n')
    file_list = os.listdir(data_folder)

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
                autoContin(datafile_abspath, full_auto=True, rename=True)
                print(' - O - CONTIN success | {}'.format(f))
                N_success += 1
            except:
                print(' - X - CONTIN fail    | {}'.format(f))
                N_fail += 1
    print('-----------------------------------------------')
    print('all done, {} in total, {} success, {} fail. Have a nice day!\n'.format(N_datafile, N_success, N_fail))
    #print('failed file:')

if __name__ == "__main__":
    right_input = False

    while not right_input:
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
    input('\npress ENTER to exit')
            
            