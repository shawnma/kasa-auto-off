import asyncio
import argparse
import sys
import logging
from kasa import Discover

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def turn_off_after(dev, delay, alias):
    """Wait for 'delay' seconds and then turn off the device."""
    try:
        logger.info(f"[{alias}] Timer started: sleeping for {delay} seconds...")
        await asyncio.sleep(delay)
        logger.info(f"[{alias}] 2 minutes passed. Turning device OFF.")
        await dev.turn_off()
        logger.info(f"[{alias}] Device turned OFF successfully.")
    except asyncio.CancelledError:
        logger.info(f"[{alias}] Timer cancelled.")
    except Exception as e:
        logger.error(f"[{alias}] Error turning off device: {e}")

async def list_devices():
    logger.info("Discovering Kasa devices on the local network...")
    devices = await Discover.discover()
    if not devices:
        logger.warning("No devices found on the local network!")
        sys.exit(1)
        
    logger.info(f"Found {len(devices)} device(s):")
    for ip, dev in devices.items():
        await dev.update()
        logger.info(f"- \"{dev.alias}\" at IP: {ip} (Type: {dev.device_type.name if hasattr(dev, 'device_type') else 'Unknown'})")

async def monitor_device(target, is_ip=False):
    if is_ip:
        logger.info(f"Connecting to device at IP {target}...")
        try:
            dev = await Discover.discover_single(target)
            await dev.update()
        except Exception as e:
            logger.error(f"Failed to connect to device at {target}: {e}")
            sys.exit(1)
    else:
        logger.info(f"Discovering device by alias: \"{target}\"...")
        devices = await Discover.discover()
        
        matches = []
        for ip, found_dev in devices.items():
            await found_dev.update()
            if found_dev.alias == target:
                matches.append((ip, found_dev))
                
        if len(matches) == 0:
            logger.error(f"Could not find any device with alias \"{target}\".")
            logger.info("Use the 'list' command to see available devices.")
            sys.exit(1)
        elif len(matches) > 1:
            logger.error(f"Found {len(matches)} devices with alias \"{target}\"!")
            for ip, dev in matches:
                logger.info(f"- IP: {ip}")
            logger.info("Please use the IP address instead: monitor --ip <IP>")
            sys.exit(1)
            
        ip, dev = matches[0]
        logger.info(f"Found \"{target}\" at {ip}.")
    
    alias = dev.alias
    logger.info(f"Monitoring '{alias}' ({dev.host})...")
    logger.info("Will scan status every minute. Press Ctrl+C to stop.")

    turn_off_task = None

    while True:
        try:
            # Refresh device status
            await dev.update()
            is_on = dev.is_on
            logger.info(f"[{alias}] Status scan: {'ON' if is_on else 'OFF'}")

            if is_on:
                # If device is ON and we don't have a timer running, start one
                if turn_off_task is None or turn_off_task.done():
                    logger.info(f"[{alias}] Device is ON. Scheduling turn off in 2 minutes (120 seconds).")
                    turn_off_task = asyncio.create_task(turn_off_after(dev, 120, alias))
                else:
                    logger.info(f"[{alias}] Device is ON. Timer is already running.")
            else:
                # If device is OFF, cancel the timer if it was running
                if turn_off_task is not None and not turn_off_task.done():
                    logger.info(f"[{alias}] Device is OFF. Cancelling the scheduled turn OFF timer.")
                    turn_off_task.cancel()
                    # Wait for task to formally cancel
                    try:
                        await turn_off_task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            logger.error(f"[{alias}] Error accessing device: {e}")

        # Wait 1 minute before next scan
        await asyncio.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kasa Device Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # "list" subcommand
    list_parser = subparsers.add_parser("list", help="List all Kasa devices on the local network")
    
    # "monitor" subcommand
    monitor_parser = subparsers.add_parser("monitor", help="Monitor a Kasa device and turn it off after 2 mins if it's on")
    monitor_group = monitor_parser.add_mutually_exclusive_group(required=True)
    monitor_group.add_argument("alias", nargs="?", type=str, help="Alias (name) of the device to monitor")
    monitor_group.add_argument("--ip", type=str, help="IP address of the device to monitor")
    
    args = parser.parse_args()
    
    if args.command == "list":
        try:
            asyncio.run(list_devices())
        except KeyboardInterrupt:
            logger.info("List cancelled by user.")
    elif args.command == "monitor":
        try:
            if args.ip:
                asyncio.run(monitor_device(args.ip, is_ip=True))
            else:
                asyncio.run(monitor_device(args.alias, is_ip=False))
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user.")
    else:
        parser.print_help()
