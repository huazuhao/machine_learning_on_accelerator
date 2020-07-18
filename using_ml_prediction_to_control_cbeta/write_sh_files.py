# generate the sh files
import subprocess
import os

def write_sh_file_and_submit(max_worker,cwd):

    for index in range(0,max_worker):

        sh_file_name = os.path.join(cwd, 'sh_file_for_generating_data'+str(index)+'.sh')

        with open(sh_file_name, 'w') as f:
            f.write('''
            #!/usr/bin/bash
            ''')

        worker_name = os.path.join(cwd,'a_worker_for_generating_data.py')

        with open(sh_file_name, 'a') as f:
            # Write the data to it
            f.write('''python '''+worker_name+ ''' ''' + str(index) + ''' '''+cwd + '''\n''')



        subprocess.call('qsub ' + str(sh_file_name), shell=True)