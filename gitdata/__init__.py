import yaml
import logging
import urlparse
import os
import shutil
import exectools
from pushd import Dir


SCHEMES = ['ssh', 'ssh+git', "http", "https"]


class GitDataException(Exception):
    """A broad exception for errors during GitData operations"""
    pass


class GitDataBranchException(GitDataException):
    pass


class GitDataPathException(GitDataException):
    pass


class GitData(object):
    def __init__(self, data_path=None, clone_dir='./', branch='master',
                 sub_dir=None, exts=['yaml', 'yml', 'json'], logger=None):
        self.logger = logger
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger()

        self.clone_dir = clone_dir
        self.branch = branch

        self.cmd = exectools.Exec(self.logger)

        self.remote_path = None
        self.sub_dir = sub_dir
        self.exts = ['.' + e.lower() for e in exts]
        if data_path:
            self.clone_data(data_path)

    def clone_data(self, data_path):
        self.data_path = data_path

        data_url = urlparse.urlparse(self.data_path)
        if data_url.scheme in SCHEMES or (data_url.scheme == '' and ':' in data_url.path):
            data_name = os.path.splitext(os.path.basename(data_url.path))[0]
            data_destination = os.path.join(self.clone_dir, data_name)
            clone_data = True
            if os.path.isdir(data_destination):
                self.logger.info('Data clone directory already exists, checking commit sha')
                with Dir(data_destination):
                    # verify local branch
                    rc, out, err = self.cmd.gather("git rev-parse --abbrev-ref HEAD")
                    if rc:
                        raise GitDataException('Error checking local branch name: {}'.format(err))
                    branch = out.strip()
                    if branch != self.branch:
                        msg = ('Local branch is `{}`, but requested `{}`\n'
                               'You must either clear your local data or manually checkout the correct branch.'
                               ).format(branch, self.branch)
                        raise GitDataBranchException(msg)

                    # Check if local is synced with remote
                    rc, out, err = self.cmd.gather(["git", "ls-remote", self.data_path, self.branch])
                    if rc:
                        raise GitDataException('Unable to check remote sha: {}'.format(err))
                    remote = out.strip().split('\t')[0]
                    try:
                        self.cmd.check_assert('git branch --contains {}'.format(remote))
                        self.logger.info('{} is already cloned and latest'.format(self.data_path))
                        clone_data = False
                    except:
                        rc, out, err = self.cmd.gather('git log origin/HEAD..HEAD')
                        out = out.strip()
                        if len(out):
                            msg = ('Local data is out of sync with remote and you have unpushed commits: {}\n'
                                   'You must either clear your local data\n'
                                   'or manually rebase from latest remote to continue'
                                   ).format(data_destination)
                            raise GitDataException(msg)

            if clone_data:
                if os.path.isdir(data_destination):  # delete if already there
                    shutil.rmtree(data_destination)
                self.logger.info('Cloning config data from {}'.format(self.data_path))
                if not os.path.isdir(data_destination):
                    cmd = "git clone -b {} --depth 1 {} {}".format(self.branch, self.data_path, data_destination)
                    rc, out, err = self.cmd.gather(cmd)
                    if rc:
                        raise GitDataException('Error while cloning data: {}'.format(err))

            self.remote_path = self.data_path
            self.data_path = data_destination
        elif data_url.scheme in ['', 'file']:
            self.remote_path = None
            self.data_path = os.path.abspath(self.data_path)  # just in case relative path was given
        else:
            print(data_url)
            print(data_url.scheme)
            raise ValueError(
                'Invalid data_path: {} - invalid scheme: {}'
                .format(self.data_path, data_url.scheme)
            )

        if self.sub_dir:
            self.data_dir = os.path.join(self.data_path, self.sub_dir)
        else:
            self.data_dir = self.data_path
        if not os.path.isdir(self.data_dir):
            raise GitDataPathException('{} is not a valid sub-directory in the data'.format(self.sub_dir))

    def load_data(self, path='', key=None, filter_funcs=None):
        full_path = os.path.join(self.data_dir, path.replace('\\', '/'))
        if path and not os.path.isdir(full_path):
            raise GitDataPathException('Cannot find "{}" under "{}"'.format(path, self.data_dir))

        if filter_funcs is not None and not isinstance(filter_funcs, list):
            filter_funcs = [filter_funcs]
        if key:
            files = ['{}{}'.format(key, e) for e in self.exts]
            result = None
        else:
            files = os.listdir(full_path)
            result = {}

        for name in files:
            base_name, ext = os.path.splitext(name)
            if ext.lower() in self.exts:
                data_file = os.path.join(full_path, name)
                if os.path.isfile(data_file):
                    with open(data_file, 'r') as f:
                        data = yaml.load(f)
                        if key:
                            return data
                        else:
                            use = True
                            if filter_funcs:
                                for func in filter_funcs:
                                    use &= func(base_name, data)
                                    if not use:
                                        break
                            if use:
                                k = name.replace(ext, '')
                                result[k] = data

        return result
