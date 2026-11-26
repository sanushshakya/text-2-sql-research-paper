"""Build the synthetic e-commerce database (reproducible: fixed seed, no real data).

Usage: python db/build_synthetic.py [--dsn "host=... port=... dbname=shopdb user=..."]

A fictional UK online grocery shop (mainstream and world foods, modelled on the kind of ranges sold by UK grocers
such as Tesco, Asda and M18 Foods; no data from any company is used): UK customers with Nepali-heritage names,
UK suppliers, prices in pounds sterling. Eleven tables. customers, categories, products, orders, order_items and payments carry
most questions; shipments, returns, reviews and coupons are mostly distractors that
schema selection has to ignore (or use when a question really needs them).
"""
import argparse
import datetime as dt
import random

import psycopg

SEED = 42
N_CUSTOMERS = 400
N_ORDERS = 1500
START = dt.date(2025, 1, 1)
END = dt.date(2026, 9, 30)  # fixed "today" for the dataset: date questions are relative to this

SCHEMA = """
DROP TABLE IF EXISTS reviews, returns, shipments, payments, order_items, orders,
    coupons, products, suppliers, categories, customers CASCADE;

CREATE TABLE customers (
    customer_id   serial PRIMARY KEY,
    full_name     text NOT NULL,
    email         text NOT NULL UNIQUE,
    city          text NOT NULL,
    region        text NOT NULL,          -- England, Scotland, Wales or Northern Ireland
    postcode_area text NOT NULL,          -- first part of the UK postcode, e.g. M4 or EH1
    signup_date   date NOT NULL,
    is_active     boolean NOT NULL DEFAULT true
);
CREATE TABLE categories (
    category_id   serial PRIMARY KEY,
    category_name text NOT NULL UNIQUE
);
CREATE TABLE suppliers (
    supplier_id   serial PRIMARY KEY,
    supplier_name text NOT NULL,
    city          text NOT NULL,
    region        text NOT NULL
);
CREATE TABLE products (
    product_id    serial PRIMARY KEY,
    product_name  text NOT NULL,
    category_id   int NOT NULL REFERENCES categories,
    supplier_id   int NOT NULL REFERENCES suppliers,
    unit_price    numeric(10,2) NOT NULL,
    unit_cost     numeric(10,2) NOT NULL,
    stock_qty     int NOT NULL,
    discontinued  boolean NOT NULL DEFAULT false
);
CREATE TABLE coupons (
    coupon_id     serial PRIMARY KEY,
    code          text NOT NULL UNIQUE,
    discount_pct  int NOT NULL,
    valid_from    date NOT NULL,
    valid_to      date NOT NULL
);
CREATE TABLE orders (
    order_id      serial PRIMARY KEY,
    customer_id   int NOT NULL REFERENCES customers,
    order_date    date NOT NULL,
    status        text NOT NULL,          -- completed, cancelled, pending
    coupon_id     int REFERENCES coupons,
    channel       text NOT NULL           -- web, mobile_app, marketplace
);
CREATE TABLE order_items (
    order_item_id serial PRIMARY KEY,
    order_id      int NOT NULL REFERENCES orders,
    product_id    int NOT NULL REFERENCES products,
    quantity      int NOT NULL,
    unit_price    numeric(10,2) NOT NULL  -- price paid, may differ from products.unit_price
);
CREATE TABLE payments (
    payment_id    serial PRIMARY KEY,
    order_id      int NOT NULL REFERENCES orders,
    payment_date  date NOT NULL,
    method        text NOT NULL,          -- card, paypal, bank_transfer
    amount        numeric(10,2) NOT NULL,
    payment_status text NOT NULL          -- paid, refunded, failed
);
CREATE TABLE shipments (
    shipment_id   serial PRIMARY KEY,
    order_id      int NOT NULL REFERENCES orders,
    carrier       text NOT NULL,
    shipped_date  date NOT NULL,
    delivered_date date
);
CREATE TABLE returns (
    return_id     serial PRIMARY KEY,
    order_item_id int NOT NULL REFERENCES order_items,
    return_date   date NOT NULL,
    reason        text NOT NULL
);
CREATE TABLE reviews (
    review_id     serial PRIMARY KEY,
    product_id    int NOT NULL REFERENCES products,
    customer_id   int NOT NULL REFERENCES customers,
    rating        int NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date   date NOT NULL
);
"""

UK_CITIES = {   # region -> (cities with postcode areas, weight): everything is UK-based
    "England": ([("London", "SW1"), ("London", "E1"), ("Manchester", "M4"), ("Birmingham", "B1"), ("Leeds", "LS1"),
                 ("Bristol", "BS1"), ("Liverpool", "L1"), ("Newcastle", "NE1"), ("Sheffield", "S1")], 0.80),
    "Scotland": ([("Glasgow", "G1"), ("Edinburgh", "EH1"), ("Aberdeen", "AB10")], 0.10),
    "Wales": ([("Cardiff", "CF10"), ("Swansea", "SA1")], 0.06),
    "Northern Ireland": ([("Belfast", "BT1")], 0.04),
}
SUPPLIERS = [("Himalayan Imports UK Ltd", "Birmingham", "England"), ("Everest Spice Traders Ltd", "Leicester", "England"),
             ("Pennine Fresh Produce Ltd", "Leeds", "England"), ("Thames Wholesale Foods Ltd", "London", "England"),
             ("Mersey Dairy Co-operative", "Liverpool", "England"), ("Severn Bakery Supplies Ltd", "Bristol", "England"),
             ("Tyneside Meat and Fish Ltd", "Newcastle", "England"), ("Clyde Foods Wholesale Ltd", "Glasgow", "Scotland"),
             ("Highland Drinks Distribution Ltd", "Aberdeen", "Scotland"), ("Cambrian Frozen Foods Ltd", "Cardiff", "Wales"),
             ("Lagan Snacks and Confectionery Ltd", "Belfast", "Northern Ireland"), ("Northern Pantry Supplies Ltd", "Manchester", "England")]
FIRST = ["Sanush", "Anish", "Sujan", "Bibek", "Prabin", "Roshan", "Sabin", "Suman", "Sagar", "Kiran", "Bikash", "Rajan",
         "Dipesh", "Nabin", "Pratik", "Ashish", "Manish", "Rohit", "Binod", "Ramesh", "Anita", "Sunita", "Sarita", "Pooja",
         "Sabina", "Kabita", "Rina", "Sushmita", "Asmita", "Nisha", "Binita", "Sapana", "Mina", "Laxmi", "Gita", "Sita"]
LAST = ["Shakya", "Thapa", "Gurung", "Rai", "Limbu", "Sherpa", "Tamang", "Magar", "Adhikari", "Sharma", "Karki", "Poudel",
        "Basnet", "Shrestha", "Maharjan", "Bhandari", "Khadka", "Pandey", "Neupane", "Lama", "Subedi", "Dahal", "Regmi", "Joshi"]
# (product name, typical shelf price in GBP) -- invented prices, not real retailer prices
CATS = {
    "Fresh Produce": [("Bananas 5 pack", 0.95), ("Loose Carrots 1kg", 0.79), ("Onions 1kg", 1.10), ("Tomatoes 6 pack", 1.65),
                      ("Potatoes 2.5kg", 2.20), ("Garlic 3 pack", 0.85), ("Fresh Ginger 100g", 0.60), ("Coriander Bunch", 0.75)],
    "Dairy and Eggs": [("Semi Skimmed Milk 4 pint", 1.55), ("Free Range Eggs 12 pack", 3.20), ("Mature Cheddar 350g", 3.10),
                       ("Natural Yoghurt 500g", 1.10), ("Salted Butter 250g", 2.05), ("Paneer 225g", 2.50), ("Double Cream 300ml", 1.60)],
    "Bakery": [("Wholemeal Sliced Loaf", 1.25), ("White Sliced Loaf", 1.10), ("Plain Naan 4 pack", 1.40), ("Chapati 6 pack", 1.75),
               ("Croissants 4 pack", 1.50), ("Hot Cross Buns 4 pack", 1.30)],
    "Meat and Fish": [("Chicken Breast Fillets 1kg", 6.50), ("Lamb Mince 500g", 5.25), ("Goat Curry Cuts 1kg", 9.50),
                      ("Salmon Fillets 2 pack", 4.75), ("Frozen Prawns 400g", 4.20), ("Beef Mince 500g", 3.90), ("Whole Chicken 1.5kg", 4.80)],
    "Rice, Flour and Pulses": [("Basmati Rice 5kg", 9.50), ("Sona Masoori Rice 10kg", 14.50), ("Chakki Atta Flour 5kg", 6.25),
                               ("Toor Dal 2kg", 5.40), ("Red Lentils 1kg", 2.30), ("Chickpeas 500g", 1.60), ("Black Gram Dal 1kg", 3.20),
                               ("Poha Flattened Rice 500g", 1.90), ("Rice Flour 1kg", 2.10)],
    "Spices and Seasonings": [("Turmeric Powder 200g", 1.80), ("Cumin Seeds 100g", 1.50), ("Garam Masala 100g", 1.70),
                              ("Timur Sichuan Pepper 50g", 3.40), ("Chilli Powder 200g", 1.90), ("Himalayan Pink Salt 500g", 1.60),
                              ("Mustard Oil 1 litre", 4.90), ("Ghee 500g", 6.20)],
    "Snacks and Confectionery": [("Instant Noodles 5 pack", 2.20), ("Salted Crisps 6 pack", 1.80), ("Chocolate Biscuits 300g", 1.45),
                                 ("Roasted Peanuts 400g", 2.40), ("Milk Chocolate Bar 100g", 1.10), ("Bhujia Snack Mix 250g", 1.90),
                                 ("Digestive Biscuits 400g", 1.20), ("Dried Dates 500g", 3.30)],
    "Drinks": [("Black Tea Bags 240 pack", 3.60), ("Masala Chai Mix 400g", 3.90), ("Orange Juice 1 litre", 1.85),
               ("Still Water 6x1.5 litre", 3.10), ("Instant Coffee 200g", 4.80), ("Mango Juice 1 litre", 1.70),
               ("Cola 2 litre", 1.95), ("Lassi Drink 500ml", 1.50)],
    "Frozen Food": [("Chicken Momo 20 pack", 5.50), ("Vegetable Momo 20 pack", 4.80), ("Frozen Peas 1kg", 1.90),
                    ("Paratha 5 pack", 2.10), ("Oven Chips 1.5kg", 2.80), ("Vanilla Ice Cream 2 litre", 3.20)],
    "Household": [("Washing Up Liquid 500ml", 1.40), ("Kitchen Roll 4 pack", 3.20), ("Laundry Capsules 30 pack", 7.50),
                  ("Toilet Roll 9 pack", 4.50), ("Bin Bags 40 pack", 2.60), ("Aluminium Foil 10m", 1.90)],
}
N_PRODUCTS = sum(len(v) for v in CATS.values())


def rand_date(rng, lo, hi):
    return lo + dt.timedelta(days=rng.randint(0, (hi - lo).days))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="host=localhost port=5432 dbname=shopdb user=postgres")
    args = ap.parse_args()
    rng = random.Random(SEED)

    with psycopg.connect(args.dsn, autocommit=False) as con:
        cur = con.cursor()
        cur.execute(SCHEMA)

        # suppliers
        sup_ids = []
        for name, city, region in SUPPLIERS:
            cur.execute("INSERT INTO suppliers (supplier_name,city,region) VALUES (%s,%s,%s) RETURNING supplier_id", (name, city, region))
            sup_ids.append(cur.fetchone()[0])

        # categories + products
        cat_ids = {}
        for name in CATS:
            cur.execute("INSERT INTO categories (category_name) VALUES (%s) RETURNING category_id", (name,))
            cat_ids[name] = cur.fetchone()[0]
        products = []
        for cat, names in CATS.items():
            for n, base in names:
                price = round(base * rng.uniform(0.97, 1.03), 2)
                cost = round(price * rng.uniform(0.55, 0.85), 2)
                cur.execute(
                    "INSERT INTO products (product_name, category_id, supplier_id, unit_price, unit_cost, stock_qty, discontinued)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING product_id",
                    (n, cat_ids[cat], rng.choice(sup_ids), price, cost, rng.randint(0, 400), rng.random() < 0.08),
                )
                products.append((cur.fetchone()[0], price))
        assert len(products) == N_PRODUCTS

        # customers
        cust_ids = []
        for i in range(N_CUSTOMERS):
            region = rng.choices(list(UK_CITIES), [w for _, w in UK_CITIES.values()])[0]
            city, postcode = rng.choice(UK_CITIES[region][0])
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            if i == 0:
                name = "Sanush Shakya"          # the author is customer 1
            while i > 0 and name == "Sanush Shakya":
                name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            cur.execute(
                "INSERT INTO customers (full_name,email,city,region,postcode_area,signup_date,is_active)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING customer_id",
                (name, f"user{i + 1}@example.co.uk", city, region, postcode,
                 rand_date(rng, dt.date(2023, 1, 1), END), rng.random() > 0.07),
            )
            cust_ids.append(cur.fetchone()[0])

        # coupons
        coupon_ids = []
        for code, pct in [("WELCOME10", 10), ("SPRING15", 15), ("SUMMER20", 20), ("VIP25", 25), ("FLASH5", 5)]:
            lo = rand_date(rng, START, dt.date(2026, 3, 1))
            cur.execute("INSERT INTO coupons (code,discount_pct,valid_from,valid_to) VALUES (%s,%s,%s,%s)"
                        " RETURNING coupon_id", (code, pct, lo, lo + dt.timedelta(days=60)))
            coupon_ids.append(cur.fetchone()[0])

        # orders, items, payments, shipments, returns
        carriers = ["Royal Mail", "Evri", "DPD", "Parcelforce"]
        for _ in range(N_ORDERS):
            cid = rng.choice(cust_ids)
            od = rand_date(rng, START, END)
            status = rng.choices(["completed", "cancelled", "pending"], [0.84, 0.10, 0.06])[0]
            cpn = rng.choice(coupon_ids) if rng.random() < 0.15 else None
            cur.execute(
                "INSERT INTO orders (customer_id,order_date,status,coupon_id,channel) VALUES (%s,%s,%s,%s,%s)"
                " RETURNING order_id",
                (cid, od, status, cpn, rng.choices(["web", "mobile_app", "marketplace"], [0.55, 0.30, 0.15])[0]),
            )
            oid = cur.fetchone()[0]
            total = 0.0
            item_ids = []
            for pid, price in rng.sample(products, rng.randint(1, 4)):
                qty = rng.randint(1, 5)
                paid = round(price * rng.choice([1, 1, 1, 0.9, 0.95]), 2)
                cur.execute("INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES (%s,%s,%s,%s)"
                            " RETURNING order_item_id", (oid, pid, qty, paid))
                item_ids.append(cur.fetchone()[0])
                total += qty * paid
            if status != "cancelled":
                pstat = "paid" if status == "completed" else "failed"
                if status == "completed" and rng.random() < 0.04:
                    pstat = "refunded"
                cur.execute("INSERT INTO payments (order_id,payment_date,method,amount,payment_status)"
                            " VALUES (%s,%s,%s,%s,%s)",
                            (oid, od + dt.timedelta(days=rng.randint(0, 2)),
                             rng.choice(["card", "paypal", "bank_transfer"]), round(total, 2), pstat))
            if status == "completed":
                sd = od + dt.timedelta(days=rng.randint(1, 4))
                dd = sd + dt.timedelta(days=rng.randint(1, 7)) if rng.random() < 0.95 else None
                cur.execute("INSERT INTO shipments (order_id,carrier,shipped_date,delivered_date) VALUES (%s,%s,%s,%s)",
                            (oid, rng.choice(carriers), sd, dd))
                if rng.random() < 0.06:
                    cur.execute("INSERT INTO returns (order_item_id,return_date,reason) VALUES (%s,%s,%s)",
                                (rng.choice(item_ids), sd + dt.timedelta(days=rng.randint(5, 20)),
                                 rng.choice(["damaged", "wrong item", "past best before date", "changed mind"])))

        # reviews
        for _ in range(900):
            cur.execute("INSERT INTO reviews (product_id,customer_id,rating,review_date) VALUES (%s,%s,%s,%s)",
                        (rng.choice(products)[0], rng.choice(cust_ids),
                         rng.choices([1, 2, 3, 4, 5], [0.05, 0.08, 0.17, 0.35, 0.35])[0],
                         rand_date(rng, START, END)))
        con.commit()
    print("synthetic database built")


if __name__ == "__main__":
    main()
