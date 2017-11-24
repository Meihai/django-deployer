import zipfile
import re
import os
import paramiko

import confparser
from sys import argv
from os.path import join, relpath, abspath
from datetime import datetime


class Deployer:
    def __init__(self, conf_file):
        conf = confparser.parse_conf_file(conf_file)

        host = conf.get('host')  # required
        port = conf.get('port', 22)
        pri_key = conf.get('pri_key')
        pri_key_password = conf.get('pri_key_password')
        user = conf.get('user', 'root')
        password = conf.get('password')  # either pri_key or password is required
        local_project_dir = conf.get('local_project_dir')  # required
        remote_project_dir = conf.get('remote_project_dir')  # required
        collectstatic = str(conf.get('collectstatic', False)) in ('False', 'false', 'FALSE')

        if not any((pri_key, password)):
            raise Exception('deploy config is not satisfied,either ssh private key or user&password for login is '
                            'required')

        missed = []
        if not host:
            missed.append('host')
        if not local_project_dir:
            missed.append('local_project_dir')
        if not remote_project_dir:
            missed.append('remote_project_dir')

        if missed:
            raise Exception(
                'deploy config is not satisfied,%s %s required' % (
                    ','.join(missed), 'is' if len(missed) == 1 else 'are'))

        remote_uwsgi_path = conf.get('remote_uwsgi_path', join(remote_project_dir, 'uwsgi.ini'))
        remote_requirements_path = conf.get('remote_requirements_path',
                                            join(remote_project_dir, 'requirements.txt'))
        remote_shell_path = conf.get('remote_shell_path')
        ignore_path = conf.get('ignore_path', join(local_project_dir, 'd_ignore'))

        self.host = host
        self.port = port
        self.ssh_pri_key = paramiko.RSAKey.from_private_key_file(pri_key,
                                                                 password=pri_key_password) if pri_key else None
        self.user = user
        self.password = password
        self.remote_project_dir = remote_project_dir
        self.local_project_dir = local_project_dir
        self.remote_uwsgi_path = remote_uwsgi_path
        self.remote_requirements_path = remote_requirements_path
        self.remote_shell_path = remote_shell_path
        self.ignore_path = ignore_path
        self.collectstatic = collectstatic

        self.ignored_dirs = []
        self.ignored_files = []

        self.tmp_zip = 'tmp.zip'

    def __enter__(self):
        print('Start to connect to host...')
        self.transport = paramiko.Transport((self.host, self.port))
        print('Connection succeeded!')
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.ssh_pri_key:
            print('Start to login...')
            self.transport.connect(username=self.user, pkey=self.ssh_pri_key)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            self.ssh.connect(hostname=self.host, port=self.port, username=self.user, pkey=self.ssh_pri_key)
            print('Login succeeded!')
        else:
            print('Start to login...')
            self.transport.connect(username=self.user, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            self.ssh.connect(hostname=self.host, port=self.port, username=self.user, password=self.password,
                             allow_agent=True)
            print('Login succeeded!')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.transport.close()
        os.remove(self.tmp_zip)
        return False

    def __is_file_ignored(self, file_path):
        return any(map(lambda x: bool(re.search('%s$' % x, file_path)), self.ignored_files))

    def __is_dir_ignored(self, dir_path):
        return any(map(lambda x: bool(re.search('%s$' % x, dir_path + '/')), self.ignored_dirs))

    def __zip_local_project(self):
        os.chdir(self.local_project_dir)
        tmp_zip = self.tmp_zip
        z = zipfile.ZipFile(file=tmp_zip, mode='w', compression=zipfile.ZIP_DEFLATED)

        for dir_path, dir_names, file_names in os.walk(self.local_project_dir):

            # dir check
            if not self.__is_dir_ignored(dir_path):
                for filename in file_names:
                    file_path = join(dir_path, filename)
                    relative_file_path = relpath(file_path, self.local_project_dir)
                    # file check
                    if not self.__is_file_ignored(relative_file_path):
                        z.write(file_path, relative_file_path)
        z.close()

    def __parse_ignore(self):
        """
        parse ignore file
        :return:
        """
        lines = confparser.parse_ignore_file(self.ignore_path)
        self.ignored_files.append(self.tmp_zip)
        for l in lines:
            if re.match('[\w\s.]+(/[\w\s.]+)*/$', l):
                # exact dir path that will be ignored in root of project dir, all files or dirs will also be
                # ignored. eg: migrations/,a/d/
                self.ignored_dirs.append(l)
            elif re.match('^[\w\s.]+(/[\w\s.]+)*$', l):
                # exact path of file. eg: a/b/debug.txt
                self.ignored_files.append(l)
            elif re.match('\*/[\w\s.]+/', l):
                # fuzzy dir path that will be ignored with the name. eg: */abc/
                l = l.replace('*', '').replace('/', '', 1)
                self.ignored_dirs.append(l)
            elif re.match('\*\.\w+$', l):
                # fuzzy path of file that has some suffix. eg: *.md
                l = l.replace('*', '')
                self.ignored_files.append(l)

    def __upload(self):
        """
        upload project files to server
        :return:
        """
        self.__parse_ignore()
        self.__zip_local_project()
        try:
            print('Start to upload...')
            self.sftp.put(self.tmp_zip, join(self.remote_project_dir, self.tmp_zip))
            print('Upload finished!')
        except Exception as e:
            print('Upload failed:', e)
            os.remove(self.tmp_zip)

    def __exec_remote_cmd(self, cmd):
        print('Executing:', cmd)
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        out_lines = stdout.readlines()
        for l in out_lines:
            print(l)
        return stdin, out_lines, stderr

    def deploy(self):
        """
        deploy django project
        :return:
        """
        if self.collectstatic:
            print('Start to collect static files...')
            os.system('python3 %s/manage.py collectstatic --noinput' % self.local_project_dir)

        remote_backup_zip = abspath(
            join(self.remote_project_dir, '..', '{0}_backup_{1}.zip'.format(os.path.basename(self.remote_project_dir),
                                                                            datetime.now().strftime('%Y%m%d%H%M'))))
        self.__exec_remote_cmd('test -d {0} | mkdir -p {0}'.format(self.remote_project_dir))
        self.__exec_remote_cmd('zip -r {0} {1}'.format(remote_backup_zip, self.remote_project_dir))

        self.__upload()

        self.__exec_remote_cmd(
            "cd {0} && rm -rf `ls -a | egrep -v '^(\.|\.\.|{1})$'`".format(self.remote_project_dir, self.tmp_zip))
        self.__exec_remote_cmd(
            'cd {0} && unzip -n {1}'.format(self.remote_project_dir, self.tmp_zip))
        self.__exec_remote_cmd('cd {0} && rm {1}'.format(self.remote_project_dir, self.tmp_zip))
        self.__exec_remote_cmd('pip3 install -r {0}'.format(self.remote_requirements_path))

        stdin, out_lines, stderr = self.__exec_remote_cmd('cat {0}'.format(self.remote_uwsgi_path))
        uwsgi_conf = confparser.parse_conf_lines(out_lines)

        uwsgi_socket = uwsgi_conf.get('socket', '')
        uwsgi_http = uwsgi_conf.get('http', '')
        uwsgi_pid_path = uwsgi_conf.get('pidfile')
        uwsgi_daemonize = uwsgi_conf.get('daemonize', '')

        if uwsgi_pid_path:
            uwsgi_pid_dir = abspath(join(uwsgi_pid_path, '..'))
            self.__exec_remote_cmd(cmd='test -d {0} | mkdir -p {0}'.format(uwsgi_pid_dir))
        else:
            raise Exception("uwsgi.ini file lacks 'pidfile'  parameter, deploying is canceled")

        if uwsgi_daemonize:
            uwsgi_deamonize_dir = abspath(join(uwsgi_daemonize, '..'))
            self.__exec_remote_cmd('test -d {0} | mkdir -p {0}'.format(uwsgi_deamonize_dir))

        tmp_socket = re.findall(':(\d+)', uwsgi_socket)
        tmp_http = re.findall(':(\d+)', uwsgi_http)
        if tmp_socket or tmp_http:
            if tmp_socket:
                port = tmp_socket[0]
            else:
                port = tmp_http[0]
        else:
            raise Exception("uwsgi.ini file lacks 'socket' or 'http' parameter, deployment is canceled")

        cmd = 'lsof -i:{0} | grep uwsgi | wc -l'.format(port)
        stdin, out_lines, stderr = self.__exec_remote_cmd(cmd)
        pcount = int(out_lines[0]) if out_lines else 0
        if pcount:
            # uwsgi is already running
            self.__exec_remote_cmd('uwsgi --reload {0}'.format(uwsgi_pid_path))
        else:
            # uwsgi is not running
            self.__exec_remote_cmd('uwsgi --ini {0}'.format(self.remote_uwsgi_path))

        if self.remote_shell_path:
            # execute your customized shell script
            self.__exec_remote_cmd('chmod +x {0} && {0}'.format(self.remote_shell_path))

        print('Deployment finished!')


if __name__ == '__main__':
    script, *args = argv
    conf = args[0] if args else 'confexample/d_conf'
    with Deployer(conf) as deployer:
        deployer.deploy()
