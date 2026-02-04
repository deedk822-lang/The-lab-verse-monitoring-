class PRErrorFixer:
    """Security-hardened error fixer."""

    def __init__(self, agent: OllamaAgent, repo_path: str, validator: SecurityValidator):
        self.agent = agent
        self.repo_path = Path(repo_path)
        self.validator = validator
        self.sanitizer = PromptSanitizer()
        self.llm_validator = LLMResponseValidator()

    def fix_missing_file_error(self, error: str) -> str | None:
        """Fix missing file error securely."""
        match = SafeRegex.safe_search(SafeRegex.FILE_NOT_FOUND, error)
        if not match: return None
        filename = match.group(1)

        try:
            file_path = self.validator.validate_path(filename)
        except SecurityError:
            return None

        if file_path.exists(): return None

        prompt = self.sanitizer.create_safe_prompt(error, f"Generate minimal Python code for file: {filename}")
        try:
            code = self.agent.query(prompt, temperature=0.1)
        except OllamaQueryError:
            return None

        try:
            code_clean = self.llm_validator.validate_code(self._extract_code_block(code))
        except ValueError:
            return None

        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            existing_packages = self._parse_requirements(req_file)
            if validated_module.lower() not in existing_packages:
                with open(req_file, 'a') as f:
                    f.write(f"\n{validated_module}\n")
                return f"Added {validated_module} to requirements.txt"
        return None

    def fix_missing_dependency(self, error: str) -> str | None:
        """Add missing dependencies to requirements files securely."""
        match = SafeRegex.safe_search(SafeRegex.MODULE_NOT_FOUND, error)
        if not match: return None
        module_name = match.group(1)

        try:
            validated_module = self.validator.validate_module_name(module_name)
        except SecurityError:
            return None

        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            existing_packages = self._parse_requirements(req_file)
            if validated_module.lower() not in existing_packages:
                # Check if the dependency exists before adding it
                with open(req_file, 'r') as f:
                    existing_content = f.read()
                
                if module_name not in existing_content:
                    with open(req_file, 'a') as f:
                        f.write(f"\n{validated_module}\n")
                    return f"Added {validated_module} to requirements.txt"
        return None

    def _parse_requirements(self, req_file: Path) -> set:
        packages = set()
        with open(req_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                pkg_name = re.split(r'[<>=\[;]', line)[0].strip()
                packages.add(pkg_name.lower())
        return packages

    def _extract_code_block(self, text: str) -> str:
        match = re.search(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        return match.group(1).strip() if match else text.strip()