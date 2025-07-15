#!/usr/bin/env python3
"""
Protocol Comparison Test - Test both protocol formats

This test verifies the protocol differences between services:
- BlenderAutoMCP uses: {"type": "execute_code", "params": {"code": "..."}}
- BLD_Remote_MCP uses: {"code": "...", "message": "..."}
"""

import socket
import json


def test_protocol_format(port, service_name, message_format, test_name):
    """Test a specific protocol format on a service."""
    print(f"\n[TESTING] Testing {service_name} with {test_name}")
    print(f"[SEND] Sending: {json.dumps(message_format)}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(("127.0.0.1", port))

        json_msg = json.dumps(message_format)
        sock.sendall(json_msg.encode("utf-8"))

        response_data = sock.recv(4096)
        response = json.loads(response_data.decode("utf-8"))

        sock.close()

        print(f"[RECEIVE] Response: {response}")

        # Check if response indicates success
        is_success = (
            response.get("response") == "OK"
            or response.get("status") == "success"
            or "error" not in response.get("status", "").lower()
        )

        status = "[PASS] SUCCESS" if is_success else "[FAIL] ERROR"
        print(f"[RESULT] Result: {status}")

        return is_success, response

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        return False, str(e)


def main():
    print("[TESTING] PROTOCOL COMPATIBILITY TEST")
    print("=" * 60)
    print("Testing protocol format compatibility between services")

    # Test formats
    bld_remote_format = {
        "code": "test_result = 'BLD_Remote_format_test'",
        "message": "Testing BLD_Remote_MCP format",
    }

    blender_auto_format = {
        "type": "execute_code",
        "params": {"code": "test_result = 'BlenderAuto_format_test'"},
    }

    print(f"\n[INFO] Protocol Formats Being Tested:")
    print(f"BLD_Remote format: {json.dumps(bld_remote_format)}")
    print(f"BlenderAuto format: {json.dumps(blender_auto_format)}")

    # Test BLD_Remote_MCP with both formats
    print(f"\n" + "=" * 60)
    print("[RESULT] TESTING BLD_REMOTE_MCP (port 6688)")
    print("=" * 60)

    bld_with_bld_format = test_protocol_format(
        6688, "BLD_Remote_MCP", bld_remote_format, "BLD_Remote format"
    )
    bld_with_auto_format = test_protocol_format(
        6688, "BLD_Remote_MCP", blender_auto_format, "BlenderAuto format"
    )

    # Test BlenderAutoMCP with both formats
    print(f"\n" + "=" * 60)
    print("[RESULT] TESTING BLENDERAUTOMCP (port 9876)")
    print("=" * 60)

    auto_with_bld_format = test_protocol_format(
        9876, "BlenderAutoMCP", bld_remote_format, "BLD_Remote format"
    )
    auto_with_auto_format = test_protocol_format(
        9876, "BlenderAutoMCP", blender_auto_format, "BlenderAuto format"
    )

    # Summary
    print(f"\n" + "=" * 60)
    print("[STATS] PROTOCOL COMPATIBILITY SUMMARY")
    print("=" * 60)

    def format_result(success, desc):
        return f"{'[PASS] WORKS' if success else '[FAIL] FAILS':12} - {desc}"

    print("BLD_Remote_MCP Protocol Support:")
    print(f"  {format_result(bld_with_bld_format[0], 'Native BLD_Remote format')}")
    print(
        f"  {format_result(bld_with_auto_format[0], 'BlenderAuto format (compatibility)')}"
    )

    print("\nBlenderAutoMCP Protocol Support:")
    print(
        f"  {format_result(auto_with_bld_format[0], 'BLD_Remote format (compatibility)')}"
    )
    print(f"  {format_result(auto_with_auto_format[0], 'Native BlenderAuto format')}")

    # Analysis
    print(f"\n[INFO] ANALYSIS:")

    bld_supports_both = bld_with_bld_format[0] and bld_with_auto_format[0]
    auto_supports_both = auto_with_bld_format[0] and auto_with_auto_format[0]

    if bld_supports_both and auto_supports_both:
        print("[SUCCESS] FULL COMPATIBILITY: Both services support both protocol formats")
    elif bld_with_bld_format[0] and auto_with_auto_format[0]:
        print("[WARNING] PARTIAL COMPATIBILITY: Each service works with its native format")
        print("   - This explains why BlenderMCPClient works (it translates protocols)")
        print("   - But raw TCP shows differences")
    else:
        print("[FAIL] COMPATIBILITY ISSUES: One or both services have protocol problems")

    # Recommendations
    print(f"\n[TIP] RECOMMENDATIONS:")
    if not bld_with_auto_format[0]:
        print(
            "   [FIX] Add BlenderAuto protocol support to BLD_Remote_MCP for full compatibility"
        )
    if not auto_with_bld_format[0]:
        print("   ℹ️ BlenderAutoMCP doesn't support BLD_Remote format (expected)")

    print("=" * 60)


if __name__ == "__main__":
    main()
