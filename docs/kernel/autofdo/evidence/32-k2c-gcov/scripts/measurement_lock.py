"""Apply the approved shared-flock semantics to the archived K1f board driver."""

def shared_timing(code):
    edits = (
        ('fcntl.LOCK_EX|fcntl.LOCK_NB', 'fcntl.LOCK_SH|fcntl.LOCK_NB'),
        ('dict(lock_acquired=acquired)', "dict(lock_acquired=acquired,lock_mode='shared')"),
        ('dict(lock_held=True,wait_s=', "dict(lock_held=True,lock_mode='shared',wait_s="),
        ("state|dict(lock_held=True)", "state|dict(lock_held=True,lock_mode='shared')"),
        ('        initial()\n', "        with no_build(OUT/'staging-host'):\n            initial()\n"),
        ("    select_variant(OUT/'finish-switch','switch','kbase','finish-switch')\n"
         "    select_variant(OUT/'finish-verify','verify','kbase','finish-verify')",
         "    with no_build(OUT/'finish-host'):\n"
         "        select_variant(OUT/'finish-switch','switch','kbase','finish-switch')\n"
         "        select_variant(OUT/'finish-verify','verify','kbase','finish-verify')"),
        ("                select_variant(OUT/'emergency-switch','switch','kbase','emergency-finish-switch')",
         "                with no_build(OUT/'emergency-switch-host'):\n"
         "                    select_variant(OUT/'emergency-switch','switch','kbase','emergency-finish-switch')"),
    )
    for old, new in edits:
        assert code.count(old) == 1, old
        code = code.replace(old, new, 1)
    return code
