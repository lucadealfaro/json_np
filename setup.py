import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "json_np",
    version = "0.0.1",
    url = 'https://github.com/lucadealfaro/json_np',
    license = 'BSD',
    author = 'Luca de Alfaro and Massimo Di Pierro',
    author_email = 'luca@dealfaro.com, mdipierro@gmail.com',
    maintainer = 'Luca de Alfaro',
    maintainer_email = 'luca@dealfaro.com',
    description = 'Json serialization extended to dates, numpy arrays, and more',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    packages = ['json_np'],
    install_requires=[
        "numpy"
    ],
    zip_safe = False,
    platforms = 'any',
    python_requires=">=3.7",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
