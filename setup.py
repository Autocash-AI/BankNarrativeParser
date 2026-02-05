from setuptools import setup, find_packages

setup(
    name="counterparty",
    version="0.1.6",
    description="A library for counterparty extraction and narrative parsing.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={
        "counterparty": ["key_engine/*.json"],
    },
    python_requires=">=3.9",
    install_requires=[
        "rapidfuzz>=2.0.0",
    ],
)
