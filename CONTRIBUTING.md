# Contributing

## Conventional Commits

PanelApp uses [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/).

If you fork the project you don't need to follow the conventional commits, as your
commits can be squashed before the merge. If you want to keep the commits history,
you need to follow the conventional commits.

### Overview

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

You can [validate](https://regex101.com/r/cP1SQR/1) the commit messages using regex
validator, currently the rule is

```
^(revert: )?(feat|fix|docs|refactor|perf|test|chore|ci)(|!)(\([a-z-]+\))?: .{1,50}
```

### Examples

- `feat: new feature`
- `feat!: breaking change feature`
- `fix: some bug fix`
- `chore: neither a feat nor fix`
- `docs: add contrib.md`
- `refactor: code improvements without new features`
- `perf: performance improvements`
- `test: add some unit or integration test`
- `ci: ci pipelines improvement`
- `revert: feat: new feature`
- `feat(moi): add moi checks`
- `fix(api): fix api endpoint response`

## Rebasing & Squashing

Rebase instead of merge as it keeps the history cleaner and doesn't create unnecessarily
merge commit messages.

If the merge request has too many commit messages or they are either repetitive or
ungrouped PanelApp maintainers will squash them.

I.e. a `feat` commit can have a feature implementation, tests, and docs updated all in
one vs three separate commits.

If you don't want your commits to be squashed, you'd need to squash and reword commits
yourself. When creating a merge request add a note you don't want it to be squashed.

## Merge requests

Please follow the original template for merge requests. The current template is added below.
You can remove HTML comment blocks (`<!-- -->`).

```text
<!--
  Please ensure the PR title contains the ticket ID, short description and
  is formatted to match "PANELAPP-XXX - Add padding fix" or "#123 - Add padding fix"

  If you don't know `PANELAPP-XXX` id, PanelApp maintainers will add it.

  If the PR should not be merged prefix the title WIP;
  e.g. "WIP: PANELAPP-XXX - Add padding fix"
-->

## Overview

<!-- Describe the changes, additionally, if the PR is "WIP", explain why -->

## Related ticket

<!-- Replace XXX with the ticket ID, e.g. 123 -->

- PANELAPP-XXX

## Checklist

<!-- Replace [ ] with [x] for the items that apply -->

- [ ] The PR only includes changes relating to 1 ticket
- [ ] I have added labels to reflect change type
- [ ] I have checked all existing and new tests pass
- [ ] I have checked that linting passes
- [ ] I have added tests to cover my changes
- [ ] I have updated the documentation where required
- [ ] I have informed the team of any impactful changes
```

## Branching

If you fork the project you can use any branch strategy you are comfortable with.

Any internal PanelApp branches should use the following convention:

`PANELAPP-XXX/short-description`, where `PANELAPP` can be a project related to the
change.

You can also use `release/0.0.0` branches in case you aren't tagging a commit on master
branch, i.e. hotfix, etc.

[Regex check](https://regex101.com/r/ydie9u/1)

## CI/CD pipelines

When you create a merge request CI/CD pipelines will run the following pipelines:

- import sorting using isort (version 5.0.5)
- code formatting using black (version 22.1.0)
- unit tests using pytest

You can use [pre-commit](https://pypi.org/project/pre-commit/) to check the code before
creating a commit.
