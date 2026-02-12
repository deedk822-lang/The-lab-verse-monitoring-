validator = SecurityValidator(repo_path="path/to/repo")
try:
    valid_path = validator.validate_path("/etc/passwd")
    print(valid_path)
except SecurityError as e:
    print(e)

try:
    valid_module_name = validator.validate_module_name("user-input-module")
    print(valid_module_name)
except SecurityError as e:
    print(e)

try:
    is_valid_extension = validator.validate_file_extension("example.txt")
    print(is_valid_extension)
except SecurityError as e:
    print(e)

sanitized_input = validator.sanitize_input(" sensitive data \n here!")
print(sanitized_input)