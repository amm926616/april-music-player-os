from datetime import datetime, timedelta
from _utils.easy_json import EasyJson
from activate_program import ClockWarningDialog

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

    def has_expired(self):
        """check subscription status and expired datetime, return true if expired and false if it hasn't.
        This method also checks if the user has breached the system clock use the old time cheating method and
        it will return True if he does so"""
        if not self.ej.get_value("active_subscription"):
            return True
        else:
            # if the subscript is active, check for time
            expired_time_str = self.ej.get_value("time_to_expire")
            if not expired_time_str:
                return True
            expired_time = datetime.strptime(expired_time_str, self.datetime_format)
            current_time = datetime.now()
            if current_time < expired_time:
                previous_login_time = self.ej.get_value("previous_login_time")
                if not previous_login_time:
                    return True
                else:
                    previous_login_time = datetime.strptime(self.ej.get_value("previous_login_time"), self.datetime_format)
                    if current_time > previous_login_time:
                        self.ej.edit_value("previous_login_time", str(current_time))
                        return False
                    else:
                        ClockWarningDialog().init_ui()
                        return True
            else:
                return True
