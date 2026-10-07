"""Task 2: Procedural Smart Campus EV charging and parking billing.

Assumptions:
- Hourly rates are cumulative tiers; partial hours round up.
- The AC/DC fee cap applies to gross charging fees before discounts.
- First-time users receive a charging-fee waiver, not a surcharge waiver.
- The attendant confirms whether each special condition applies.
- Eco-Pass reduces the total bill by up to RM 2, without a negative bill.
"""

import math
import re
from datetime import datetime, timedelta, timezone


def calculate_gross_fee(charger_type, hours_charged):
    billable_hours = math.ceil(hours_charged)

    if charger_type == "AC":
        rate_1 = 4
        rate_2 = 6
        rate_3 = 8
        rate_4 = 12
        fee_limit = 80
    elif charger_type == "DC":
        rate_1 = 10
        rate_2 = 15
        rate_3 = 20
        rate_4 = 30
        fee_limit = 150
    else:
        raise ValueError("Charger type must be AC or DC.")

    if billable_hours <= 2:
        gross_fee = billable_hours * rate_1
    elif billable_hours <= 4:
        gross_fee = 2 * rate_1 + (billable_hours - 2) * rate_2
    elif billable_hours <= 6:
        gross_fee = (
            2 * rate_1
            + 2 * rate_2
            + (billable_hours - 4) * rate_3
        )
    else:
        gross_fee = (
            2 * rate_1
            + 2 * rate_2
            + 2 * rate_3
            + (billable_hours - 6) * rate_4
        )

    gross_fee = min(gross_fee, fee_limit)
    return gross_fee, billable_hours
    """Return the gross fee and the rounded-up billable hours."""


def read_yes_no(prompt):
    """asking about wheather their another person."""
    answer = input(prompt).strip().upper()

    while answer not in ["Y", "N"]:
        answer = input("Please enter Y or N: ").strip().upper()

    return answer == "Y"


def calculate_discount(is_first_time, member_type, charger_type, gross_fee):
    """Return the first-time waiver or the applicable member discount."""
    if is_first_time:
        discount_amount = gross_fee
    elif member_type == "STAFF":
        discount_amount = gross_fee * 0.50
    elif member_type == "STUDENT" and charger_type == "AC":
        discount_amount = gross_fee * 0.25
    else:
        discount_amount = 0

    return discount_amount


def calculate_extra_fees(is_peak_hour, is_idle, needs_card_replacement):
    """Return peak, idle and card replacement fees separately."""
    if is_peak_hour:
        peak_surcharge = 5
    else:
        peak_surcharge = 0

    if is_idle:
        idle_surcharge = 15
    else:
        idle_surcharge = 0

    if needs_card_replacement:
        card_replacement_fee = 30
    else:
        card_replacement_fee = 0

    return peak_surcharge, idle_surcharge, card_replacement_fee


def calculate_and_display_bill(
    user_id,
    name,
    member_type,
    is_first_time,
    has_eco_pass,
    vehicle_number,
    charger_type,
    hours_charged,
    is_peak_hour,
    is_idle,
    needs_card_replacement,
):
    """Calculate all fees and print an itemized bill for one vehicle."""
    gross_fee, billable_hours = calculate_gross_fee(
        charger_type, hours_charged
    )
    discount_amount = calculate_discount(
        is_first_time, member_type, charger_type, gross_fee
    )
    peak_surcharge, idle_surcharge, card_replacement_fee = (
        calculate_extra_fees(
            is_peak_hour, is_idle, needs_card_replacement
        )
    )

    subtotal = (
        gross_fee
        - discount_amount
        + peak_surcharge
        + idle_surcharge
        + card_replacement_fee
    )

    # Only deduct the available amount when the subtotal is below RM 2.
    if has_eco_pass:
        eco_discount = min(2, subtotal)
    else:
        eco_discount = 0

    total_fee = subtotal - eco_discount

    print("\n" + "=" * 54)
    print("TAYLOR'S SMART CAMPUS - EV CHARGING BILL")
    print("=" * 54)
    print(f"User ID: {user_id}")
    print(f"Name: {name}")
    print(f"Vehicle Number: {vehicle_number}")
    print(f"Member Type: {member_type}")
    print(f"Charger Type: {charger_type}")
    print(f"Hours Charged: {hours_charged}")
    print(f"Billable Hours: {billable_hours}")
    print(f"First-Time User: {'Yes' if is_first_time else 'No'}")
    print(f"Green Eco-Pass: {'Yes' if has_eco_pass else 'No'}")
    print("-" * 54)
    print(f"Gross Charging Fee:         RM {gross_fee:.2f}")
    print(f"First-Time / Member Discount: -RM {discount_amount:.2f}")
    print(f"Peak Surcharge:             RM {peak_surcharge:.2f}")
    print(f"Idle Surcharge:             RM {idle_surcharge:.2f}")
    print(f"Card Replacement Fee:       RM {card_replacement_fee:.2f}")
    print(f"Eco-Pass Discount:         -RM {eco_discount:.2f}")
    print("-" * 54)
    print(f"Total Payable:              RM {total_fee:.2f}")
    print("=" * 54)

def is_valid_vehicle_number(vehicle_number):
    pattern = r"[A-HJ-NP-Y]{1,3}[1-9][0-9]{0,3}"
    return re.fullmatch(pattern, vehicle_number) is not None


def main():
    """Read session data and process vehicles until the attendant exits."""
    print("Welcome to Taylor's Smart Campus EV Billing System.")
    process_another = "Y"

    while process_another == "Y":
        print("\nEnter details for the next charging session.")

        user_id = input("Enter user ID: ").strip()
        while not (
            len(user_id) ==7
            and user_id.isdigit()
        ):
            print('ileagal User ID')
            user_id = input("try again please. Enter user ID: ").strip()

        name = input("Enter name: ").strip()
        while not name:
            name = input("Name cannot be empty. Enter name: ").strip()

        vehicle_number = input("Enter vehicle number: ")
        vehicle_number = vehicle_number.strip().upper().replace(" ", "")

        while not is_valid_vehicle_number(vehicle_number):
            print("Invalid or unsupported plate format. Example: ABC1234")
            vehicle_number = input("Enter vehicle number again: ")
            vehicle_number = vehicle_number.strip().upper().replace(" ", "")

        member_type = input(
            "Enter member type (STAFF / STUDENT / REGULAR): "
        ).strip().upper()
        while member_type not in ["STAFF", "STUDENT", "REGULAR"]:
            member_type = input(
                "Invalid member type. Enter STAFF, STUDENT or REGULAR: "
            ).strip().upper()

        charger_type = input("Enter charger type (AC / DC): ").strip().upper()
        while charger_type not in ["AC", "DC"]:
            charger_type = input(
                "Invalid charger type. Enter AC or DC: "
            ).strip().upper()

        valid_hours = False
        while not valid_hours:
            hours_input = input("Enter charging hours (greater than 0): ")
            try:
                hours_charged = float(hours_input)
            except ValueError:
                print("Please enter a valid number.")
            else:
                if math.isfinite(hours_charged) and hours_charged > 0:
                    valid_hours = True
                else:
                    print("Charging hours must be a finite number above 0.")

        is_first_time = read_yes_no(
            "Is this the user's first charge? (Y/N): "
        )
        has_eco_pass = read_yes_no(
            "Does the user hold a Green Eco-Pass? (Y/N): "
        )
        is_idle = read_yes_no(
            "Did the vehicle remain in the bay after 100% charge? (Y/N): "
        )
        needs_card_replacement = read_yes_no(
            "Is an RFID card replacement required? (Y/N): "
        )

        malaysia_timezone = timezone(timedelta(hours=8))
        current_time = datetime.now(malaysia_timezone)

        is_peak_hour = 12 <= current_time.hour < 16

        print(
            "Current Malaysia time:",
            current_time.strftime("%Y-%m-%d %H:%M:%S")
        )

        calculate_and_display_bill(
            user_id,
            name,
            member_type,
            is_first_time,
            has_eco_pass,
            vehicle_number,
            charger_type,
            hours_charged,
            is_peak_hour,
            is_idle,
            needs_card_replacement,
        )

        process_another = input(
            "\nProcess another vehicle? (Y/N): "
        ).strip().upper()
        while process_another not in ["Y", "N"]:
            process_another = input(
                "Please enter Y or N: "
            ).strip().upper()

    print("Thank you. Please clock out.")


if __name__ == "__main__":
    main()
