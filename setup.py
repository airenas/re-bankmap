import subprocess
from pathlib import Path

from setuptools import setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
git_version = subprocess.run(["git", "rev-list", "--count", "HEAD"], stdout=subprocess.PIPE).stdout.decode(
    'utf-8').strip()

setup(
    name='bankmap',
    url='https://github.com/airenas/re-bankmap',
    author='Airenas Vaičiūnas',
    author_email='airenass@gmail.com',
    packages=['bankmap'],
    version='0.1.' + git_version + "-beta",
    license='BSD-3',
    description='Bank statement entries mapping to internal db entries',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires=">=3.8"
)
