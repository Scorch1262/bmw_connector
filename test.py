# https://bimmer-connected.readthedocs.io/en/latest/module/vehicle.html
# Enhanced bimmer_connected to custom_bimmer with following changes:
# - Added 'address' to VehicleLocation (location.py, line 54)
# - DEPRECATED: Added 'print' in line 109/110 of account.py to print the raw JSON response for each vehicle. Use vehicle.data instead.
# - Add option to get the 'lastUpdatedAt'-field from the BMW JSON response (vehicle.py, line 179)
# Dependencies generated with pipreqs. bimmer_connected version based on version 0.13.0

import asyncio
import json
import logging
import os
import pytz
import datetime
from bmwcredentials import BMWCredentials
from colorama import Fore, Style
from custom_bimmer.account import MyBMWAccount
from custom_bimmer.api.regions import Regions
from custom_bimmer.vehicle.fuel_and_battery import ChargingState
from custom_bimmer.vehicle.doors_windows import LockState
from custom_bimmer.vehicle.vehicle import VehicleViewDirection


def utc_to_local(utc_timestamp: datetime.datetime) -> datetime.datetime:
    local_timezone = pytz.timezone('Europe/Berlin')
    local_datetime = utc_timestamp.astimezone(local_timezone)
    return local_datetime


def calc_time_dif(time1: datetime.datetime, time2: datetime.datetime) -> str:
    return "Not implemented yet."


async def main():
    try:
        # logging.basicConfig(level=logging.DEBUG)
        credentials = BMWCredentials().getCredentials()
        print("Authentication was successful...")
        account = MyBMWAccount(credentials["username"], credentials["password"], Regions.REST_OF_WORLD)
        await account.get_vehicles()
    except Exception as e:
        print(e)
        return

    print("Found", len(account.vehicles), "vehicles:")
    print("-----------------")
    for vehicle in account.vehicles:
        print(vehicle.brand.name, vehicle.name, "(" + vehicle.vin + ") from", vehicle.data["attributes"]["year"], end=" ")
        print("is EV" if vehicle.has_electric_drivetrain else "has combustion engine")
        # print(vehicle.available_attributes)
        if vehicle.has_electric_drivetrain:
            batData = vehicle.fuel_and_battery
            match batData.charging_status:
                case ChargingState.CHARGING:
                    print("Charging. Will finish on " + batData.charging_end_time.strftime("%d.%m.%Y %H:%M:%S (%Z)"))
                case ChargingState.ERROR:
                    print("Charging error.")
                case ChargingState.COMPLETE:
                    print("Charging complete.")
                case ChargingState.FULLY_CHARGED:
                    print("Charging complete. Vehicle is fully charged.")
                case ChargingState.FINISHED_FULLY_CHARGED:
                    print("Charging finished. Vehicle is fully charged.")
                case ChargingState.FINISHED_NOT_FULL:
                    print("Charging finished. Vehicle is not fully charged.")
                case ChargingState.INVALID:
                    print("Charging invalid.")
                case ChargingState.NOT_CHARGING:
                    print("Not charging.")
                case ChargingState.PLUGGED_IN:
                    print("Plugged in.")
                case ChargingState.WAITING_FOR_CHARGING:
                    print("Waiting for charging.")
                case ChargingState.TARGET_REACHED:
                    print("Charging target reached.")
                case ChargingState.UNKNOWN:
                    print("Charging status unknown.")
                case _:
                    print(f"Error: ChargingState {batData.charging_status} not found")

            print(batData.remaining_battery_percent, "% remaining")
            print(batData.remaining_range_electric.value, batData.remaining_range_electric.unit, "remaining")
        if vehicle.has_combustion_drivetrain:
            engineData = vehicle.fuel_and_battery
            print(engineData.remaining_fuel.value, engineData.remaining_fuel.unit, "remaining")
            print(engineData.remaining_range_fuel.value, engineData.remaining_range_fuel.unit, "remaining")

        if vehicle.is_vehicle_active:
            print("Vehicle is active. Location not available.")
        elif vehicle.vehicle_location.location is None:
            print(f"{Fore.YELLOW}Location not available.{Style.RESET_ALL}")
        else:
            print("Lat:", vehicle.vehicle_location.location.latitude, "Long:", vehicle.vehicle_location.location.longitude,
                  "Heading:", vehicle.vehicle_location.heading, "Address:", vehicle.vehicle_location.address)

        if vehicle.check_control_messages.has_check_control_messages:
            print(Fore.CYAN + "Check Control Message(s): " + str(len(vehicle.check_control_messages.messages)) + Style.RESET_ALL)
            for id, message in enumerate(vehicle.check_control_messages.messages, 1):
                print(f"{Fore.CYAN}{id}. {message.description_short}: {message.state.name}{Style.RESET_ALL}")

        print("Last update:", utc_to_local(vehicle.timestamp).strftime("%d.%m.%Y %H:%M:%S (%Z)"))
        print("Last update from car:", utc_to_local(vehicle.lastUpdatedAt).strftime("%d.%m.%Y %H:%M:%S (%Z)"), end=" ")
        print(f"{Fore.GREEN}(In Operation){Style.RESET_ALL}" if vehicle.is_vehicle_active else "")

        match vehicle.doors_and_windows.door_lock_state:
            case LockState.LOCKED:
                print(Fore.GREEN + "Vehicle locked." + Style.RESET_ALL)
            case LockState.PARTIALLY_LOCKED:
                print(Fore.YELLOW + "Vehicle partially locked." + Style.RESET_ALL)
            case LockState.UNLOCKED:
                print(Fore.RED + "Vehicle not locked!" + Style.RESET_ALL)
            case LockState.SECURED:
                print(Fore.GREEN + "Vehicle secured." + Style.RESET_ALL)
            case LockState.UNKNOWN:
                print("Vehicle lock state unknown.")
            case _:
                print("Unhandled lock state: " + vehicle.doors_and_windows.door_lock_state)

        print("Mileage:", vehicle.mileage.value, vehicle.mileage.unit)

        # Available Service Messages
        # print(vehicle.condition_based_services.messages)

        # Get raw JSON data (dict)
        # print(json.dumps(vehicle.data, indent=4, default=str))

        # Save Image to file
        # Check if file exists
        if not os.path.exists(f"{vehicle.vin}.png"):
            with open(f"{vehicle.vin}.png", "wb") as f:
                image = await vehicle.get_vehicle_image(VehicleViewDirection.FRONTSIDE)
                f.write(image)
                f.close()
        else:
            print("Image already exists.")

        print("-----------------")

    # Example Remote Service
    # vehicle = account.get_vehicle("VIN")
    # result = await vehicle.remote_services.trigger_remote_door_lock()
    # print(f"Status: {result.state.name}")

asyncio.run(main())
