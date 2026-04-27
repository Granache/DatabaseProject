import datetime

from MARIADB_CREDS import DB_CONFIG
from mariadb import connect
from models.RentalHistory import RentalHistory
from models.Waitlist import Waitlist
from models.Item import Item
from models.Rental import Rental
from models.Customer import Customer
from datetime import date, timedelta


conn = connect(user=DB_CONFIG["username"], password=DB_CONFIG["password"], host=DB_CONFIG["host"],
               database=DB_CONFIG["database"], port=DB_CONFIG["port"])


cur = conn.cursor()


def add_item(new_item: Item = None):
    """
    new_item - An Item object containing a new item to be inserted into the DB in the item table.
        new_item and its attributes will never be None.
    """
    raise NotImplementedError("you must implement this function")


def add_customer(new_customer: Customer = None):
    """
    new_customer - A Customer object containing a new customer to be inserted into the DB in the customer table.
        new_customer and its attributes will never be None.
    """
    raise NotImplementedError("you must implement this function")


def edit_customer(original_customer_id: str = None, new_customer: Customer = None):
    """
    original_customer_id - A string containing the customer id for the customer to be edited.
    new_customer - A Customer object containing attributes to update. If an attribute is None, it should not be altered.
    """
    raise NotImplementedError("you must implement this function")


def rent_item(item_id: str = None, customer_id: str = None):
    """
    item_id - A string containing the Item ID for the item being rented.
    customer_id - A string containing the customer id of the customer renting the item.
    """
    rent_date = datetime.date.today()
    due_date = rent_date + datetime.timedelta(days=14)
    print(f"{due_date}")
    query = (f"INSERT INTO rental (item_id, customer_id, rental_date, due_date) VALUES ('{item_id}', '{customer_id}', "
             f"'{rent_date}', '{due_date}');")
    cur.execute(query)


def waitlist_customer(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's new place in line.
    """
    line_size = line_length(item_id) + 1
    print(f"New place: {line_size}")
    query = f"INSERT INTO waitlist (item_id, customer_id, place_in_line) VALUES ('{item_id}', '{customer_id}', {line_size});"
    cur.execute(query)
    return line_size

def update_waitlist(item_id: str = None):
    """
    Removes person at position 1 and shifts everyone else down by 1.
    """
    raise NotImplementedError("you must implement this function")


def return_item(item_id: str = None, customer_id: str = None):
    """
    Moves a rental from rental to rental_history with return_date = today.
    """
    raise NotImplementedError("you must implement this function")


def grant_extension(item_id: str = None, customer_id: str = None):
    """
    Adds 14 days to the due_date.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_items(filter_attributes: Item = None,
                       use_patterns: bool = False,
                       min_price: float = -1,
                       max_price: float = -1,
                       min_start_year: int = -1,
                       max_start_year: int = -1) -> list[Item]:
    """
    Returns a list of Item objects matching the filters.
    """
    query = f"SELECT * FROM item"
    query += f" WHERE i_item_id = '{filter_attributes.item_id}'"
    query += f";"
    cur.execute(query)
    results = []
    for item in cur:
        results.append(item)
    return results



def get_filtered_customers(filter_attributes: Customer = None, use_patterns: bool = False) -> list[Customer]:
    """
    Returns a list of Customer objects matching the filters.
    """
    query = f"SELECT * FROM customer"
    query += f" WHERE c_customer_id = '{filter_attributes.customer_id}'"
    query += f";"
    cur.execute(query)
    results = []
    for customer in cur:
        results.append(customer)
    return results


def get_filtered_rentals(filter_attributes: Rental = None,
                         min_rental_date: str = None,
                         max_rental_date: str = None,
                         min_due_date: str = None,
                         max_due_date: str = None) -> list[Rental]:
    """
    Returns a list of Rental objects matching the filters.
    """
    print(f"Filter: {filter_attributes}")
    query = f"SELECT * FROM rental"
    query += f" WHERE customer_id = '{filter_attributes.customer_id}'"
    query += f" AND item_id = '{filter_attributes.item_id}'"
    query += f";"
    cur.execute(query)
    results = []
    for rental in cur:
        results.append(rental)
    return results


def get_filtered_rental_histories(filter_attributes: RentalHistory = None,
                                  min_rental_date: str = None,
                                  max_rental_date: str = None,
                                  min_due_date: str = None,
                                  max_due_date: str = None,
                                  min_return_date: str = None,
                                  max_return_date: str = None) -> list[RentalHistory]:
    """
    Returns a list of RentalHistory objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    Returns a list of Waitlist objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def number_in_stock(item_id: str = None) -> int:
    """
    Returns num_owned - active rentals. Returns -1 if item doesn't exist.
    """
    query = f"SELECT i_num_owned FROM item"
    query += f" WHERE i_item_id = '{item_id}'"
    query += f";"
    cur.execute(query)
    num_owned = 0
    for item in cur:
        num_owned = item[0]
    print(f"Number owned: {num_owned}")

    query = f"SELECT COUNT(*) FROM rental"
    query += f" WHERE item_id = '{item_id}'"
    query += f";"
    cur.execute(query)
    num_rented = 0
    for rented_item in cur:
        num_rented = rented_item[0]
    print(f"Number rented: {num_rented}")

    return num_owned - num_rented


def place_in_line(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's place_in_line, or -1 if not on waitlist.
    """
    query = f"SELECT place_in_line FROM waitlist"
    query += f" WHERE item_id = '{item_id}' AND customer_id = '{customer_id}'"
    query += f";"
    cur.execute(query)
    waitlist_place = -1
    for line_place in cur:
        waitlist_place = line_place[0]
    print(f"Place in line: {waitlist_place}")
    return waitlist_place


def line_length(item_id: str = None) -> int:
    """
    Returns how many people are on the waitlist for this item.
    """
    query = f"SELECT * FROM waitlist"
    query += f" WHERE item_id = '{item_id}'"
    query += f";"
    cur.execute(query)
    waitlist_place = 0
    for line_place in cur:
        waitlist_place += 1
    print(f"Line length: {waitlist_place}")
    return waitlist_place


def save_changes():
    """
    Commits all changes made to the db.
    """
    conn.commit()


def close_connection():
    """
    Closes the cursor and connection.
    """
    cur.close()
    conn.close()

