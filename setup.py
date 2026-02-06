from setuptools import setup, find_packages

setup(
    name="banknarrativeparser",
    version="0.1.7",
    author="Siddharth Gautam",
    description="A library for counterparty extraction and narrative parsing.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "banknarrativeparser": ["key_engine/*.json"],
    },
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "rapidfuzz>=2.0.0",
    ],
)
