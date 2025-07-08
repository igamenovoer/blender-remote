# How to Use Pixi to Run Python Scripts

This guide explains how to use pixi to run Python scripts in your development environment.

## What is Pixi?

Pixi is a fast, modern package manager for Python and other languages. It creates isolated environments with reproducible dependencies, similar to conda/mamba but with better cross-platform support and faster execution.

## Basic Commands

### Environment Setup

```bash
# Install dependencies from pixi.toml
pixi install

# Enter the pixi environment shell
pixi shell

# Exit the pixi shell
exit
```

### Running Python Scripts

#### 1. Direct Script Execution

```bash
# Run a Python script directly
pixi run python script.py

# Run a Python script with arguments
pixi run python script.py --arg1 value1 --arg2 value2

# Run scripts from different directories
pixi run python src/blender_remote/main.py
pixi run python tests/smoke_test.py
```

#### 2. Using Predefined Tasks

The project defines several tasks in `pixi.toml`. Use them like this:

```bash
# Run tests
pixi run test

# Run tests with coverage
pixi run test-cov

# Run linting
pixi run lint

# Format code
pixi run format

# Type checking
pixi run typecheck

# Development install
pixi run dev
```

#### 3. Running Scripts in Development Environment

```bash
# Use the dev environment with additional tools (jupyter, ipython)
pixi run --environment dev python script.py

# Start IPython in dev environment
pixi run --environment dev ipython

# Start Jupyter in dev environment
pixi run --environment dev jupyter notebook
```

## Advanced Usage

### Running One-off Commands

```bash
# Run a command without installing dependencies to the project
pixi exec python --version

# Run with specific Python version
pixi exec --spec "python=3.11" python --version

# Run with additional packages
pixi exec --spec "python pandas numpy" python -c "import pandas; print(pandas.__version__)"
```

### Environment Management

```bash
# Show information about the current environment
pixi info

# List all installed packages
pixi list

# Show dependency tree
pixi tree

# Clean environment (remove cached files)
pixi clean
```

### Adding New Dependencies

```bash
# Add a new package
pixi add numpy

# Add development-only dependency
pixi add --feature dev pytest-mock

# Add platform-specific dependency
pixi add --platform linux-64 some-linux-package
```

## Common Workflows

### 1. Running Tests

```bash
# Quick test run
pixi run test

# Test with coverage report
pixi run test-cov

# Run specific test file
pixi run python -m pytest tests/test_specific.py

# Run tests with verbose output
pixi run python -m pytest tests/ -v
```

### 2. Development Workflow

```bash
# Install in development mode
pixi run dev

# Format and lint code
pixi run format
pixi run lint

# Type check
pixi run typecheck

# Run your script
pixi run python your_script.py
```

### 3. Interactive Development

```bash
# Start IPython (dev environment)
pixi run --environment dev ipython

# Start Jupyter notebook
pixi run --environment dev jupyter notebook

# Or enter shell and work interactively
pixi shell
python
>>> import your_module
>>> # Interactive development
>>> exit()
exit  # Exit pixi shell
```

## Tips and Best Practices

### 1. Environment Isolation
- Each pixi project has its own isolated environment
- Dependencies are locked in `pixi.lock` for reproducibility
- No need to worry about conflicting package versions

### 2. Cross-Platform Compatibility
- Pixi works consistently across Linux, macOS, and Windows
- Platform-specific dependencies are handled automatically
- Tasks defined in `pixi.toml` work on all platforms

### 3. Performance
- Pixi is faster than conda for most operations
- Environments are cached and reused when possible
- Use `pixi run` instead of activating environments manually

### 4. Debugging
```bash
# Check what's in your environment
pixi list

# Get detailed information
pixi info

# Check for issues
pixi install --frozen  # Use locked versions only
```

### 5. Working with Multiple Environments
```bash
# List available environments
pixi info

# Run in specific environment
pixi run --environment dev python script.py

# Shell into specific environment
pixi shell --environment dev
```

## Troubleshooting

### Common Issues

1. **Script not found**: Make sure you're in the right directory or use absolute paths
2. **Import errors**: Run `pixi install` to ensure all dependencies are installed
3. **Permission errors**: Check file permissions and use `pixi run` instead of direct execution
4. **Environment issues**: Try `pixi clean` and `pixi install` to rebuild environment

### Getting Help

```bash
# General help
pixi help

# Help for specific command
pixi help run
pixi help add
pixi help install
```

## Examples from This Project

```bash
# Run the smoke test
pixi run python tests/smoke_test.py

# Run the MCP service starter
pixi run python start_bld_remote.py

# Run comparison tests
pixi run python run_comparison_test.py

# Start development server
pixi run --environment dev python scripts/start_bld_remote_background.py
```

This guide should help you effectively use pixi to run Python scripts in your development workflow!
