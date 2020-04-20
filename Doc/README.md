# fontTools Documentation

The fontTools project documentation updates continuously on Read the Docs as the project source changes.  

The documentation is hosted at https://fonttools.readthedocs.io/.

## Contents

- [How to Build Local Documentation](#how-to-build-local-documentation)
- [Contributing to the fontTools Documentation](#contributing-to-the-documentation)
- [Documentation License](#documentation-license)

## How to Build Local Documentation

### Install Dependencies

You must have a Python 3 interpreter and the `pip` Python package manager installed on your system to build the fontTools documentation.

Pull the fontTools project source files, create a Python virtual environment, and then install fontTools and the documentation build dependencies by executing the following commands in the root of the fontTools source repository:

```
$ pip install -e . [all]
$ pip install -r Doc/docs-requirements.txt
```

### Build Documentation

**With `make`**: execute the following command in the root of the repository:

```
$ make docs
```

**Without `make`**: execute the following command in the **`Doc` directory**:

```
$ sphinx-build -b html source build
```

Open the `Doc/build/html/index.html` file in your browser to view the documentation home page.

## Contributing to the Documentation

We highly encourage contributions!  Please follow the instructions below to improve the documentation.

### Python Docstring Style

We recommend the use of Python docstrings that follow [the Google Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#381-docstrings).  Our documentation build approach parses appropriately formatted docstrings into formatted documentation files.

#### Function Documentation Example

```python
def fetch_bigtable_rows(big_table, keys, other_silly_variable=None):
    """Fetches rows from a Bigtable.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by big_table.  Silly things may happen if
    other_silly_variable is not None.

    Args:
        big_table: An open Bigtable Table instance.
        keys: A sequence of strings representing the key of each table row
            to fetch.
        other_silly_variable: Another optional variable, that has a much
            longer name than the other args, and which does nothing.

    Returns:
        A dict mapping keys to the corresponding table row data
        fetched. Each row is represented as a tuple of strings. For
        example:

        {'Serak': ('Rigel VII', 'Preparer'),
         'Zim': ('Irk', 'Invader'),
         'Lrrr': ('Omicron Persei 8', 'Emperor')}

        If a key from the keys argument is missing from the dictionary,
        then that row was not found in the table.

    Raises:
        IOError: An error occurred accessing the bigtable.Table object.
    """
```
*Source: [Google Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md) (CC BY-SA 3.0)*

#### Class Documentation Example

```python
class SampleClass(object):
    """Summary of class here.

    Longer class information....
    Longer class information....

    Attributes:
        likes_spam: A boolean indicating if we like SPAM or not.
        eggs: An integer count of the eggs we have laid.
    """

    def __init__(self, likes_spam=False):
        """Inits SampleClass with blah."""
        self.likes_spam = likes_spam
        self.eggs = 0

    def public_method(self):
        """Performs operation blah."""
```
*Source: [Google Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md) (CC BY-SA 3.0)*

### Build Local Documentation and Review Your Changes

Build a local set of HTML documentation files with the instructions above and review your changes.

### Submit a Pull Request

Submit a Github pull request with your proposed improvements to the documentation.  

Thanks for your contribution!

## Documentation License

The fontTools documentation is released under a [CC BY-SA 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).
