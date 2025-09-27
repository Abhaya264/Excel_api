#!/usr/bin/env python3
"""
Simple test to verify MCP server is working
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_server_basic():
    """Basic test of MCP server functionality."""
    
    print("🧪 Testing MCP Server...")
    print("=" * 40)
    
    # Start the MCP server process
    server_path = Path("mcpServer/edg_mcp_server.py")
    if not server_path.exists():
        print(f"❌ Server file not found: {server_path}")
        print("💡 Make sure you're running from the correct directory")
        return
    
    print(f"📁 Found server file: {server_path}")
    print("🚀 Starting MCP server subprocess...")
    
    try:
        # Start MCP server as subprocess
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ MCP server process started")
        print(f"📊 Process ID: {process.pid}")
        
        # Wait a moment for startup
        await asyncio.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ MCP server is running")
        else:
            print("❌ MCP server exited early")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return
        
        # Send a basic MCP initialization message
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialization request...")
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Wait for response (with timeout)
        try:
            # Read response line
            response_line = await asyncio.wait_for(
                asyncio.to_thread(process.stdout.readline), 
                timeout=5.0
            )
            
            if response_line:
                print("📥 Received response!")
                try:
                    response = json.loads(response_line.strip())
                    print("✅ Valid JSON response received")
                    print(f"🔍 Response ID: {response.get('id', 'N/A')}")
                    
                    if 'result' in response:
                        print("✅ Initialization successful!")
                        capabilities = response['result'].get('capabilities', {})
                        print(f"🛠️  Server capabilities: {list(capabilities.keys())}")
                    else:
                        print("⚠️  Unexpected response format")
                        print(f"📄 Response: {response}")
                        
                except json.JSONDecodeError:
                    print("❌ Invalid JSON in response")
                    print(f"📄 Raw response: {response_line}")
            else:
                print("❌ No response received")
                
        except asyncio.TimeoutError:
            print("⏰ Timeout waiting for response")
            
        # Test listing tools
        print("\n🔧 Testing tools list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        request_json = json.dumps(tools_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        try:
            response_line = await asyncio.wait_for(
                asyncio.to_thread(process.stdout.readline), 
                timeout=3.0
            )
            
            if response_line:
                response = json.loads(response_line.strip())
                if 'result' in response:
                    tools = response['result'].get('tools', [])
                    print(f"✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                else:
                    print("❌ Tools list request failed")
                    print(f"📄 Response: {response}")
            
        except (asyncio.TimeoutError, json.JSONDecodeError) as e:
            print(f"❌ Error getting tools list: {e}")
        
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        
    finally:
        # Clean up
        if 'process' in locals():
            print("\n🧹 Cleaning up...")
            process.terminate()
            try:
                process.wait(timeout=3)
                print("✅ Server process terminated")
            except subprocess.TimeoutExpired:
                process.kill()
                print("🔥 Server process killed")

def check_mcp_imports():
    """Check if MCP dependencies are available."""
    print("🔍 Checking MCP dependencies...")
    
    required_imports = [
        ('mcp.server', 'Server'),
        ('mcp.server.stdio', 'stdio_server'),
        ('mcp.types', 'Tool'),
        ('httpx', None)
    ]
    
    all_good = True
    for module, item in required_imports:
        try:
            if item:
                exec(f"from {module} import {item}")
            else:
                exec(f"import {module}")
            print(f"✅ {module}" + (f".{item}" if item else ""))
        except ImportError as e:
            print(f"❌ {module}" + (f".{item}" if item else "") + f" - {e}")
            all_good = False
    
    return all_good

async def main():
    print("🧪 MCP Server Diagnostic Tool")
    print("=" * 40)
    
    # Check imports first
    if not check_mcp_imports():
        print("\n💡 Install missing dependencies:")
        print("pip install mcp httpx")
        return
    
    print("\n")
    await test_mcp_server_basic()
    
    print("\n" + "=" * 40)
    print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())