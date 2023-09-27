# Design Decisions

## Other parser packages to look at

- [iodata](https://github.com/theochem/iodata) and [cclib](https://cclib.github.io/contents.html) are recommended by [this](https://mattermodeling.stackexchange.com/questions/6532/whats-the-best-quantum-chemistry-output-parser-for-the-command-line) StackOverflow post. `iodata` was [published](https://onlinelibrary.wiley.com/doi/abs/10.1002/jcc.26468?casa_token=iQFOBtKf0qAAAAAA:pAv_vxn6Nfis_DhQENlqGpeIZoawNhJYCg17fdobB3ftuyEbHSOAyHbsjKTeU_AdVS48EiqqQDzUHKNf) in 2020 so I'd consider it the more modern alternative. It's still a mess to use.

## UPDATED DESIGN DECISION:

- I don't see a strong reason for making this package a standalone package that parses everything required for a `SinglePointOutput` object including input data, provenance data, xyz files, etc... While the original idea was to have a cli tool to run on TeraChem files, now that I've build my own data structures (`qcio`) and driver program (`qcop`), there's no reason to parse anything but `SinglePointResults` values because we should just be driving the programs with `qcop` and already have access to the input data. The code is far easier to maintain as only a results parser. The only downside would be walking in to someone else's old data and wanting to slurp it all in, but perhaps there's no reason to build for that use case now... Just go with SIMPLE and keep the code maintainable.

## Publishing Checklist

- Update `CHANGELOG.md`
- Bump version in `pyproject.toml`
- Tag commit with a version and GitHub Actions will publish it to pypi if tag is on `master` branch.
- `git push --tags`
- `git push`
