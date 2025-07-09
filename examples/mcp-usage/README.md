# MCP Usage Examples

This directory contains comprehensive examples showing how to use the blender-remote MCP server with LLM-powered IDEs.

## Overview

These examples demonstrate:
- **Basic Operations**: Scene inspection, object creation, code execution
- **Advanced Workflows**: Complex scene creation, animation setup, material creation
- **LLM Integration**: Effective prompting patterns and interaction examples
- **Error Handling**: How to handle errors gracefully in LLM workflows
- **Best Practices**: Optimal usage patterns and performance considerations

## Prerequisites

Before running these examples, ensure you have:

1. **Blender running** with BLD_Remote_MCP addon enabled
2. **MCP server configured** in your IDE
3. **Service connectivity** verified with `uvx blender-remote` test

## Example Categories

### 1. Basic Operations (`01_basic_operations.md`)
- Scene inspection workflows
- Object querying and analysis
- Basic code execution patterns
- Health monitoring

### 2. Object Creation (`02_object_creation.md`)
- Creating primitive objects
- Setting object properties
- Material assignment
- Object positioning and scaling

### 3. Screenshot Workflows (`03_screenshot_workflows.md`)
- Capturing viewport images
- Using screenshots for LLM analysis
- Handling GUI vs background mode
- Visual feedback loops

### 4. Complex Scene Creation (`04_complex_scenes.md`)
- Multi-object scenes
- Complete workflow examples
- Architecture and product visualization
- Animation setup

### 5. LLM Interaction Patterns (`05_llm_patterns.md`)
- Effective prompting strategies
- Multi-step workflows
- Error recovery patterns
- Context management

### 6. Error Handling (`06_error_handling.md`)
- Common error scenarios
- Graceful degradation
- Background mode limitations
- Troubleshooting workflows

## Running Examples

### With LLM IDE
1. Copy the example prompts into your LLM conversation
2. Follow the step-by-step instructions
3. Observe the results in Blender

### Direct Testing
```bash
# Test MCP server directly
pixi run python -m blender_remote.mcp_server

# Use specific examples
pixi run python -c "from examples.mcp_usage.basic_operations import *; run_example()"
```

## Example Structure

Each example follows this pattern:

```markdown
## Example: [Name]

### Description
Brief description of what this example demonstrates.

### LLM Prompt
The exact prompt to use with your LLM.

### Expected Result
What you should see in Blender after running the example.

### Explanation
Technical details about what happened.

### Variations
Alternative approaches or modifications.
```

## Best Practices

### Effective Prompting
- **Be Specific**: "Create a blue metallic cube at (2, 0, 0)" vs "add object"
- **Use Context**: "Based on the current scene, add complementary lighting"
- **Iterate**: Build complex scenes step by step
- **Verify**: Always ask for screenshots to confirm results

### Performance Optimization
- **Batch Operations**: Group related commands in single requests
- **Efficient Queries**: Use specific object queries instead of full scene dumps
- **Screenshot Management**: Use appropriate sizes for your needs
- **Connection Management**: Let the MCP server handle connections

### Error Handling
- **Check Connection**: Start with connection status check
- **Handle Modes**: Account for GUI vs background mode differences
- **Graceful Degradation**: Provide alternatives when features unavailable
- **Clear Messages**: Use error messages to guide next steps

## Troubleshooting

### Common Issues

**Example doesn't work:**
- Verify Blender is running with BLD_Remote_MCP addon
- Check MCP server configuration in your IDE
- Test connection with `uvx blender-remote status`

**Screenshots failing:**
- Ensure Blender is in GUI mode (not `--background`)
- Check if viewport is visible and active
- Try smaller screenshot sizes first

**Code execution errors:**
- Verify Python syntax in code blocks
- Check for typos in object names
- Ensure objects exist before referencing them

### Getting Help

1. **Check Documentation**: [MCP Server Guide](../../docs/mcp-server.md)
2. **Test Direct Connection**: Use CLI tools to verify functionality
3. **Review Logs**: Check Blender console for error messages
4. **Community Support**: Use GitHub discussions for questions

## Contributing Examples

We welcome contributions of new examples! Please:

1. **Follow the structure** shown in existing examples
2. **Test thoroughly** with multiple LLM IDEs
3. **Document clearly** with step-by-step instructions
4. **Include variations** for different use cases
5. **Add error handling** examples where appropriate

### Example Contribution Template

```markdown
## Example: [Your Example Name]

### Description
Clear description of what this example demonstrates and why it's useful.

### Prerequisites
- Any specific Blender setup required
- Objects that should exist in the scene
- Special considerations

### LLM Prompt
```
[Exact prompt text to use with LLM]
```

### Expected Result
- What should appear in Blender
- What the MCP server should return
- Any console output to expect

### Step-by-Step
1. First step with expected result
2. Second step with expected result
3. Continue...

### Variations
- Alternative approaches
- Different parameters to try
- Related techniques

### Common Issues
- Potential problems and solutions
- Error messages and fixes
```

## Advanced Topics

### Custom Tool Development
See [Development Guide](../../docs/development.md) for adding new MCP tools.

### Integration Testing
Examples include integration with the comprehensive test suite.

### Performance Benchmarking
Some examples include performance measurement techniques.

---

**Ready to explore? Start with [Basic Operations](01_basic_operations.md) or jump to [LLM Patterns](05_llm_patterns.md) for advanced techniques!**