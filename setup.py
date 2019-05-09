from setuptools import setup

setup(
    name="onlinewebfonts-dl",
    version="0.0.1",
    description="",
    author="Victor Gavro",
    author_email="vgavro@gmail.com",
    url="https://github.com/vgavro/onlinewebfonts-dl",
    license="MIT License",
    classifiers=[
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
    ],
    py_modules=["onlinewebfonts_dl"],
    install_requires=[
        'requests',
        'click',
    ],
    entry_points={
        'console_scripts': [
            'onlinewebfonts-dl=onlinewebfonts_dl:main',
        ],
    },
)
