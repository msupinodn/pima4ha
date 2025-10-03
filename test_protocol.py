#!/usr/bin/env python3
"""Standalone test script for PIMA protocol."""
import argparse
import asyncio
import logging
import sys
import os

# Add custom_components/pima to path so we can import directly
pima_path = os.path.join(os.path.dirname(__file__), "custom_components/pima")
sys.path.insert(0, pima_path)

# Now import directly - this avoids __init__.py but allows relative imports within pima_protocol.py to work
from pima_protocol import PimaProtocol

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='PIMA Protocol Test - Test PIMA alarm communication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_protocol.py --ip 192.168.1.250 --code 1234
    python test_protocol.py --ip 192.168.1.250 --port 10150 --code 1234
        """
    )

    parser.add_argument('--ip', required=True,
                       help='IP address of your PIMA alarm system')
    parser.add_argument('--port', type=int, default=10150,
                       help='PIMA TCP port (default: 10150)')
    parser.add_argument('--code', required=True,
                       help='Your alarm system user code (4-6 digits)')

    return parser.parse_args()


async def test_status(pima_ip, pima_port, alarm_code):
    """Test getting alarm status."""
    print("\n=== Testing Status Query ===")
    protocol = PimaProtocol(pima_ip, pima_port, alarm_code)

    status = await protocol.async_get_status()
    print(f"Status: {status}")

    return status


async def test_arm_disarm(pima_ip, pima_port, alarm_code):
    """Test arm and disarm commands."""
    protocol = PimaProtocol(pima_ip, pima_port, alarm_code)

    print("\n=== Testing Disarm ===")
    success = await protocol.async_disarm()
    print(f"Disarm: {'✓ Success' if success else '✗ Failed'}")
    await asyncio.sleep(2)

    print("\n=== Testing Arm Away ===")
    success = await protocol.async_arm_away()
    print(f"Arm Away: {'✓ Success' if success else '✗ Failed'}")
    await asyncio.sleep(2)

    print("\n=== Testing Arm Home ===")
    success = await protocol.async_arm_home()
    print(f"Arm Home: {'✓ Success' if success else '✗ Failed'}")
    await asyncio.sleep(2)

    print("\n=== Testing Arm Night ===")
    success = await protocol.async_arm_night()
    print(f"Arm Night: {'✓ Success' if success else '✗ Failed'}")
    await asyncio.sleep(2)

    print("\n=== Final Disarm ===")
    success = await protocol.async_disarm()
    print(f"Disarm: {'✓ Success' if success else '✗ Failed'}")


async def main():
    """Main test function."""
    args = parse_args()

    print("PIMA Protocol Test")
    print("==================")
    print(f"IP: {args.ip}")
    print(f"Port: {args.port}")
    print(f"Code: {'*' * len(args.code)}")

    try:
        # Test status first
        status = await test_status(args.ip, args.port, args.code)

        if status is None:
            print("\n❌ Failed to get status. Check connection settings.")
            return

        # Ask user if they want to test arm/disarm
        response = input("\nTest arm/disarm commands? (y/N): ")
        if response.lower() == 'y':
            await test_arm_disarm(args.ip, args.port, args.code)
        else:
            print("Skipping arm/disarm tests")

        print("\n✅ Tests completed!")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
