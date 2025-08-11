<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Contributing to LibreAssistant

Thank you for your interest in contributing! We welcome all contributions that uphold the [Constitution](CONSTITUTION.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Development Workflow
1. Fork the repository and create your feature branch from `develop`.
2. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
3. Write clear, self-documented code and include tests when relevant.
4. Run `pytest` to make sure all tests pass.
5. Lint documentation with `npx markdownlint-cli '**/*.md'`.
6. Verify files contain the MIT license header using `python scripts/check_license_headers.py`.
7. Submit a pull request to `develop` describing your change.

All changes should target the `develop` branch. The `main` branch is protected and reserved for production-ready releases.

## Review Process
All pull requests require review by at least one member of the appropriate guild (e.g., code, ethics, documentation). Reviewers will check for:

- Adherence to the Constitution and Code of Conduct
- Inclusion of necessary tests and documentation
- Proper licensing headers and commit messages

## Reporting Issues
Use the GitHub issue tracker to report bugs or request features. Please include as much detail as possible so we can reproduce the problem or understand the feature request.

## Community
Join discussions in issues and pull requests to help shape the direction of the project. We strive for inclusive and respectful collaboration.

## Theme Submissions

Community themes live under the `community-themes/` directory. To submit a new theme:

1. Create a folder in `community-themes/` with your theme's name.
2. Add a `metadata.json` file describing the theme and a `theme.css` stylesheet containing your CSS variables.
3. Run `python scripts/build_theme_catalog.py` to regenerate the catalog and sanitized styles.
4. Include the generated changes in your pull request.
