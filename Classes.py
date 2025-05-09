# Варіант 15.
# Розробити класи Житлове приміщення, Орендатор, Орендодавець, Договір
# оренди. Реалізувати логіку роботи процесу оренди житла. У одного
# орендодавця може бути декілька житлових приміщень, готових до оренди.
# В договорі фіксується дата старту та закінчення оренди. Одночасно можуть
# створювати заявки декілька орендаторів. Забезпечити блокування
# приміщення при оформленні договору. Пояснити доцільність такого
# підходу.
import time, threading, datetime
from dateutil.relativedelta import relativedelta


class Housing:
    def __init__(self, area: float, address: str):
        self.area = area
        self.address = address
        self.lock = threading.Lock()
    

    def visit(self): # small method for demonstrating visit blocking
        self.lock.acquire()
        print("visit started")
        time.sleep(5)
        print("visit ended")
        self.lock.release()


class Person:
    def __init__(self, name, surname):
        self.name = name
        self.surname = surname


class Landlord(Person):
    _property: list[Housing] = list()


    def __init__(self, name, surname, *_property):
        super().__init__(name, surname)
        for p in _property:
            if type(p) is not Housing:
                raise Exception("property must be Housing type")
            self._property.append(p)


class Lease:
    leases = []


    def __init__(self, landlord: Landlord, tenant: 'Tenant', subject: Housing, length_months: int):
        self.landlord = landlord
        self.tenant = tenant

        if not landlord._property.__contains__(subject):
            raise Exception("Landlord does not own this property")
        self.subject = subject  
        self.length_months = length_months
        
        self.is_signed = False
        Lease.leases.append(self)


    def sign(self):
        self.subject.lock.acquire()

        for l in Lease.leases:
            if l.subject is self.subject and l.is_signed:
                if l.termination < datetime.datetime.now():
                    l.is_signed = False
                else:
                    print(f"This property(house at {self.subject.address}) is already being leased. Lease can't be signed")
                    self.subject.lock.release()
                    return

        print(f"Started signing {self.subject.address} lease...")
        self.is_signed = True
        time.sleep(5)

        current_time = datetime.datetime.now()
        self.sign_date = current_time
        self.termination = current_time + relativedelta(seconds=self.length_months) # for sake of simulation months = seconds
        

        print(f"Finished signing {self.subject.address} lease.")
        self.subject.lock.release()


    def terminate(self):
        self.is_signed = False
        Lease.leases.remove(self)
        print("Lease terminated")


class Tenant(Person):
    leases: list[Lease] = list()
    def __init__(self, name, surname):
        super().__init__(name, surname)


    def create_lease(self, lease: Lease):
        self.leases.append(lease)


if __name__ == "__main__":

    house1 = Housing(54.7, "312 43rd st")
    house2 = Housing(42.2, "55 41st st")

    Lewis = Landlord("Lewis", "Stanfield", house1, house2)
    Tim = Tenant("Tim", "Bradford")

    Tim.create_lease(Lease(Lewis, Tim, house1, 10))
    Tim.create_lease(Lease(Lewis, Tim, house1, 6))

    thread1 = threading.Thread(target=Tim.leases[0].sign, args=())
    thread2 = threading.Thread(target=house1.visit, args=())
    thread3 = threading.Thread(target=Tim.leases[1].sign, args=())

    thread1.start()
    thread2.start()


    time.sleep(15)
    thread3.start()
    thread3.join()
    # # test leasing of already leased subject proofness
    # lease2 = Lease(Lewis, Tim, house1, 6)
    # lease2.sign()
    # assert lease2.is_signed == False
    # time.sleep(11)
    # # lease1 expired
    # lease2.sign()
    # assert lease2.is_signed == True