# This is to limit certain accounts from accessing Prod/UAT. Initially created to limit access to UAT,
# then refactored to limit access to PROD environment based on user request
import os


class AccessList:
    blackList = []

    @staticmethod
    def is_allowed(email):
        if os.getenv('webenv') == 'prd' and email in AccessList.blackList:
            return False

        return True
