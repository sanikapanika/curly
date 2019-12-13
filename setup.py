from setuptools import setup, find_packages

setup(
        name="Curly",
        version="0.1.0",
        description="Curl framework to ease cli request forgery",
        long_description=None,
        author="AjferSanjo",
        author_email="sanin.alagic@gmail.com",
        url="",
        download_url="",
        packages=find_packages(),
        include_package_data=True,
        scripts=('Kernel.py',),
        entry_points={},
        install_requires=[
            "future",
            "requests",
            "paramiko",
            "pysnmp",
            "pycryptodome",
            ],
        extras_require={},
        classifiers=[],
        ) 
