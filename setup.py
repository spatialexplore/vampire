try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Vampire - Vulnerability Analysis and Monitoring Platform for Impact of Regional Events',
    'author': "Rochelle O'Hagan",
    'url': 'URL to get it at',
    'download_url': 'Where to download it.',
    'author_email': 'rochelle.ohagan@rokoconsulting.com.au',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['vampire'],
    'scripts': [],
    'name': 'Vampire'
}

setup(**config)
