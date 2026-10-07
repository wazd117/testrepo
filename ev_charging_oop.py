from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from math import ceil, isfinite
import re


def valid_text(value, field):
    """Shared validation used by private-attribute setters."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} cannot be empty.")
    return value.strip()

def valid_user_id(user_id):

    if not isinstance(user_id, str):
        raise ValueError("User ID must be a string.")

    if not user_id.isascii() or not user_id.isdigit():
        raise ValueError("User ID must contain only digits 0-9.")
    # must be number


    if len(user_id) != 6:
        raise ValueError("User ID must be exactly 6 digits.")
    #length must be 6

    return user_id

def valid_vehicle_number(vehicle_number):
    if not isinstance(vehicle_number, str):
        raise ValueError("Vehicle number must be a string.")


    vehicle_number = vehicle_number.strip()

    if not vehicle_number:
        raise ValueError("Vehicle number cannot be empty.")

    # resuse other type of number
    if not vehicle_number.isascii():
        raise ValueError(
            "Vehicle number must use English letters and digits 0-9."
        )

    vehicle_number = vehicle_number.upper()

    # check my regular type of car ID
    pattern = (
        r"([ABCDFJKMNPRTVW][A-HJ-NP-Y]{0,2})"
        r" *"
        r"([1-9][0-9]{0,3})"
    )

    match = re.fullmatch(pattern, vehicle_number)

    if match is None:
        raise ValueError(
            "Invalid or unsupported plate format. "
            "Use a standard Peninsular plate such as B123 or ABC1234. "
            "Special and suffix-letter series are not supported."
        )

    return match.group(1) + match.group(2)

def valid_number(value, field, positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{field} must be a valid number.") from None
    if not isfinite(number) or number < 0 or (positive and number == 0):
        limit = "greater than zero" if positive else "zero or greater"
        raise ValueError(f"{field} must be finite and {limit}.")
    return number


def valid_boolean(value, field):
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be True or False.")
    return value


class User(ABC):
    """Abstract parent class: shared profile and charging interface."""

    def __init__(self, user_id, name, email="", balance=0):
        self.__user_id = valid_user_id(user_id)
        self.set_name(name)
        self.set_email(email)
        self.set_balance(balance)

    def get_user_id(self):
        return self.__user_id

    def set_user_id(self, user_id):
        self.__user_id = valid_text(user_id, "User ID")

    def get_name(self):
        return self.__name

    def set_name(self, name):
        self.__name = valid_text(name, "Name")

    def get_email(self):
        return self.__email

    def set_email(self, email):
        if not isinstance(email, str):
            raise ValueError("Email must be text.")
        email = email.strip()
        # Blank is allowed because Table 1/2 billing does not need email.
        if email and (email.count("@") != 1 or " " in email
                      or not all(email.split("@"))):
            raise ValueError("Enter an email with a local part and domain.")
        self.__email = email

    def get_balance(self):
        return self.__balance

    def set_balance(self, balance):
        self.__balance = valid_number(balance, "Balance")

    def request_waiver(self):
        return False

    @abstractmethod
    def calculate_fee(self, gross_fee, charger_type):
        """Common validation; the child overrides the discount behavior."""
        if charger_type not in ("AC", "DC"):
            raise ValueError("Charger type must be AC or DC.")
        return valid_number(gross_fee, "Gross fee")


class MemberUser(User):
    """IS-A User; implements staff, student and regular user pricing."""

    def __init__(self, user_id, name, member_id, member_type,
                 is_first_time=False, has_eco_pass=False,
                 email="", balance=0):
        super().__init__(user_id, name, email, balance)
        self.set_member_id(member_id)
        self.set_member_type(member_type)
        self.set_is_first_time(is_first_time)
        self.set_has_eco_pass(has_eco_pass)

    def get_member_id(self):
        return self.__member_id

    def set_member_id(self, member_id):
        self.__member_id = valid_text(member_id, "Member ID")

    def get_member_type(self):
        return self.__member_type

    def set_member_type(self, member_type):
        member_type = valid_text(member_type, "Member type").upper()
        if member_type not in ("STAFF", "STUDENT", "REGULAR"):
            raise ValueError("Member type must be STAFF, STUDENT or REGULAR.")
        self.__member_type = member_type
        # Derived from category so an arbitrary discount cannot be entered.
        self.__discount_rate = {
            "STAFF": 0.50, "STUDENT": 0.25, "REGULAR": 0.0
        }[member_type]

    def get_discount_rate(self):
        return self.__discount_rate

    def get_is_first_time(self):
        return self.__is_first_time

    def set_is_first_time(self, value):
        self.__is_first_time = valid_boolean(value, "First-time status")

    def get_has_eco_pass(self):
        return self.__has_eco_pass

    def set_has_eco_pass(self, value):
        self.__has_eco_pass = valid_boolean(value, "Eco-Pass status")

    def request_waiver(self):
        return self.__is_first_time

    def calculate_fee(self, gross_fee, charger_type):
        """Override the parent's method: return net CHARGING fee."""
        gross_fee = super().calculate_fee(gross_fee, charger_type)
        if self.request_waiver():
            return 0.0
        if self.__member_type == "STUDENT" and charger_type == "DC":
            return gross_fee
        return round(gross_fee * (1 - self.__discount_rate), 2)


class EVCharger:
    """Hourly charging configuration; rates are fixed by the assignment."""

    def __init__(self, charger_id, location, charger_type):
        self.set_charger_id(charger_id)
        self.set_location(location)
        self.set_charger_type(charger_type)
        self.set_status("AVAILABLE")

    def get_charger_id(self):
        return self.__charger_id

    def set_charger_id(self, charger_id):
        self.__charger_id = valid_text(charger_id, "Charger ID")

    def get_location(self):
        return self.__location

    def set_location(self, location):
        self.__location = valid_text(location, "Location")

    def get_charger_type(self):
        return self.__charger_type

    def set_charger_type(self, charger_type):
        charger_type = valid_text(charger_type, "Charger type").upper()
        if charger_type not in ("AC", "DC"):
            raise ValueError("Charger type must be AC or DC.")
        self.__charger_type = charger_type
        if charger_type == "AC":
            self.__power_rating = 7
            self.__hourly_rates = (4, 6, 8, 12)
            self.__fee_cap = 80
        else:
            self.__power_rating = 50
            self.__hourly_rates = (10, 15, 20, 30)
            self.__fee_cap = 150

    def get_power_rating(self):
        return self.__power_rating

    def get_hourly_rates(self):
        return self.__hourly_rates

    def get_fee_cap(self):
        return self.__fee_cap

    def get_status(self):
        return self.__status

    def set_status(self, status):
        status = valid_text(status, "Status").upper()
        if status not in ("AVAILABLE", "IN_USE", "OUT_OF_SERVICE"):
            raise ValueError("Invalid charger status.")
        self.__status = status

    def is_available(self):
        return self.__status == "AVAILABLE"

    def calculate_gross_fee(self, hours):
        hours = ceil(valid_number(hours, "Charging hours", positive=True))
        rate_1, rate_2, rate_3, rate_4 = self.__hourly_rates
        if hours <= 2:
            fee = hours * rate_1
        elif hours <= 4:
            fee = 2 * rate_1 + (hours - 2) * rate_2
        elif hours <= 6:
            fee = 2 * rate_1 + 2 * rate_2 + (hours - 4) * rate_3
        else:
            fee = (2 * rate_1 + 2 * rate_2 + 2 * rate_3
                   + (hours - 6) * rate_4)
        return float(min(fee, self.__fee_cap))


class ChargingSession:
    """Associates with one User and owns a session-specific EVCharger.

    The owned charger is a configuration snapshot, following the supplied
    UML composition. A real shared physical charger would use association.
    """

    def __init__(self, session_id, user, vehicle_number, charger_type,
                 hours_charged, is_idle=False,
                 needs_card_replacement=False):
        self.set_session_id(session_id)

        if not isinstance(user, User):
            raise ValueError("Session user must be a User object.")

        self.__user = user
        self.set_vehicle_number(vehicle_number)

        self.__charger = EVCharger(
            f"CH-{self.__session_id}",
            "Taylor's Campus",
            charger_type
        )

        # 系统当前时间作为结束时间，明确使用马来西亚 UTC+8。
        malaysia_timezone = timezone(timedelta(hours=8))
        self.__end_time = datetime.now(malaysia_timezone)

        # 根据输入时长计算开始时间，并自动判断高峰。
        self.set_hours_charged(hours_charged)

        self.set_is_idle(is_idle)
        self.set_needs_card_replacement(needs_card_replacement)

    def get_session_id(self):
        return self.__session_id

    def set_session_id(self, session_id):
        self.__session_id = valid_text(session_id, "Session ID")

    def get_user(self):
        return self.__user

    def get_vehicle_number(self):
        return self.__vehicle_number

    def set_vehicle_number(self, vehicle_number):
        self.__vehicle_number = valid_vehicle_number(vehicle_number)

    def get_hours_charged(self):
        return self.__hours_charged

    def set_hours_charged(self, hours):
        hours = valid_number(
            hours, "Charging hours", positive=True
        )

        try:
            start_time = self.__end_time - timedelta(hours=hours)
        except OverflowError:
            raise ValueError(
                "Charging hours exceed the date range."
            ) from None

        self.__hours_charged = hours
        self.__start_time = start_time

        self.__energy_kwh = (
                hours * self.__charger.get_power_rating()
        )

        self.__overtime_minutes = ceil(
            max(0, hours - 6) * 60
        )

        # 每次修改充电时长，都重新判断是否经过高峰。
        self.__is_peak_hour = self.check_peak_hour()

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def get_energy_kwh(self):
        return self.__energy_kwh

    def get_overtime_minutes(self):
        return self.__overtime_minutes

    def get_is_peak_hour(self):
        return self.__is_peak_hour

    def set_is_peak_hour(self, value):
        self.__is_peak_hour = valid_boolean(value, "Peak-hour status")

    def get_is_idle(self):
        return self.__is_idle

    def set_is_idle(self, value):
        self.__is_idle = valid_boolean(value, "Idle status")

    def get_needs_card_replacement(self):
        return self.__needs_card_replacement

    def set_needs_card_replacement(self, value):
        self.__needs_card_replacement = valid_boolean(value, "Card status")

    def apply_surcharge(self):
        return {
            "peak_surcharge": 5.0 if self.__is_peak_hour else 0.0,
            "idle_surcharge": 15.0 if self.__is_idle else 0.0,
            "card_replacement_fee": (
                30.0 if self.__needs_card_replacement else 0.0
            ),
        }

    def calculate_bill(self):
        """Return itemized values without changing user eligibility."""
        gross = self.__charger.calculate_gross_fee(self.__hours_charged)
        # Polymorphism: call the User interface; MemberUser's override runs.
        charging_fee = self.__user.calculate_fee(
            gross, self.__charger.get_charger_type()
        )
        extras = self.apply_surcharge()
        subtotal = charging_fee + sum(extras.values())
        eco_discount = 0.0
        if isinstance(self.__user, MemberUser):
            if self.__user.get_has_eco_pass():
                eco_discount = min(2.0, subtotal)
        return {
            "gross_fee": gross,
            "discount": round(gross - charging_fee, 2),
            **extras,
            "eco_discount": eco_discount,
            "total": round(subtotal - eco_discount, 2),
        }

    def calculate_fee(self):
        """Session-level calculate_fee returns the FINAL amount payable."""
        return self.calculate_bill()["total"]

    def check_peak_hour(self):
        peak_start = self.__start_time.replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        peak_end = self.__start_time.replace(
            hour=16, minute=0, second=0, microsecond=0
        )

        if self.__start_time >= peak_end:
            peak_start += timedelta(days=1)
            peak_end += timedelta(days=1)

        overlap_start = max(self.__start_time, peak_start)
        overlap_end = min(self.__end_time, peak_end)

        return overlap_start < overlap_end

    def generate_bill(self):
        bill = self.calculate_bill()
        category = "REGULAR"
        if isinstance(self.__user, MemberUser):
            category = self.__user.get_member_type()
        discount_label = ("First-time waiver" if self.__user.request_waiver()
                          else "Member discount")
        lines = [
            "=" * 56,
            "       TAYLOR'S SMART CAMPUS EV CHARGING BILL",
            "=" * 56,
            f"Session ID       : {self.__session_id}",
            f"User ID / Name   : {self.__user.get_user_id()} / "
            f"{self.__user.get_name()}",
            f"Vehicle number   : {self.__vehicle_number}",
            f"Member type      : {category}",
            f"Charger type     : {self.__charger.get_charger_type()} "
            f"({self.__charger.get_power_rating()} kW)",
            f"Hours charged    : {self.__hours_charged:g}",
            f"Billable hours   : {ceil(self.__hours_charged)}",
            "-" * 56,
            f"{'Gross charging fee':<29} RM {bill['gross_fee']:8.2f}",
            f"{discount_label:<29}-RM {bill['discount']:8.2f}",
            f"{'Peak surcharge':<29} RM {bill['peak_surcharge']:8.2f}",
            f"{'Idle surcharge':<29} RM {bill['idle_surcharge']:8.2f}",
            f"{'Card replacement fee':<29} RM "
            f"{bill['card_replacement_fee']:8.2f}",
            f"{'Eco-Pass discount':<29}-RM {bill['eco_discount']:8.2f}",
            "-" * 56,
            f"{'TOTAL PAYABLE':<29} RM {bill['total']:8.2f}",
            "=" * 56,
        ]
        return "\n".join(lines)


def read_valid(prompt, validator, strip_input=True):
    while True:
        try:
            value = input(prompt)

            if strip_input:
                value = value.strip()

            return validator(value)

        except ValueError as error:
            print(f"Invalid input: {error}")


def read_choice(prompt, choices):
    def validate(value):
        value = value.upper()
        if value not in choices:
            raise ValueError(f"Choose {' / '.join(choices)}.")
        return value

    return read_valid(prompt, validate)


def read_yes_no(prompt):
    return read_choice(prompt + " (Y/N): ", ("Y", "N")) == "Y"


def input_session(session_number):
    user_id = read_valid(
        "User ID (6 digits): ",
        valid_user_id,
        strip_input=False
    )
    name = read_valid("Name: ",
                      lambda v: valid_text(v, "Name"))
    vehicle = read_valid(
        "Vehicle number (e.g. ABC1234): ",
        valid_vehicle_number
    )
    category = read_choice("Member type (STAFF/STUDENT/REGULAR): ",
                           ("STAFF", "STUDENT", "REGULAR"))
    charger = read_choice("Charger type (AC/DC): ", ("AC", "DC"))
    first_time = read_yes_no("Is this the user's first charge?")
    eco_pass = read_yes_no("Does the user have a Green Eco-Pass?")
    user = MemberUser(user_id, name, user_id, category, first_time, eco_pass)

    # Validation of hours is delegated to the session setter.
    while True:
        try:
            session = ChargingSession(
                f"S{session_number:03d}", user, vehicle, charger,
                input("Hours charged (greater than 0): ")
            )
            break
        except ValueError as error:
            print(f"Invalid input: {error}")
    session.set_is_idle(
        read_yes_no("Did the car occupy the bay after reaching 100% charge?")
    )
    session.set_needs_card_replacement(
        read_yes_no("Is an RFID card replacement required?")
    )
    return session


def main():
    print("Smart Campus EV Charging & Parking Management System")
    processed_sessions = []
    while True:
        print("\n1. Process vehicle(s)\n0. Exit")
        choice = read_choice("Choose an option: ", ("1", "0"))
        if choice == "0":
            print("Session processing ended. Please clock out.")
            break
        else:
            while True:
                session = input_session(len(processed_sessions) + 1)
                processed_sessions.append(session)
                print("\n" + session.generate_bill())
                if not read_yes_no("Process another vehicle?"):
                    break


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nProgram closed.")
