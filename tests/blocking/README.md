# Blocking and Concurrency Tests

This directory contains tests for the BLD Remote MCP service's blocking mechanism and multi-client functionality.

## Test Files Overview

### `test_multi_client.py`
Tests multi-client blocking functionality with concurrent connections. Verifies that when multiple clients connect simultaneously, the service properly handles blocking behavior.

### `test_blocking_simple.py`
Simple test to check if blocking is working. Uses a basic approach with one long-running task and one quick task to verify blocking behavior.

### `test_blocking_execute.py`
Tests blocking specifically with two `execute_code` commands. Ensures that when one execute_code command is running, subsequent execute_code commands are properly blocked.

### `test_debug_blocking.py`
Debug script for the blocking mechanism. Provides step-by-step debugging of the blocking functionality with detailed output.

### `test_precise_blocking.py`
Tests blocking with very precise timing. Uses multiple threads with small delays to test the blocking mechanism under precise timing conditions.

## Purpose

These tests verify that the BLD Remote MCP service correctly implements blocking behavior to prevent concurrent execution of commands that could interfere with each other, particularly in Blender's single-threaded Python environment.

## Usage

Run individual tests:
```bash
python test_multi_client.py
python test_blocking_simple.py
python test_blocking_execute.py
python test_debug_blocking.py
python test_precise_blocking.py
```

## Prerequisites

- Blender running with BLD Remote MCP service on port 7777
- Service should be configured to handle blocking properly

## Expected Behavior

When the blocking mechanism is working correctly:
- Only one command should execute at a time
- Additional commands should receive a `blocked` status response
- Long-running commands should complete before new commands start