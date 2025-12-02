"""Import compatible wrapper so module can be imported as `docs_parser`.

This duplicates the original CLI implementation in `docs-parser.py` so tests
can import the conversion functions as a normal python module.
"""

import docs_dash_compat as _compat

# Export the key functions used by tests
docx_to_markdown_full = _compat.docx_to_markdown_full
process_directory = _compat.process_directory

# if run directly, delegate to original script's CLI (docs_dash_compat)
if __name__ == '__main__':
    _compat.__main__()
