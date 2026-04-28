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
    """creates a datetime variable with today's date"""
    rent_date = datetime.date.today()
    """creates a datetime variable that is 14 days from today's date"""
    due_date = rent_date + datetime.timedelta(days=14)

    """inserts the item id, customer id, today's date, and due date into the rental table"""
    query = (f"INSERT INTO rental (item_id, customer_id, rental_date, due_date) VALUES ('{item_id}', '{customer_id}', "
             f"'{rent_date}', '{due_date}');")
    cur.execute(query)


def waitlist_customer(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's new place in line.
    """
    """calls the line_length function to find the wait list size, then adds 1 to account for the new user"""
    line_size = line_length(item_id) + 1

    """insters the item id, customer id, and wait list position into the waitlist table"""
    query = f"INSERT INTO waitlist (item_id, customer_id, place_in_line) VALUES ('{item_id}', '{customer_id}', {line_size});"
    cur.execute(query)
    return line_size

def update_waitlist(item_id: str = None):
    """
    Removes person at position 1 and shifts everyone else down by 1.
    """
    """deletes the row associated with our item id and that is first in line"""
    query = f"DELETE FROM waitlist WHERE item_id = '{item_id}' AND place_in_line = 1;"
    cur.execute(query)

    """sets all the remaining rows associated with the item id to have their place in line be one step lower"""
    query = f"UPDATE waitlist SET place_in_line = place_in_line-1 WHERE item_id = '{item_id}';"
    cur.execute(query)


def return_item(item_id: str = None, customer_id: str = None):
    """
    Moves a rental from rental to rental_history with return_date = today.
    """
    """selects the row from the rental table with the desired item id and customer id"""
    query = f"SELECT * FROM rental WHERE item_id = '{item_id}' AND customer_id = '{customer_id}';"
    cur.execute(query)
    new_item_id = ""
    new_customer_id = ""
    rent_date = 0
    due_date = 0
    """copies the rental variables into a buffer for later use"""
    for rental in cur:
        new_item_id = rental[0]
        new_customer_id = rental[1]
        rent_date = rental[2]
        due_date = rental[3]
    """sets the return_date to today's date"""
    return_date = datetime.date.today()

    """inserts the buffer variables into rental_history"""
    query = f"INSERT INTO rental_history VALUES ('{new_item_id}', '{new_customer_id}', '{rent_date}', '{due_date}', '{return_date}');"
    cur.execute(query)

    """deletes the old entry from the rental table"""
    query = f"DELETE FROM rental WHERE item_id = '{item_id}' AND customer_id = '{customer_id}';"
    cur.execute(query)



def grant_extension(item_id: str = None, customer_id: str = None):
    """
    Adds 14 days to the due_date.
    """
    """selects row from the rental table with our desired item and customer id"""
    query = f"SELECT * FROM rental WHERE item_id = '{item_id}' AND customer_id = '{customer_id}';"
    cur.execute(query)

    curr_due_date = 0
    """copies the old due date to a buffer and then adds 14 days to it"""
    for row in cur:
        curr_due_date = row[3]
    curr_due_date = curr_due_date + datetime.timedelta(days=14)

    """updates the old due date to have the new date for the entry with our desired item and customer id"""
    query = f"UPDATE rental SET due_date = '{curr_due_date}' WHERE item_id = '{item_id}' AND customer_id = '{customer_id}';"
    cur.execute(query)


def get_filtered_items(filter_attributes: Item = None,
                       use_patterns: bool = False,
                       min_price: float = -1,
                       max_price: float = -1,
                       min_start_year: int = -1,
                       max_start_year: int = -1) -> list[Item]:
    """
    Returns a list of Item objects matching the filters.
    """
    """Selects all the values from item as well as the year from the item start date"""
    query = f"SELECT *, YEAR(i_rec_start_date) FROM item"
    query += f" WHERE i_item_id = '{filter_attributes.item_id}'"
    query += f";"
    cur.execute(query)

    """Creates new Item objects based on the seleted values and passes them into a list of Items"""
    results = []
    for row in cur:
        sel_items = Item(item_id=row[1], product_name=row[3], brand=row[4], category=row[6], manufact=row[7], current_price=row[8], num_owned=row[9], start_year=row[10])
        results.append(sel_items)
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
    """Starts the query with our selection statement"""
    query = f"SELECT * FROM rental"

    """adds a Where clause with our filter attributes"""
    query += f" WHERE customer_id = '{filter_attributes.customer_id}'"
    query += f" AND item_id = '{filter_attributes.item_id}'"

    """finishes the query statement with a ; and executes"""
    query += f";"
    cur.execute(query)
    """Creates a list of Rental objects consisting of the selected rows"""
    results = []
    for row in cur:
        """Creates a Rental object and appends it to the list"""
        sel_rental = Rental(item_id=row[0], customer_id=row[1], rental_date=str(row[2]), due_date=str(row[3]))
        results.append(sel_rental)
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
    """Selects the number of products owned of a given item id"""
    query = f"SELECT i_num_owned FROM item"
    query += f" WHERE i_item_id = '{item_id}'"
    query += f";"
    cur.execute(query)
    """Copies the number of products owned into a buffer"""
    num_owned = 0
    for item in cur:
        num_owned = item[0]

    """Gets the count of instances of a given item id from the rental table, for the number of rented objects"""
    query = f"SELECT COUNT(*) FROM rental"
    query += f" WHERE item_id = '{item_id}'"
    query += f";"
    cur.execute(query)
    """Copies the count of rented items to a buffer"""
    num_rented = 0
    for rented_item in cur:
        num_rented = rented_item[0]

    """returns the number owned - the number rented out, for the total available"""
    return num_owned - num_rented


def place_in_line(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's place_in_line, or -1 if not on waitlist.
    """
    """Gets the position in the wait list for a given item id and customer id"""
    query = f"SELECT place_in_line FROM waitlist"
    query += f" WHERE item_id = '{item_id}' AND customer_id = '{customer_id}'"
    query += f";"
    cur.execute(query)

    """Copies the position in the wait list to a buffer, which defaults to -1 (not on the wait list) if there was
    no selected customer"""
    waitlist_place = -1
    for line_place in cur:
        waitlist_place = line_place[0]

    return waitlist_place


def line_length(item_id: str = None) -> int:
    """
    Returns how many people are on the waitlist for this item.
    """
    """Selects all the rows in the wait list table with a given item id"""
    query = f"SELECT * FROM waitlist"
    query += f" WHERE item_id = '{item_id}'"
    query += f";"
    cur.execute(query)

    """Increments the length of the waitlist by 1 for each row with that item id, 
    defaults to 0 if there is no wait list"""
    waitlist_place = 0
    for line_place in cur:
        waitlist_place += 1

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

