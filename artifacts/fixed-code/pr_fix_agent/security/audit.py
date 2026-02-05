The suggested code contains a few improvements to enhance the security of the audit logger and prevent potential issues such as:

1. **Duplicate Handlers**: Ensures that only one `FileHandler` is created per instance, preventing duplicate log files.
2. **Propagate**: Disables propagation to avoid interference with other logging handlers or root logger.
3. **Singleton Pattern**: Ensures that only one `AuditLogger` instance exists in the application.

### Key Changes:
1. **Disable Propagation**:
   ```python
   # ✅ FIX: Disable propagation to prevent root logger interference
   self.logger.propagate = False
   ```

2. **Check for Existing Handlers**:
   ```python
   existing_handler = None
   for handler in self.logger.handlers:
       if isinstance(handler, logging.FileHandler):
           # Check if it's the same file
           if hasattr(handler, 'baseFilename') and \
                  handler.baseFilename == str(self.log_path.resolve()):
                existing_handler = handler
                break

   if existing_handler is None:
       # Create append-only file handler
       handler = logging.FileHandler(
           self.log_path,
           mode='a',  # Append only (immutable)
           encoding='utf-8',
       )
       handler.setFormatter(logging.Formatter('%(message)s'))

       self.logger.addHandler(handler)
   else:
       # Handler already exists, no need to add
       pass
   ```

3. **Thread-Safe Singleton**:
   ```python
   @lru_cache
   def get_audit_logger() -> AuditLogger:
       settings = get_settings()
       return AuditLogger(settings.audit_log_path)
   ```

### Additional Considerations:
- **File Path**: Ensure that the `audit_log_path` is properly configured to avoid issues with path manipulation.
- **Logging Format**: The current format of the log messages includes `timestamp`, which may not be necessary for all use cases. Consider simplifying or using more specific timestamps if needed.
- **Error Handling**: Add error handling to manage exceptions that might occur during log file operations.

By these changes, the audit logger becomes more secure and maintainable.