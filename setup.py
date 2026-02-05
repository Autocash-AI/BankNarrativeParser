from setuptools import setup, find_packages

setup(
    name="counterparty",
    version="0.1.0",
    description="A library for counterparty extraction and narrative parsing.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        # Add dependencies here if needed, e.g. 'spacy', 'pandas'
        # based on project_gamma requirements
    ],
)
