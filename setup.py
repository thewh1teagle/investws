from setuptools import setup, find_packages
import glob

setup(
    name='investws',
    version='0.0.1',
    packages=find_packages(),
    data_files=glob.glob('investws/**'),
    include_package_data=True,
    install_requires=[
        'websockets'
    ],
)