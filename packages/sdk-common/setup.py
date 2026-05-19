"""SDK Common - Package Setup"""
from setuptools import setup, find_packages

setup(
    name="safety-platform-sdk-common",
    version="1.0.0",
    description="장애인직업재활시설 스마트안전시스템 - 공통 SDK",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "pyyaml>=6.0",
    ],
)
