# Contributing

Hey there 👋! Look at you wanting to contribute! This package is designed to make it as easy as possible for you to contribute new parsers for quantum chemistry programs and to make it as easy as possible to maintain the code. This document will walk you through the design decisions and how to add new parsers.

## TL;DR - How to add new parsers

1. Create a file in the `parsers` directory named after the quantum chemistry program, e.g., `terachem.py`.
2. Create a `SUPPORTED_FILETYPES` set in the module containing the file types the parsers support.
3. If `stdout` is a file type then create a `def get_calctype(string: str) -> CalcType` function that returns the `CalcType` for the file. One of `CalcType.energy`, `CalcType.gradient`, or `CalcType.hessian`.
4. Create simple parser functions that accept file data (`str | bytes`) and a `data_collector` object. The parser should 1) parse a single piece of data from the file, 2) cast it to the correct Python type and 3) set it on the output object at its corresponding location found on the `qcio.SinglePointResults` object. Register this parser by decorating it with the `@parser()` decorator. The decorator optionally accepts a `filetype` argument (`FileType.stdout` by default) and can declare keyword arguments `required` (`True` by default), and `only` (`None` by default). See the `qcparse.utils.parser` decorator for details on what these mean.

   ```py
   @parser(filetype=FileType.stdout)
   def parse_some_data(string: str, data_collector: ParsedDataCollector):
   """Parse some data from a file."""
       regex = r"Some Data: (-?\d+(?:\.\d+)?)"
       data_collector.some_data = float(regex_search(regex, string).group(1))
   ```

5. That's it! The developer just has to focus on writing simple parser functions like this and the `qcparse` package will take care of registering these parsers for the correct program and filetype and will call them at the right time when parsing a file.

See the `terachem.py` file for an overview.

## Basic Architectural Overview and Program Flow

1. Top level `parse` function is called passing `data_or_path: Union[Path, str, bytes]`, the `program: str` that generated the output, and the `filetype` (e.g., `stdout` or `wavefunction` or whatever filetypes a particular program emits for which parsers have been written).
2. `parse` instantiates an `ParsedDataCollector` object that acts as a proxy for the `SinglePointResults` object but offers two advantages:
   - The `SinglePointResults` object has multiple required data fields, but parsers only return a single data value per parser. The `ParsedDataCollector` object gets passed to parsers and they can add their parsed value to the objects just as if it were a mutable `SinglePointResults` object. This makes it easy for each parser to both specify exactly what data they parse and where that data will live on the final structured object.
   - The `ParsedDataCollector` object only allows setting a particular data attribute once. If a second attempt is made it raises an `AttributeError`. This provides a sanity check that multiple parsers aren't trying to write to the same field and overwriting each other.
3. `parse` looks up the parsers for the `program` in the `parser_registry`. Parsers are registered by wrapping them with the `@parser` decorator found in `qcparse.parsers.utils`. The `@parser` decorator registers a parser with the registry under the program name of the module in which it is found, verifying that the `filetype` for which it is registered is supported by the `program` by checking `SupportedFileTypes` in the parser's module. It also registers whether a parser `must_succeed` which means an exception will be raised if this value is not found when attempting to parse a file. In order for parsers to properly register they must be imported, so make sure they are hoisted into the `qcparse.parsers.__init__` file.
4. `parse` executes all parsers for the given `filetype` and converts the `ParsedDataCollector` object passed to all the parsers into a final `SinglePointResults` object.
