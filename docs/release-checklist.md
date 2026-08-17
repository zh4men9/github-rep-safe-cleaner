# Release checklist

- [ ] Full diff reviewed
- [ ] `python -m compileall -q src scripts tests`
- [ ] `python scripts/check_safety.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] Offline demo generated
- [ ] GitHub Actions passed
- [ ] Memory Bank and handoff agree with code
- [ ] No mutation capability or secret introduced
- [ ] Real-account acceptance status is explicit
