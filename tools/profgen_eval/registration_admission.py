"""Evaluation command admission. Never expand response files."""
def validate_generation_argv(argv):
    for arg in argv:
        if not isinstance(arg,str):
            raise ValueError("non_string_argv")
        if arg.startswith("@"):
            raise ValueError("response_file_not_admitted")
        if arg.split("=",1)[0] in ("-ip-test-inject-failure","--ip-test-inject-failure"):
            raise ValueError("test_injection_not_admitted")
    return True
