async def generate_secure_content(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate security-aware content of the requested type using the GLM service.
    
    Generates structured content for the given content_type and context, evaluates it for security issues, requests an enhanced version that addresses those issues, and returns the enhanced content if it is valid JSON; otherwise returns the raw enhanced text with the original generated content.
        
    Parameters:
        content_type (str): Identifier of the kind of content to generate (e.g., "policy", "remediation_plan", "alert_summary").
        context (Dict[str, Any]): Contextual data used to guide content generation.
        
    Returns:
        Dict[str, Any]: The enhanced content parsed from JSON when possible; otherwise a dictionary with keys:
                - "content": the enhanced content as a string,
                - "original": the initially generated structured content.
    """
    # First, use GLM-4.7 to generate content
    generated_content = await self.glm.generate_structured_content(content_type, context)

    # Then, analyze the generated content for security issues
    security_analysis = await self.glm.analyze_content_security(
        json.dumps(generated_content, indent=2)
    )

    # Enhance content based on security analysis
    enhanced_prompt = f"""
    Enhance this content based on security recommendations:
    Original content: {json.dumps(generated_content, indent=2)}
    Security analysis: {json.dumps(security_analysis, indent=2)}

    Return improved content that addresses the security concerns while maintaining quality.
    """

    enhanced_content = await self.glm.generate_text(enhanced_prompt)

    try:
        return json.loads(enhanced_content)
    except json.JSONDecodeError:
        # Log the error and provide a fallback value
        self.logger.error(f"Failed to parse enhanced content as JSON: {generated_content}")
        enhanced_content = generated_content  # Provide raw enhanced text

    return {"content": enhanced_content, "original": generated_content}