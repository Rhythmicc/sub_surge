from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()
VERSION = "0.0.3"

setup(
    name="sub_surge",
    version=VERSION,
    description="Update surge config",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="surge config update",
    author="RhythmLian",
    url="https://github.com/Rhythmicc/sub_surge",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=["Qpro"],
    entry_points={
        "console_scripts": [
            "sub-surge = sub_surge.main:main",
        ]
    },
)
