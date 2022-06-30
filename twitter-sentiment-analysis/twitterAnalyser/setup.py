import setuptools

# NOTE: Any additional file besides the `main.py` file has to be in a module
#       (inside a directory) so it can be packaged and staged correctly for
#       cloud runs.

REQUIRED_PACKAGES = [
    'google-cloud==0.34.0',
    'google-cloud-language==1.3.0',
    'apache-beam==2.23.0',
    'apache-beam[gcp]==2.23.0'
]

setuptools.setup(
    name='twitter-pipeline',
    version='0.0.1',
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
    include_package_data=True,
    description='Cloud ML molecules sample with preprocessing',
)
