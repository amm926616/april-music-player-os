from datetime import datetime, timedelta
from _utils.easy_json import EasyJson
from password_generator.insertion import Insertion
from program_activation.clock_warning_dialog import ClockWarningDialog

class CheckSubscriptionTime:
    def __init__(self):
        self.datetime_format = "%Y-%m-%d %H:%M:%S.%f"
        self.ej = EasyJson()

    def set_subscription_status_and_time(self, plus_active_days: int):
        # Calculate expiration and current times once
        current_date_time = datetime.now()
        expired_date_time = current_date_time + timedelta(days=plus_active_days)

        # Batch update all values at once
        updates = {
            "active_subscription": True,
            "time_to_expire": str(expired_date_time),
            "previous_login_time": str(current_date_time)
        }

        for key, value in updates.items():
            self.ej.edit_value(key, value)

        # Save changes and print feedback
        self.ej.save_json()
        print(f"Subscription updated for {plus_active_days} days.")

    def check_status(self) -> bool:
        """check subscription status and expired datetime, return true if expired and false if it hasn't.
        This method also checks if the user has breached the system clock use the old time cheating method and
        it will return True if he does so"""
        if not self.ej.get_value("active_subscription"):
            self.ej.printCyan("active_subscription is False")
            return True
        else:
            # if the subscript is active, check for time
            expired_time_str = self.ej.get_value("time_to_expire")
            if not expired_time_str:
                self.ej.printGreen("No Time To Expire value yet")
                return True
            expired_time = datetime.strptime(expired_time_str, self.datetime_format)
            current_time = datetime.now()
            if current_time < expired_time:
                previous_login_time = self.ej.get_value("previous_login_time")
                if not previous_login_time:
                    self.ej.printRed("Previous Login time not set")
                    return True
                else:
                    previous_login_time = datetime.strptime(self.ej.get_value("previous_login_time"), self.datetime_format)
                    if current_time > previous_login_time:
                        self.ej.edit_value("previous_login_time", str(current_time))
                        self.ej.printYellow("It is not expired yet")
                        return False
                    else:
                        ClockWarningDialog().init_ui()
                        self.ej.printRed("User has cheated the clock!")
                        return True
            else:
                return True

    def has_expired(self) -> bool:
        if self.check_status():
            if not self.ej.get_value("activation_keys"):
                self.prepare_passcodes_for_both_one_time_and_installment()
            return True
        else:
            return False

    def prepare_passcodes_for_both_one_time_and_installment(self):
        onetime_secret_key, onetime_passcode = self.ej.generate_activation_codes()
        installment_secret_key, installment_passcode = self.ej.generate_activation_codes()

        insertion = Insertion()

        inserted_onetime_secret_key = insertion.get_one_time_inserted(onetime_secret_key)
        self.ej.printCyan(f"onetime secret key: {onetime_secret_key}")
        self.ej.printGreen(f"onetime inserted secret key: {inserted_onetime_secret_key}")

        inserted_installment_secret_key = insertion.get_installment_inserted(installment_secret_key)
        self.ej.printCyan(f"installment inserted secret key: {installment_secret_key}")
        self.ej.printGreen(f"installment inserted secret key: {inserted_installment_secret_key}")

        activation_keys =  {
            "onetime": {
                "secret_key": inserted_onetime_secret_key,
                "passcode": onetime_passcode,
            },
            "installment": {
                "secret_key": inserted_installment_secret_key,
                "passcode": installment_passcode,
            }
        }

        self.ej.edit_value("activation_keys", activation_keys)
        self.ej.save_json()



