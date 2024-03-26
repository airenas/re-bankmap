import subprocess
from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
git_version = subprocess.run(["git", "rev-list", "--count", "HEAD"], stdout=subprocess.PIPE).stdout.decode(
    'utf-8').strip()

setup(
    name='bankmap',
    url='https://github.com/airenas/re-bankmap',
    author='Airenas Vaičiūnas',
    author_email='airenass@gmail.com',
    packages=find_packages(include=['bankmap', 'bankmap.*']),
    version='0.3.' + git_version,
    license='BSD-3',
    description='Bank statement entries mapping to internal db entries',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires=">=3.8",
    install_requires=[
        'pandas~=1.5.0',
        'tqdm~=4.64.1',
        'numpy~=1.23.3',
        'jellyfish~=0.9.0',
        'jsonlines==4.0.0',
        'strsimpy @ git+https://github.com/airenas/python-string-similarity.git@v0.2.87#egg=strsimpy',
    ]
)
