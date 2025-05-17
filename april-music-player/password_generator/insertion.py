import random
import string
from _utils.easy_json import EasyJson

class Insertion:
    def __init__(self):
        self.ej = EasyJson()
        ### They are positions of indexes to be inserted in front of them.
        self.onetime_insert_positions = {0, 1, 6, 7}
        self.installment_insert_positions = {2, 3, 5, 6}
        self.onetime_extract_positions = {0, 2, 6, 9, 11}
        self.installment_extract_positions = {2, 4, 6, 8, 10}
        self.numbers_and_characters = string.ascii_letters + string.digits
        self.onetime_keys = "abcde"
        self.installment_keys = "fghij"

    def get_one_time_inserted(self, secret_key) -> str:
        inserted_key = ""
        for i in range(len(secret_key)):
            if i == 4:
                inserted_key += random.choice(self.onetime_keys)
            if i in self.onetime_insert_positions:
                inserted_key += random.choice(self.numbers_and_characters)
            inserted_key += secret_key[i]

        return inserted_key

    def get_installment_inserted(self, secret_key) -> str:
        inserted_key = ""
        for i in range(len(secret_key)):
            if i == 4:
                inserted_key += random.choice(self.installment_keys)
            if i in self.installment_insert_positions:
                inserted_key += random.choice(self.numbers_and_characters)
            inserted_key += secret_key[i]

        return inserted_key

    def get_one_time_extracted_key(self, inserted_key) -> str:
        extracted_key = ""
        for i in range(len(inserted_key)):
            if i in self.onetime_extract_positions:
                continue
            else:
                extracted_key += inserted_key[i]
        return extracted_key

    def get_installment_extracted_key(self, inserted_key) -> str:
        extracted_key = ""
        for i in range(len(inserted_key)):
            if i in self.installment_extract_positions:
                continue
            else:
                extracted_key += inserted_key[i]
        return extracted_key

if __name__ == '__main__':
    secret_key = "zd5@#wq$"

    insertion = Insertion()
    print(f"secret key: {secret_key}")
    inserted_one_time_key = insertion.get_one_time_inserted(secret_key)
    inserted_installment_key = insertion.get_installment_inserted(secret_key)

    print(inserted_one_time_key)
    print(inserted_installment_key)

    print(insertion.get_one_time_extracted_key(inserted_one_time_key))
    print(insertion.get_installment_extracted_key(inserted_installment_key))

    def check_key_type(key):
        if key[6] in insertion.onetime_keys:
            print("it is a one time key")
        elif key[6] in insertion.installment_keys:
            print("it is an installment key")
        else:
            print("it is null")

    check_key_type(inserted_one_time_key)
    check_key_type(inserted_installment_key)