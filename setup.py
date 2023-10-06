from setuptools import setup, find_packages

def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file]
    
setup(
    name='plugipy',
    version='0.1.0',
    description='PlugiPy is a python library to rapidly create a flexible plugin system inside an application.',
    author='Christopher von Klitzing',
    url='https://github.com/ChristophervonKlitzing/PlugiPy',
    packages=find_packages(),
    install_requires=parse_requirements("requirements.txt"),
    license_files=['LICENSE'],
)
