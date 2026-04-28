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
    """Select the maximum item secret key identifier, copy it to item_sk, and add 1. This our new item's sk"""
    query = f"SELECT MAX(i_item_sk) FROM item;"
    cur.execute(query)
    item_sk = 0
    for sk in cur:
        item_sk = sk[0]
    item_sk += 1

    start_date = str(new_item.start_year) + "-01-01"
    print(f"Start date: {start_date}, item_sk: {item_sk}")

    query = (f"INSERT INTO item (i_item_sk, i_item_id, i_rec_start_date, i_product_name, "
             f"i_brand, i_category, i_manufact, i_current_price, i_num_owned)"
             f"VALUES ({item_sk}, '{new_item.item_id}', '{start_date}', '{new_item.product_name}', "
             f"'{new_item.brand}', '{new_item.category}', '{new_item.manufact}', {new_item.current_price}, {new_item.num_owned})")

    cur.execute(query)


def add_customer(new_customer: Customer = None):
    """
    new_customer - A Customer object containing a new customer to be inserted into the DB in the customer table.
        new_customer and its attributes will never be None.
    """
    address_sections = new_customer.address.split(",")
    street = address_sections[0].split(" ", 1)
    street_number = street[0]
    street_name = street[1]
    city_name = address_sections[1][1:]
    state_and_zip = address_sections[2][1:].split()
    state = state_and_zip[0]
    zip_code = state_and_zip[1]
    """print(address_sections)
    print(f"Number: {street_number}, Name: {street_name}")
    print(f"City Name: {city_name}")
    print(f"Zip Code: {zip_code}, State: {state}")"""

    query = f"SELECT MAX(ca_address_sk) FROM customer_address;"
    cur.execute(query)
    address_sk = 0
    for sk in cur:
        address_sk = sk[0]
    address_sk += 1

    query = (f"INSERT INTO customer_address VALUES ({address_sk}, '{street_number}', '{street_name}', '{city_name}', "
             f"'{state}', '{zip_code}')")
    cur.execute(query)

    customer_name = new_customer.name.split()
    query = f"SELECT MAX(c_customer_sk) FROM customer;"
    cur.execute(query)
    customer_sk = 0
    for sk in cur:
        customer_sk = sk[0]
    customer_sk += 1

    query = (f"INSERT INTO customer VALUES ({customer_sk}, '{new_customer.customer_id}', '{customer_name[0]}', "
             f"'{customer_name[1]}', '{new_customer.email}', {address_sk})")
    cur.execute(query)


def edit_customer(original_customer_id: str = None, new_customer: Customer = None):
    """
    original_customer_id - A string containing the customer id for the customer to be edited.
    new_customer - A Customer object containing attributes to update. If an attribute is None, it should not be altered.
    """
    """Gets the address sk for the original customer"""
    query = f"SELECT c_current_addr_sk FROM customer WHERE c_customer_id = '{original_customer_id}';"
    cur.execute(query)
    addr_sk = 0
    for row in cur:
        addr_sk = row[0]

    """Updates the customer_address table if a new address is provided"""
    if new_customer.address is not None:
        address_sections = new_customer.address.split(",")
        street = address_sections[0].split(" ", 1)
        street_number = street[0]
        street_name = street[1]
        city_name = address_sections[1][1:]
        state_and_zip = address_sections[2][1:].split()
        state = state_and_zip[0]
        zip_code = state_and_zip[1]

        query = (f"UPDATE customer_address SET ca_street_number = '{street_number}', ca_street_name = '{street_name}', "
                 f"ca_city = '{city_name}', ca_state = '{state}', ca_zip = '{zip_code}' "
                 f"WHERE ca_address_sk = {addr_sk};")
        cur.execute(query)

    """Builds and executes an UPDATE query for the customer table with non-None attributes"""
    query = f"UPDATE customer SET "
    if new_customer.customer_id is not None:
        query += f"c_customer_id = '{new_customer.customer_id}', "
    if new_customer.name is not None:
        customer_name = new_customer.name.split()
        query += f"c_first_name = '{customer_name[0]}', "
        query += f"c_last_name = '{customer_name[1]}', "
    if new_customer.email is not None:
        query += f"c_email_address = '{new_customer.email}', "
    query = query[:-2] + f" WHERE c_customer_id = '{original_customer_id}';"
    cur.execute(query)


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
    op = "LIKE" if use_patterns else "="

    """Checks if any filter attributes or range filters are set"""
    has_filter = (filter_attributes is not None and
                  (filter_attributes.item_id is not None or filter_attributes.product_name is not None
                   or filter_attributes.brand is not None or filter_attributes.category is not None
                   or filter_attributes.manufact is not None
                   or (filter_attributes.current_price is not None and filter_attributes.current_price != -1)
                   or (filter_attributes.num_owned is not None and filter_attributes.num_owned != -1)))
    has_filter = has_filter or min_price != -1 or max_price != -1 or min_start_year != -1 or max_start_year != -1

    """Appends a WHERE clause with the desired filters if any exist"""
    if has_filter:
        query += " WHERE "
        if filter_attributes is not None:
            if filter_attributes.item_id is not None:
                query += f"i_item_id {op} '{filter_attributes.item_id}' AND "
            if filter_attributes.product_name is not None:
                query += f"i_product_name {op} '{filter_attributes.product_name}' AND "
            if filter_attributes.brand is not None:
                query += f"i_brand {op} '{filter_attributes.brand}' AND "
            if filter_attributes.category is not None:
                query += f"i_category {op} '{filter_attributes.category}' AND "
            if filter_attributes.manufact is not None:
                query += f"i_manufact {op} '{filter_attributes.manufact}' AND "
            if filter_attributes.current_price is not None and filter_attributes.current_price != -1:
                query += f"i_current_price = {filter_attributes.current_price} AND "
            if filter_attributes.num_owned is not None and filter_attributes.num_owned != -1:
                query += f"i_num_owned = {filter_attributes.num_owned} AND "
        if min_price != -1:
            query += f"i_current_price >= {min_price} AND "
        if max_price != -1:
            query += f"i_current_price <= {max_price} AND "
        if min_start_year != -1:
            query += f"YEAR(i_rec_start_date) >= {min_start_year} AND "
        if max_start_year != -1:
            query += f"YEAR(i_rec_start_date) <= {max_start_year} AND "
        query = query[:-4] + ";"
    else:
        query += ";"

    cur.execute(query)

    """Creates new Item objects based on the selected values and appends them to a list"""
    results = []
    for row in cur:
        sel_item = Item(item_id=row[1], product_name=row[3], brand=row[4], category=row[6], manufact=row[7], current_price=row[8], num_owned=row[9], start_year=row[10])
        results.append(sel_item)
    return results



def get_filtered_customers(filter_attributes: Customer = None, use_patterns: bool = False) -> list[Customer]:
    """
    Returns a list of Customer objects matching the filters.
    """
    query = f"SELECT * FROM customer"
    op = "LIKE" if use_patterns else "="

    """Checks if any filter attributes are set"""
    has_filter = (filter_attributes is not None and
                  (filter_attributes.customer_id is not None or filter_attributes.name is not None
                   or filter_attributes.email is not None))

    """Appends a WHERE clause with the desired filters if any exist"""
    if has_filter:
        query += " WHERE "
        if filter_attributes.customer_id is not None:
            query += f"c_customer_id {op} '{filter_attributes.customer_id}' AND "
        if filter_attributes.name is not None:
            query += f"CONCAT(TRIM(c_first_name), ' ', TRIM(c_last_name)) {op} '{filter_attributes.name}' AND "
        if filter_attributes.email is not None:
            query += f"c_email_address {op} '{filter_attributes.email}' AND "
        query = query[:-4] + ";"
    else:
        query += ";"

    cur.execute(query)

    """Creates new Customer objects based on the selected values and appends them to a list"""
    results = []
    for row in cur:
        sel_customer = Customer(customer_id=row[1], name=row[2].strip() + " " + row[3].strip(), email=row[4])
        results.append(sel_customer)
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

    """Checks if any filter attributes or range filters are set"""
    has_filter = (filter_attributes is not None and
                  (filter_attributes.item_id is not None or filter_attributes.customer_id is not None
                   or filter_attributes.rental_date is not None or filter_attributes.due_date is not None))
    has_filter = (has_filter or min_rental_date is not None or max_rental_date is not None
                  or min_due_date is not None or max_due_date is not None)

    """Appends a WHERE clause with the desired filters if any exist"""
    if has_filter:
        query += " WHERE "
        if filter_attributes is not None:
            if filter_attributes.item_id is not None:
                query += f"item_id = '{filter_attributes.item_id}' AND "
            if filter_attributes.customer_id is not None:
                query += f"customer_id = '{filter_attributes.customer_id}' AND "
            if filter_attributes.rental_date is not None:
                query += f"rental_date = '{filter_attributes.rental_date}' AND "
            if filter_attributes.due_date is not None:
                query += f"due_date = '{filter_attributes.due_date}' AND "
        if min_rental_date is not None:
            query += f"rental_date >= '{min_rental_date}' AND "
        if max_rental_date is not None:
            query += f"rental_date <= '{max_rental_date}' AND "
        if min_due_date is not None:
            query += f"due_date >= '{min_due_date}' AND "
        if max_due_date is not None:
            query += f"due_date <= '{max_due_date}' AND "
        query = query[:-4] + ";"
    else:
        query += ";"

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
    """Starts the query with our selection statement"""
    query = f"SELECT * FROM rental_history"

    """Checks if any filter attributes or range filters are set"""
    has_filter = (filter_attributes is not None and
                  (filter_attributes.item_id is not None or filter_attributes.customer_id is not None
                   or filter_attributes.rental_date is not None or filter_attributes.due_date is not None
                   or filter_attributes.return_date is not None))
    has_filter = (has_filter or min_rental_date is not None or max_rental_date is not None
                  or min_due_date is not None or max_due_date is not None
                  or min_return_date is not None or max_return_date is not None)

    """Appends a WHERE clause with the desired filters if any exist"""
    if has_filter:
        query += " WHERE "
        if filter_attributes is not None:
            if filter_attributes.item_id is not None:
                query += f"item_id = '{filter_attributes.item_id}' AND "
            if filter_attributes.customer_id is not None:
                query += f"customer_id = '{filter_attributes.customer_id}' AND "
            if filter_attributes.rental_date is not None:
                query += f"rental_date = '{filter_attributes.rental_date}' AND "
            if filter_attributes.due_date is not None:
                query += f"due_date = '{filter_attributes.due_date}' AND "
            if filter_attributes.return_date is not None:
                query += f"return_date = '{filter_attributes.return_date}' AND "
        if min_rental_date is not None:
            query += f"rental_date >= '{min_rental_date}' AND "
        if max_rental_date is not None:
            query += f"rental_date <= '{max_rental_date}' AND "
        if min_due_date is not None:
            query += f"due_date >= '{min_due_date}' AND "
        if max_due_date is not None:
            query += f"due_date <= '{max_due_date}' AND "
        if min_return_date is not None:
            query += f"return_date >= '{min_return_date}' AND "
        if max_return_date is not None:
            query += f"return_date <= '{max_return_date}' AND "
        query = query[:-4] + ";"
    else:
        query += ";"

    cur.execute(query)

    """Creates a list of RentalHistory objects consisting of the selected rows"""
    results = []
    for row in cur:
        """Creates a RentalHistory object and appends it to the list"""
        sel_history = RentalHistory(item_id=row[0], customer_id=row[1], rental_date=str(row[2]), due_date=str(row[3]), return_date=str(row[4]))
        results.append(sel_history)
    return results


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    Returns a list of Waitlist objects matching the filters.
    """
    """Starts the query with our selection statement"""
    query = f"SELECT * FROM waitlist"

    """Checks if any filter attributes or range filters are set"""
    has_filter = (filter_attributes is not None and
                  (filter_attributes.item_id is not None or filter_attributes.customer_id is not None
                   or (filter_attributes.place_in_line is not None and filter_attributes.place_in_line != -1)))
    has_filter = has_filter or min_place_in_line != -1 or max_place_in_line != -1

    """Appends a WHERE clause with the desired filters if any exist"""
    if has_filter:
        query += " WHERE "
        if filter_attributes is not None:
            if filter_attributes.item_id is not None:
                query += f"item_id = '{filter_attributes.item_id}' AND "
            if filter_attributes.customer_id is not None:
                query += f"customer_id = '{filter_attributes.customer_id}' AND "
            if filter_attributes.place_in_line is not None and filter_attributes.place_in_line != -1:
                query += f"place_in_line = {filter_attributes.place_in_line} AND "
        if min_place_in_line != -1:
            query += f"place_in_line >= {min_place_in_line} AND "
        if max_place_in_line != -1:
            query += f"place_in_line <= {max_place_in_line} AND "
        query = query[:-4] + ";"
    else:
        query += ";"

    cur.execute(query)

    """Creates a list of Waitlist objects consisting of the selected rows"""
    results = []
    for row in cur:
        """Creates a Waitlist object and appends it to the list"""
        sel_waitlist = Waitlist(item_id=row[0], customer_id=row[1], place_in_line=row[2])
        results.append(sel_waitlist)
    return results


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

