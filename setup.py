import os
from setuptools import setup, find_packages


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

setup(name='django-excel-viewer',
      version='0.1',
      author='Ewald  Moitzi',
      url='https://github.com/emoitzi/django-excel-viewer',
      install_requires=open('%s/excel_viewer/requirements.txt' % os.environ.get('OPENSHIFT_REPO_DIR', PROJECT_ROOT)).readlines(),
)