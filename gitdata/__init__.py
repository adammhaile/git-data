import yaml
import pygit2
import logging
import urlparse
import os
import shutil


SCHEMES = ['ssh', 'ssh+git', "http", "https"]


class GitData(object):
    def __init__(self, data_path=None, clone_dir='./', branch=None, logger=None):
        self.logger = logger
        if logger is None:
            self.logger = logging.getLogger()

        self.clone_dir = clone_dir

        if data_path:
            self.load_data(data_path)

    def load_data(self, data_path):
        self.data_path = data_path

        data_url = urlparse.urlparse(self.data_path)
        if data_url in SCHEMES or (data_url == '' and ':' in data_url.path):
            data_name = os.path.splitext(os.path.basename(data_url.path))[0]
            data_destination = os.path.join(self.clone_dir, data_name)
            clone_data = True
            if os.path.isdir(data_destination):
                self.logger.info('Data clone directory already exists, checking commit sha')
                with Dir(data_destination):
                    rc, out, err = exectools.cmd_gather(["git", "ls-remote", self.data_path, "HEAD"])
                    if rc:
                        raise IOError('Unable to check remote sha: {}'.format(err))
                    remote = out.strip().split('\t')[0]

                    try:
                        exectools.cmd_assert('git branch --contains {}'.format(remote))
                        self.logger.info('{} is already cloned and latest'.format(self.data_path))
                        clone_data = False
                    except:
                        rc, out, err = exectools.cmd_gather('git log origin/HEAD..HEAD')
                        out = out.strip()
                        if len(out):
                            msg = """
                            Local config is out of sync with remote and you have unpushed commits. {}
                            You must either clear your local config repo with `./oit.py cleanup`
                            or manually rebase from latest remote to continue
                            """.format(data_destination)
                            raise IOError(msg)

            if clone_data:
                if os.path.isdir(data_destination):  # delete if already there
                    shutil.rmtree(data_destination)
                self.logger.info('Cloning config data from {}'.format(self.data_path))
                if not os.path.isdir(data_destination):
                    cmd = "git clone --depth 1 {} {}".format(self.data_path, data_destination)
                    try:
                        exectools.cmd_assert(cmd.split(' '))
                    except:
                        if self.data_path == constants.OCP_BUILD_DATA_RW:

                            self.logger.warn('Failed to clone {}, falling back to {}'.format(constants.OCP_BUILD_DATA_RW, constants.OCP_BUILD_DATA_RO))
                            self.data_path = constants.OCP_BUILD_DATA_RO
                            return self.resolve_metadata()
                        else:
                            raise
            self.data_path = data_destination
        elif data_url.scheme in ['', 'file']:
            pass
        else:
            raise ValueError(
                'Invalid data_path: {} - invalid scheme: {}'
                .format(self.data_path, data_url.scheme)
            )