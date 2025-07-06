"""
Command-line interface for blender-remote.
"""

import sys
import argparse

# Future imports from the blender_remote package:
# from blender_remote import BlenderConnection


def main():
    """Main entry point for the blender-remote CLI."""
    parser = argparse.ArgumentParser(
        description="Remote control Blender from the command line",
        prog="blender-remote"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check connection status to Blender"
    )
    
    # Execute command
    exec_parser = subparsers.add_parser(
        "exec",
        help="Execute Python code in Blender"
    )
    exec_parser.add_argument(
        "code",
        help="Python code to execute"
    )
    
    # Render command
    render_parser = subparsers.add_parser(
        "render",
        help="Render the current scene"
    )
    render_parser.add_argument(
        "--output",
        "-o",
        default="render.png",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Placeholder for actual implementation
    print(f"Command '{args.command}' will be implemented soon.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())