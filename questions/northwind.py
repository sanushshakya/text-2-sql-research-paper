"""Northwind questions. DRAFT gold SQL: the author must read and approve every query and meaning
before the test set is frozen. Each entry: (id, difficulty, question, meaning, gold_sql)."""

TEST = [
    # ---------------- easy: single table ----------------
    ("NW-E01", "easy", "How many customers do we have?",
     "Number of rows in customers.",
     "SELECT count(*) FROM customers"),
    ("NW-E02", "easy", "Which countries do our customers come from?",
     "Distinct customer countries, alphabetical.",
     "SELECT DISTINCT country FROM customers ORDER BY country"),
    ("NW-E03", "easy", "How many products are we still selling?",
     "Products not discontinued (discontinued = 0).",
     "SELECT count(*) FROM products WHERE discontinued = 0"),
    ("NW-E04", "easy", "What's our most expensive product and what does it cost?",
     "Highest list price in products.",
     "SELECT product_name, unit_price FROM products ORDER BY unit_price DESC LIMIT 1"),
    ("NW-E05", "easy", "How many orders were placed in 1997?",
     "Orders with order_date in calendar year 1997.",
     "SELECT count(*) FROM orders WHERE order_date >= '1997-01-01' AND order_date < '1998-01-01'"),
    ("NW-E06", "easy", "Which of our suppliers are based in Germany?",
     "Supplier company names with country Germany.",
     "SELECT company_name FROM suppliers WHERE country = 'Germany'"),
    ("NW-E07", "easy", "How many people work for us?",
     "Number of rows in employees.",
     "SELECT count(*) FROM employees"),
    ("NW-E08", "easy", "Which products are out of stock right now?",
     "Products with units_in_stock = 0.",
     "SELECT product_name FROM products WHERE units_in_stock = 0"),
    ("NW-E09", "easy", "What do we pay on average to ship an order?",
     "Average of orders.freight over all orders.",
     "SELECT avg(freight) FROM orders"),
    ("NW-E10", "easy", "How many orders still haven't been shipped?",
     "Orders with a null shipped_date.",
     "SELECT count(*) FROM orders WHERE shipped_date IS NULL"),
    ("NW-E11", "easy", "Which customers are based in London?",
     "Customer company names with city London.",
     "SELECT company_name FROM customers WHERE city = 'London'"),
    ("NW-E12", "easy", "How many units are currently on order across all products?",
     "Sum of products.units_on_order.",
     "SELECT sum(units_on_order) FROM products"),
    ("NW-E13", "easy", "Who are our sales representatives?",
     "First and last name of employees whose title is 'Sales Representative'.",
     "SELECT first_name, last_name FROM employees WHERE title = 'Sales Representative'"),
    ("NW-E14", "easy", "How many of our products cost more than 50?",
     "Products with list price above 50.",
     "SELECT count(*) FROM products WHERE unit_price > 50"),
    ("NW-E15", "easy", "Which shipping companies do we use?",
     "Company names in shippers.",
     "SELECT company_name FROM shippers"),

    # ---------------- medium: joins and filters ----------------
    ("NW-M01", "medium", "How many orders has each customer placed?",
     "Per customer company name, number of orders (customers with no orders are not listed).",
     "SELECT c.company_name, count(*) FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
     "GROUP BY c.company_name"),
    ("NW-M02", "medium", "How many products do we have in each category?",
     "Per category name, count of products.",
     "SELECT c.category_name, count(*) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "GROUP BY c.category_name"),
    ("NW-M03", "medium", "Who supplies our beverages?",
     "Distinct supplier company names of products in category Beverages.",
     "SELECT DISTINCT s.company_name FROM suppliers s JOIN products p ON p.supplier_id = s.supplier_id "
     "JOIN categories c ON c.category_id = p.category_id WHERE c.category_name = 'Beverages'"),
    ("NW-M04", "medium", "Which employee has handled the most orders?",
     "Employee first and last name with the highest number of orders (employee 4 is the unique maximum).",
     "SELECT e.first_name, e.last_name FROM employees e JOIN orders o ON o.employee_id = e.employee_id "
     "GROUP BY e.employee_id, e.first_name, e.last_name ORDER BY count(*) DESC LIMIT 1"),
    ("NW-M05", "medium", "How much revenue did we make in 1997?",
     "Sum of unit_price * quantity * (1 - discount) over order lines of orders placed in 1997.",
     "SELECT sum(d.unit_price * d.quantity * (1 - d.discount)) FROM order_details d "
     "JOIN orders o ON o.order_id = d.order_id "
     "WHERE o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01'"),
    ("NW-M06", "medium", "What are our five best-selling products by units sold?",
     "Top 5 product names by total quantity sold (no ties at the cut-off).",
     "SELECT p.product_name FROM products p JOIN order_details d ON d.product_id = p.product_id "
     "GROUP BY p.product_id, p.product_name ORDER BY sum(d.quantity) DESC LIMIT 5"),
    ("NW-M07", "medium", "Which German customers have placed more than 10 orders?",
     "Company names of customers in Germany with more than 10 orders.",
     "SELECT c.company_name FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
     "WHERE c.country = 'Germany' GROUP BY c.company_name HAVING count(*) > 10"),
    ("NW-M08", "medium", "How many orders went out with each shipping company?",
     "Per shipper company name, number of orders (orders.ship_via).",
     "SELECT s.company_name, count(*) FROM shippers s JOIN orders o ON o.ship_via = s.shipper_id "
     "GROUP BY s.company_name"),
    ("NW-M09", "medium", "Which customers have never ordered anything?",
     "Customer company names with no rows in orders.",
     "SELECT c.company_name FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id "
     "WHERE o.order_id IS NULL"),
    ("NW-M10", "medium", "What's the average discount we give in each product category?",
     "Per category name, average of order_details.discount over all order lines.",
     "SELECT c.category_name, avg(d.discount) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN order_details d ON d.product_id = p.product_id GROUP BY c.category_name"),
    ("NW-M11", "medium", "List each employee together with their manager's name.",
     "Employee last name and manager last name via reports_to (employees without a manager are not listed).",
     "SELECT e.last_name, m.last_name FROM employees e JOIN employees m ON e.reports_to = m.employee_id"),
    ("NW-M12", "medium", "How many orders were shipped after the date the customer wanted them?",
     "Orders where shipped_date is later than required_date.",
     "SELECT count(*) FROM orders WHERE shipped_date > required_date"),
    ("NW-M13", "medium", "How much have we spent on freight for each country we ship to?",
     "Per ship_country, sum of orders.freight.",
     "SELECT ship_country, sum(freight) FROM orders GROUP BY ship_country"),
    ("NW-M14", "medium", "Which suppliers give us more than 3 products?",
     "Supplier company names with more than 3 products.",
     "SELECT s.company_name FROM suppliers s JOIN products p ON p.supplier_id = s.supplier_id "
     "GROUP BY s.company_name HAVING count(*) > 3"),
    ("NW-M15", "medium", "Who are our top 3 customers by total spend?",
     "Top 3 customer company names by sum of unit_price * quantity * (1 - discount).",
     "SELECT c.company_name FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
     "JOIN order_details d ON d.order_id = o.order_id "
     "GROUP BY c.customer_id, c.company_name ORDER BY sum(d.unit_price * d.quantity * (1 - d.discount)) DESC LIMIT 3"),
    ("NW-M16", "medium", "How many different customers ordered something in March 1998?",
     "Distinct customers with an order dated in March 1998.",
     "SELECT count(DISTINCT customer_id) FROM orders WHERE order_date >= '1998-03-01' AND order_date < '1998-04-01'"),
    ("NW-M17", "medium", "Which product category brings in the most money?",
     "Category name with the highest revenue (unit_price * quantity * (1 - discount)).",
     "SELECT c.category_name FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN order_details d ON d.product_id = p.product_id "
     "GROUP BY c.category_name ORDER BY sum(d.unit_price * d.quantity * (1 - d.discount)) DESC LIMIT 1"),
    ("NW-M18", "medium", "How much stock value are we holding in each category?",
     "Per category name, sum of units_in_stock * unit_price (current list price).",
     "SELECT c.category_name, sum(p.units_in_stock * p.unit_price) FROM categories c "
     "JOIN products p ON p.category_id = c.category_id GROUP BY c.category_name"),
    ("NW-M19", "medium", "How many territories does each employee cover?",
     "Per employee last name, number of rows in employee_territories.",
     "SELECT e.last_name, count(*) FROM employees e JOIN employee_territories t ON t.employee_id = e.employee_id "
     "GROUP BY e.employee_id, e.last_name"),
    ("NW-M20", "medium", "Which products come from UK suppliers?",
     "Product names whose supplier country is UK.",
     "SELECT p.product_name FROM products p JOIN suppliers s ON s.supplier_id = p.supplier_id WHERE s.country = 'UK'"),

    # ---------------- complex: several joins, aggregation, dates, subqueries ----------------
    ("NW-C01", "complex", "What was our revenue in each month of 1997?",
     "Per calendar month of order_date in 1997, sum of unit_price * quantity * (1 - discount).",
     "SELECT date_trunc('month', o.order_date)::date AS month, sum(d.unit_price * d.quantity * (1 - d.discount)) "
     "FROM orders o JOIN order_details d ON d.order_id = o.order_id "
     "WHERE o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01' GROUP BY 1"),
    ("NW-C02", "complex", "Which customer spent the most in 1997 and how much was it?",
     "Customer company name and revenue for the top customer by 1997 revenue.",
     "SELECT c.company_name, sum(d.unit_price * d.quantity * (1 - d.discount)) AS spend "
     "FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_details d ON d.order_id = o.order_id "
     "WHERE o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01' "
     "GROUP BY c.customer_id, c.company_name ORDER BY spend DESC LIMIT 1"),
    ("NW-C03", "complex", "On average, how many days does each shipping company take from order to dispatch?",
     "Per shipper, average of (shipped_date - order_date) in days, ignoring unshipped orders.",
     "SELECT s.company_name, avg(o.shipped_date - o.order_date) FROM shippers s "
     "JOIN orders o ON o.ship_via = s.shipper_id WHERE o.shipped_date IS NOT NULL GROUP BY s.company_name"),
    ("NW-C04", "complex", "Which salesperson brought in the most revenue overall?",
     "Employee first and last name with the highest revenue over all orders they handled.",
     "SELECT e.first_name, e.last_name FROM employees e JOIN orders o ON o.employee_id = e.employee_id "
     "JOIN order_details d ON d.order_id = o.order_id GROUP BY e.employee_id, e.first_name, e.last_name "
     "ORDER BY sum(d.unit_price * d.quantity * (1 - d.discount)) DESC LIMIT 1"),
    ("NW-C05", "complex", "What is the best-selling product, by revenue, in each category?",
     "Per category name, the product name with the highest revenue.",
     "SELECT category_name, product_name FROM ("
     "SELECT c.category_name, p.product_name, "
     "rank() OVER (PARTITION BY c.category_name ORDER BY sum(d.unit_price * d.quantity * (1 - d.discount)) DESC) AS rnk "
     "FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN order_details d ON d.product_id = p.product_id GROUP BY c.category_name, p.product_id, p.product_name) t "
     "WHERE rnk = 1"),
    ("NW-C06", "complex", "How many customers ordered in both 1996 and 1997?",
     "Customers with at least one order in 1996 and at least one in 1997.",
     "SELECT count(*) FROM (SELECT customer_id FROM orders WHERE order_date >= '1996-01-01' AND order_date < '1997-01-01' "
     "INTERSECT SELECT customer_id FROM orders WHERE order_date >= '1997-01-01' AND order_date < '1998-01-01') t"),
    ("NW-C07", "complex", "Which products have been bought by customers from at least 17 different countries?",
     "Product names ordered by customers located in 17 or more distinct countries.",
     "SELECT p.product_name FROM products p JOIN order_details d ON d.product_id = p.product_id "
     "JOIN orders o ON o.order_id = d.order_id JOIN customers c ON c.customer_id = o.customer_id "
     "GROUP BY p.product_id, p.product_name HAVING count(DISTINCT c.country) >= 17"),
    ("NW-C08", "complex", "What share of our total revenue comes from our five biggest customers?",
     "Revenue of the top 5 customers divided by total revenue, as a fraction.",
     "WITH r AS (SELECT o.customer_id, sum(d.unit_price * d.quantity * (1 - d.discount)) AS rev "
     "FROM orders o JOIN order_details d ON d.order_id = o.order_id GROUP BY o.customer_id) "
     "SELECT (SELECT sum(rev) FROM (SELECT rev FROM r ORDER BY rev DESC LIMIT 5) t) / (SELECT sum(rev) FROM r)"),
    ("NW-C09", "complex", "Which month of 1997 was our best for revenue?",
     "Calendar month (first day) in 1997 with the highest revenue.",
     "SELECT date_trunc('month', o.order_date)::date FROM orders o JOIN order_details d ON d.order_id = o.order_id "
     "WHERE o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01' "
     "GROUP BY 1 ORDER BY sum(d.unit_price * d.quantity * (1 - d.discount)) DESC LIMIT 1"),
    ("NW-C10", "complex", "Which customers ordered in 1996 but didn't order at all in 1997?",
     "Company names of customers with a 1996 order and no 1997 order.",
     "SELECT c.company_name FROM customers c WHERE c.customer_id IN ("
     "SELECT customer_id FROM orders WHERE order_date >= '1996-01-01' AND order_date < '1997-01-01') "
     "AND c.customer_id NOT IN (SELECT customer_id FROM orders "
     "WHERE order_date >= '1997-01-01' AND order_date < '1998-01-01')"),
    ("NW-C11", "complex", "What's the average order value for customers in each country?",
     "Per customer country, total revenue divided by number of distinct orders.",
     "SELECT c.country, sum(d.unit_price * d.quantity * (1 - d.discount)) / count(DISTINCT o.order_id) "
     "FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_details d ON d.order_id = o.order_id "
     "GROUP BY c.country"),
    ("NW-C12", "complex", "Which five suppliers' products have earned us the most revenue?",
     "Top 5 supplier company names by revenue of their products.",
     "SELECT s.company_name FROM suppliers s JOIN products p ON p.supplier_id = s.supplier_id "
     "JOIN order_details d ON d.product_id = p.product_id "
     "GROUP BY s.supplier_id, s.company_name ORDER BY sum(d.unit_price * d.quantity * (1 - d.discount)) DESC LIMIT 5"),
    ("NW-C13", "complex", "Which employees have handled more orders than the average employee?",
     "Employee last names whose order count exceeds the average order count per employee.",
     "SELECT e.last_name FROM employees e JOIN orders o ON o.employee_id = e.employee_id "
     "GROUP BY e.employee_id, e.last_name HAVING count(*) > "
     "(SELECT count(*)::numeric / count(DISTINCT employee_id) FROM orders)"),
    ("NW-C14", "complex", "How many orders included more than 3 different products?",
     "Orders with more than 3 distinct product_ids in order_details.",
     "SELECT count(*) FROM (SELECT order_id FROM order_details GROUP BY order_id "
     "HAVING count(DISTINCT product_id) > 3) t"),
    ("NW-C15", "complex", "Which product's revenue grew the most from 1996 to 1997?",
     "Product name with the largest increase in revenue between orders placed in 1996 and in 1997.",
     "SELECT p.product_name FROM products p JOIN order_details d ON d.product_id = p.product_id "
     "JOIN orders o ON o.order_id = d.order_id GROUP BY p.product_id, p.product_name "
     "ORDER BY sum(CASE WHEN o.order_date >= '1997-01-01' AND o.order_date < '1998-01-01' "
     "THEN d.unit_price * d.quantity * (1 - d.discount) ELSE 0 END) - "
     "sum(CASE WHEN o.order_date >= '1996-01-01' AND o.order_date < '1997-01-01' "
     "THEN d.unit_price * d.quantity * (1 - d.discount) ELSE 0 END) DESC LIMIT 1"),
]

# Development questions: used only to tune prompts and descriptions. Never part of the test set.
DEV = [
    ("NW-D01", "easy", "How many suppliers do we have?",
     "Rows in suppliers.", "SELECT count(*) FROM suppliers"),
    ("NW-D02", "easy", "Which customers are in the UK?",
     "Customer company names with country UK.", "SELECT company_name FROM customers WHERE country = 'UK'"),
    ("NW-D03", "medium", "How many units of Chai have we sold in total?",
     "Sum of quantity for product named Chai.",
     "SELECT sum(d.quantity) FROM order_details d JOIN products p ON p.product_id = d.product_id "
     "WHERE p.product_name = 'Chai'"),
    ("NW-D04", "medium", "What's the average price of the products in each category?",
     "Per category name, average products.unit_price.",
     "SELECT c.category_name, avg(p.unit_price) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "GROUP BY c.category_name"),
    ("NW-D05", "complex", "How many orders did each employee handle in 1996?",
     "Per employee last name, count of orders with order_date in 1996.",
     "SELECT e.last_name, count(*) FROM employees e JOIN orders o ON o.employee_id = e.employee_id "
     "WHERE o.order_date >= '1996-01-01' AND o.order_date < '1997-01-01' GROUP BY e.employee_id, e.last_name"),
]
