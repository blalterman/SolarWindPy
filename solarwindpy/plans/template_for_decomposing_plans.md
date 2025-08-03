### 🧩 Goal

Convert the existing LaTeX-based scientific paper repository into a reusable template.  
This includes modularization, placeholder substitution, and template metadata creation.

---

### 🔨 Tasks (please create separate PRs if appropriate)

- [ ] Identify and replace hardcoded metadata (title, author, date) with placeholders
- [ ] Move all section files into a `sections/` directory
- [ ] Create a `copier.yml` file with appropriate user prompts (e.g., paper title, author, affiliation)
- [ ] Add instructions to the `README.md` for using the template
- [ ] Ensure the LaTeX compiles with placeholder values
- [ ] Remove paper-specific content, keeping only structural scaffolding
- [ ] Insert `\todo{Fill out the <section name>}` where full content was removed

---

### 🧠 Notes for Sweep AI

- Please split these into **separate PRs per task**, unless a combined PR is more efficient.
- Create your own branches for each PR (e.g., `sweep/add-copier`, `sweep/modularize-sections`, etc.)
- Ensure each PR has a clear commit message and references this issue.
- Use placeholders like `{{ author_name }}` or `{{ paper_title }}` where appropriate.
- Label PRs with `template-conversion` and assign reviewers if applicable.

---

### 📚 References

- Original repo: [link to repo]
- Template tool to use: [`copier`](https://copier.readthedocs.io/en/latest/)
