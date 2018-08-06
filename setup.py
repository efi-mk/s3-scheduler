import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="s3_scheduler",
    version="0.0.2",
    author="Efi Merdler-Kravitz",
    author_email="efi.merdler@gmail.com",
    description="Use S3 as a scheduler mechanism using Lambda",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/efi-mk/s3-scheduler",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
