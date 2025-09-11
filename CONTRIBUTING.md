<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Contributing to LibreAssistant

Thank you for your interest in contributing! We welcome all contributions that uphold the [Constitution](CONSTITUTION.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Development Workflow
1. Fork the repository and create your feature branch from `develop`.
2. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
3. Write clear, self-documented code and include tests when relevant. UI styling must use the tokenized design system in `ui/tokens.css`, which includes Light, Dark, and High-Contrast themes.
4. Install the system SQLCipher libraries if you need encrypted SQLite support so [`pysqlcipher3`](https://pypi.org/project/pysqlcipher3/) can compile (e.g., `sudo apt-get install libsqlcipher-dev` on Debian/Ubuntu). Without SQLCipher, the project will fall back to the standard `sqlite3` module without encryption.
5. Run `pytest` to make sure all tests pass.
6. Lint documentation with `npx markdownlint-cli '**/*.md'`.
7. Verify files contain the MIT license header using `python scripts/check_license_headers.py`.
8. Submit a pull request to `develop` describing your change.

All changes should target the `develop` branch. The `main` branch is protected and reserved for production-ready releases.

## Review Process
All pull requests require review by at least one member of the appropriate guild (e.g., code, ethics, documentation). Reviewers will check for:

- Adherence to the Constitution and Code of Conduct
- Inclusion of necessary tests and documentation
- Proper licensing headers and commit messages

## Reporting Issues
Use the GitHub issue tracker to report bugs or request features. Please include as much detail as possible so we can reproduce the problem or understand the feature request. For systematic bug discovery, consider organizing a [bug bash session](docs/bug-bash-guide.md).

## User Testing and Feedback

LibreAssistant benefits greatly from user testing and feedback. We encourage the community to organize and participate in structured testing sessions:

### Bug Bash Sessions
Collaborative testing sessions to systematically discover bugs and issues. See the [Bug Bash Guide](docs/bug-bash-guide.md) for organizing effective sessions with new users.

### Usability Walkthroughs  
User-centered testing to identify friction points and improve user experience. See the [Usability Walkthrough Guide](docs/usability-walkthrough-guide.md) for conducting structured usability testing.

### Session Templates
Use our templates to organize testing sessions:
- [Bug Bash Session Template](templates/bug-bash-session-template.md)
- [Usability Session Template](templates/usability-session-template.md)
- [Bug Report Template](templates/bug-report-template.md)
- [Usability Report Template](templates/usability-report-template.md)

## Community
Join discussions in issues and pull requests to help shape the direction of the project. We strive for inclusive and respectful collaboration.

## Theme Submissions

Community themes live under the `community-themes/` directory. Themes override design tokens via CSS custom properties and are sanitized server-side to a whitelist of safe properties. To submit a new theme:

1. Create a folder in `community-themes/` with your theme's name.
2. Add a `metadata.json` file describing the theme (follow the style guidelines in `community-themes/README.md`) and a `theme.css` stylesheet overriding tokens via CSS custom properties. Unsupported properties will be removed during sanitization.
3. Run `python scripts/build_theme_catalog.py` to regenerate the catalog and sanitized styles.
4. Open the generated `ui/themes/<id>.css` locally to verify the theme renders as expected.
5. Include the generated changes in your pull request. The sanitized CSS will be served at `/api/v1/themes/{name}.css` for the marketplace to load in a sandboxed iframe.
