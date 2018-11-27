from gitdata import GitData, GitDataException
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

args = {
    'data_path': 'git@github.com:adammhaile/ocp-build-data.git',
    'clone_dir': '/tmp/',
    'branch': 'openshift-3.12',
    # 'sub_dir': 'openshift-3.11',
    'logger': logger
}


def filter_wip(name, data):
    return data.get('mode', 'enabled') == 'wip'


filter_disabled = lambda name, data: data.get('mode', 'enabled') == 'disabled'


def owner(n, d):
    owners = d.get('owners', [])
    return 'avagarwa@redhat.com' in owners


def rhel(n, d):
    parent = d.get('from', {}).get('stream', None)
    return parent == 'rhel'


gd = GitData(**args)

data = gd.load_data(path='images', filter_funcs=[owner])
data['atomic-openshift-cluster-autoscaler'].data['mode'] = 'wip'
data['atomic-openshift-cluster-autoscaler'].save()
gd.commit('test update')
gd.push()

# print('')
# for k in data.keys():
#     print(k)
