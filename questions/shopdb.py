"""Synthetic e-commerce questions. DRAFT gold SQL: the author must read and approve every query and
meaning before the test set is frozen. Each entry: (id, difficulty, question, meaning, gold_sql).
Revenue = quantity * order_items.unit_price (price actually paid, in pounds sterling); where a question says "completed
orders" only orders with status = 'completed' count."""

TEST = [
    # ---------------- easy ----------------
    ("SH-E01", "easy", "How many customers do we have?",
     "Rows in customers.", "SELECT count(*) FROM customers"),
    ("SH-E02", "easy", "How many of our customers are in Manchester?",
     "Customers with city Manchester.", "SELECT count(*) FROM customers WHERE city = 'Manchester'"),
    ("SH-E03", "easy", "How many products have been discontinued?",
     "Products with discontinued = true.", "SELECT count(*) FROM products WHERE discontinued"),
    ("SH-E04", "easy", "What is our cheapest product?",
     "Product with the lowest list price.",
     "SELECT product_name FROM products ORDER BY unit_price ASC LIMIT 1"),
    ("SH-E05", "easy", "How many orders were cancelled?",
     "Orders with status cancelled.", "SELECT count(*) FROM orders WHERE status = 'cancelled'"),
    ("SH-E06", "easy", "How many orders came in through the mobile app?",
     "Orders with channel mobile_app.", "SELECT count(*) FROM orders WHERE channel = 'mobile_app'"),
    ("SH-E07", "easy", "What product categories do we have?",
     "Category names, alphabetical.", "SELECT category_name FROM categories ORDER BY category_name"),
    ("SH-E08", "easy", "How many customer accounts are inactive?",
     "Customers with is_active = false.", "SELECT count(*) FROM customers WHERE NOT is_active"),
    ("SH-E09", "easy", "Which discount codes give 20% or more off?",
     "Coupon codes with discount_pct >= 20.", "SELECT code FROM coupons WHERE discount_pct >= 20"),
    ("SH-E10", "easy", "How many items came back because they were damaged?",
     "Rows in returns with reason damaged.", "SELECT count(*) FROM returns WHERE reason = 'damaged'"),
    ("SH-E11", "easy", "How many orders were placed in 2025?",
     "Orders with order_date in calendar year 2025.",
     "SELECT count(*) FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'"),
    ("SH-E12", "easy", "How many product reviews gave 5 stars?",
     "Reviews with rating 5.", "SELECT count(*) FROM reviews WHERE rating = 5"),
    ("SH-E13", "easy", "How many units do we have in stock across all products?",
     "Sum of stock_qty.", "SELECT sum(stock_qty) FROM products"),
    ("SH-E14", "easy", "How many payments failed?",
     "Payments with payment_status failed.", "SELECT count(*) FROM payments WHERE payment_status = 'failed'"),
    ("SH-E15", "easy", "Which carriers do we ship with?",
     "Distinct carriers in shipments, alphabetical.",
     "SELECT DISTINCT carrier FROM shipments ORDER BY carrier"),

    # ---------------- medium ----------------
    ("SH-M01", "medium", "How many orders have we had from each part of the UK?",
     "Per customer region (England, Scotland, Wales, Northern Ireland), number of orders (all statuses).",
     "SELECT c.region, count(*) FROM customers c JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.region"),
    ("SH-M02", "medium", "How many products are there in each category?",
     "Per category name, number of products.",
     "SELECT c.category_name, count(*) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "GROUP BY c.category_name"),
    ("SH-M03", "medium", "What was our revenue from completed orders in 2025?",
     "Sum of quantity * unit_price of order_items on completed orders dated 2025.",
     "SELECT sum(i.quantity * i.unit_price) FROM order_items i JOIN orders o ON o.order_id = i.order_id "
     "WHERE o.status = 'completed' AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01'"),
    ("SH-M04", "medium", "Which categories have more than 8 products?",
     "Category names with more than 8 products.",
     "SELECT c.category_name FROM categories c JOIN products p ON p.category_id = c.category_id "
     "GROUP BY c.category_name HAVING count(*) > 8"),
    ("SH-M05", "medium", "What's the average review rating in each product category?",
     "Per category name, average of reviews.rating.",
     "SELECT c.category_name, avg(r.rating) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN reviews r ON r.product_id = p.product_id GROUP BY c.category_name"),
    ("SH-M06", "medium", "Which sales channel earns us the most from completed orders?",
     "Channel with the highest revenue over completed orders.",
     "SELECT o.channel FROM orders o JOIN order_items i ON i.order_id = o.order_id "
     "WHERE o.status = 'completed' GROUP BY o.channel ORDER BY sum(i.quantity * i.unit_price) DESC LIMIT 1"),
    ("SH-M07", "medium", "Which customers have placed more than 8 orders?",
     "Customer full names with more than 8 orders (all statuses).",
     "SELECT c.full_name FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
     "GROUP BY c.customer_id, c.full_name HAVING count(*) > 8"),
    ("SH-M08", "medium", "How many PayPal payments came from customers in Scotland?",
     "Payments with method paypal on orders of customers whose region is Scotland.",
     "SELECT count(*) FROM payments p JOIN orders o ON o.order_id = p.order_id "
     "JOIN customers c ON c.customer_id = o.customer_id "
     "WHERE p.method = 'paypal' AND c.region = 'Scotland'"),
    ("SH-M09", "medium", "Which products have been returned more than twice?",
     "Product names with more than 2 rows in returns (via order_items).",
     "SELECT p.product_name FROM products p JOIN order_items i ON i.product_id = p.product_id "
     "JOIN returns r ON r.order_item_id = i.order_item_id GROUP BY p.product_id, p.product_name HAVING count(*) > 2"),
    ("SH-M10", "medium", "How many orders used each discount code?",
     "Per coupon code, number of orders that used it.",
     "SELECT c.code, count(*) FROM coupons c JOIN orders o ON o.coupon_id = c.coupon_id GROUP BY c.code"),
    ("SH-M11", "medium", "What's our most reviewed product?",
     "Product name with the most reviews (a single clear winner).",
     "SELECT p.product_name FROM products p JOIN reviews r ON r.product_id = p.product_id "
     "GROUP BY p.product_id, p.product_name ORDER BY count(*) DESC LIMIT 1"),
    ("SH-M12", "medium", "What's our average profit per unit in each category?",
     "Per category name, average of unit_price - unit_cost over products.",
     "SELECT c.category_name, avg(p.unit_price - p.unit_cost) FROM categories c "
     "JOIN products p ON p.category_id = c.category_id GROUP BY c.category_name"),
    ("SH-M13", "medium", "How many customers who signed up in 2024 have placed at least one order?",
     "Distinct customers with signup_date in 2024 and at least one order.",
     "SELECT count(DISTINCT c.customer_id) FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
     "WHERE c.signup_date >= '2024-01-01' AND c.signup_date < '2025-01-01'"),
    ("SH-M14", "medium", "How many customers have never placed an order?",
     "Customers with no rows in orders.",
     "SELECT count(*) FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id WHERE o.order_id IS NULL"),
    ("SH-M15", "medium", "How many returns have there been for products in the Drinks category?",
     "Number of rows in returns whose order item is a product in the category named Drinks.",
     "SELECT count(*) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN order_items i ON i.product_id = p.product_id JOIN returns r ON r.order_item_id = i.order_item_id "
     "WHERE c.category_name = 'Drinks'"),
    ("SH-M16", "medium", "On average, how many days does each carrier take from shipping to delivery?",
     "Per carrier, average of delivered_date - shipped_date, ignoring undelivered shipments.",
     "SELECT carrier, avg(delivered_date - shipped_date) FROM shipments WHERE delivered_date IS NOT NULL "
     "GROUP BY carrier"),
    ("SH-M17", "medium", "How many of our products does each supplier provide?",
     "Per supplier name, number of products.",
     "SELECT s.supplier_name, count(*) FROM suppliers s JOIN products p ON p.supplier_id = s.supplier_id "
     "GROUP BY s.supplier_name"),
    ("SH-M18", "medium", "How many completed orders have customers in Wales placed?",
     "Orders with status completed whose customer region is Wales.",
     "SELECT count(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id "
     "WHERE o.status = 'completed' AND c.region = 'Wales'"),
    ("SH-M19", "medium", "Which products have an average rating below 3.55?",
     "Product names whose average review rating is below 3.55.",
     "SELECT p.product_name FROM products p JOIN reviews r ON r.product_id = p.product_id "
     "GROUP BY p.product_id, p.product_name HAVING avg(r.rating) < 3.55"),
    ("SH-M20", "medium", "How many reviews have customers from London written?",
     "Reviews written by customers whose city is London.",
     "SELECT count(*) FROM reviews r JOIN customers c ON c.customer_id = r.customer_id WHERE c.city = 'London'"),
    ("SH-C01", "complex", "What was our revenue from completed orders in each month of 2025?",
     "Per calendar month of order_date in 2025, sum of quantity * unit_price over completed orders.",
     "SELECT date_trunc('month', o.order_date)::date AS month, sum(i.quantity * i.unit_price) "
     "FROM orders o JOIN order_items i ON i.order_id = o.order_id "
     "WHERE o.status = 'completed' AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01' GROUP BY 1"),
    ("SH-C02", "complex", "Which customer spent the most on completed orders in 2026, and how much?",
     "Full name and total revenue of the top customer over completed orders dated 2026.",
     "SELECT c.full_name, sum(i.quantity * i.unit_price) AS spend FROM customers c "
     "JOIN orders o ON o.customer_id = c.customer_id JOIN order_items i ON i.order_id = o.order_id "
     "WHERE o.status = 'completed' AND o.order_date >= '2026-01-01' AND o.order_date < '2027-01-01' "
     "GROUP BY c.customer_id, c.full_name ORDER BY spend DESC LIMIT 1"),
    ("SH-C03", "complex", "What's the average value of a completed order in each sales channel?",
     "Per channel, total revenue of completed orders divided by number of completed orders.",
     "SELECT o.channel, sum(i.quantity * i.unit_price) / count(DISTINCT o.order_id) FROM orders o "
     "JOIN order_items i ON i.order_id = o.order_id WHERE o.status = 'completed' GROUP BY o.channel"),
    ("SH-C04", "complex", "What percentage of orders were cancelled in each sales channel?",
     "Per channel, 100 * cancelled orders / all orders.",
     "SELECT channel, 100.0 * count(*) FILTER (WHERE status = 'cancelled') / count(*) FROM orders GROUP BY channel"),
    ("SH-C05", "complex", "What's the best-selling product by units in each category, counting completed orders only?",
     "Per category name, product name with the most units sold on completed orders (no ties).",
     "SELECT category_name, product_name FROM (SELECT c.category_name, p.product_name, "
     "rank() OVER (PARTITION BY c.category_name ORDER BY sum(i.quantity) DESC) AS rnk "
     "FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN order_items i ON i.product_id = p.product_id JOIN orders o ON o.order_id = i.order_id "
     "WHERE o.status = 'completed' GROUP BY c.category_name, p.product_id, p.product_name) t WHERE rnk = 1"),
    ("SH-C06", "complex", "How many customers placed orders in both 2025 and 2026?",
     "Customers with at least one order in 2025 and one in 2026 (any status).",
     "SELECT count(*) FROM (SELECT customer_id FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01' "
     "INTERSECT SELECT customer_id FROM orders WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01') t"),
    ("SH-C07", "complex", "How many customers ordered in 2025 but didn't order at all in 2026?",
     "Customers with an order in 2025 and none in 2026 (any status).",
     "SELECT count(*) FROM customers c WHERE c.customer_id IN (SELECT customer_id FROM orders "
     "WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01') AND c.customer_id NOT IN "
     "(SELECT customer_id FROM orders WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01')"),
    ("SH-C08", "complex", "Which product has the highest return rate?",
     "Product name with the highest ratio of rows in returns to rows in order_items for that product "
     "(ties broken by product name).",
     "SELECT p.product_name FROM products p JOIN order_items i ON i.product_id = p.product_id "
     "LEFT JOIN returns r ON r.order_item_id = i.order_item_id "
     "GROUP BY p.product_id, p.product_name ORDER BY count(r.return_id)::numeric / count(i.order_item_id) DESC, "
     "p.product_name LIMIT 1"),
    ("SH-C09", "complex", "On average, how many days pass between a customer signing up and placing their first order?",
     "Average over customers with orders of (first order_date - signup_date) in days.",
     "SELECT avg(f.first_order - c.signup_date) FROM customers c JOIN "
     "(SELECT customer_id, min(order_date) AS first_order FROM orders GROUP BY customer_id) f "
     "ON f.customer_id = c.customer_id"),
    ("SH-C10", "complex", "What share of our completed-order revenue comes from customers in England?",
     "Revenue of completed orders from customers whose region is England divided by total completed revenue.",
     "SELECT sum(i.quantity * i.unit_price) FILTER (WHERE c.region = 'England') / sum(i.quantity * i.unit_price) "
     "FROM orders o JOIN order_items i ON i.order_id = o.order_id JOIN customers c ON c.customer_id = o.customer_id "
     "WHERE o.status = 'completed'"),
    ("SH-C11", "complex", "Which carrier has the fastest average delivery for orders placed through the mobile app?",
     "Carrier with the lowest average (delivered_date - shipped_date) over delivered shipments of mobile_app orders.",
     "SELECT s.carrier FROM shipments s JOIN orders o ON o.order_id = s.order_id "
     "WHERE o.channel = 'mobile_app' AND s.delivered_date IS NOT NULL "
     "GROUP BY s.carrier ORDER BY avg(s.delivered_date - s.shipped_date) ASC LIMIT 1"),
    ("SH-C12", "complex", "Which product's revenue from completed orders grew the most from 2025 to 2026?",
     "Product name with the largest increase in completed-order revenue between 2025 and 2026.",
     "SELECT p.product_name FROM products p JOIN order_items i ON i.product_id = p.product_id "
     "JOIN orders o ON o.order_id = i.order_id WHERE o.status = 'completed' "
     "GROUP BY p.product_id, p.product_name ORDER BY "
     "sum(CASE WHEN o.order_date >= '2026-01-01' AND o.order_date < '2027-01-01' THEN i.quantity * i.unit_price ELSE 0 END) - "
     "sum(CASE WHEN o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01' THEN i.quantity * i.unit_price ELSE 0 END) "
     "DESC LIMIT 1"),
    ("SH-C13", "complex", "How many completed orders contained products from more than 2 different categories?",
     "Completed orders whose items span more than 2 distinct categories.",
     "SELECT count(*) FROM (SELECT o.order_id FROM orders o JOIN order_items i ON i.order_id = o.order_id "
     "JOIN products p ON p.product_id = i.product_id WHERE o.status = 'completed' "
     "GROUP BY o.order_id HAVING count(DISTINCT p.category_id) > 2) t"),
    ("SH-C14", "complex", "Who are our five biggest customers by spend on completed orders, and how much did each spend?",
     "Top 5 customers by completed-order revenue: full name and total.",
     "SELECT c.full_name, sum(i.quantity * i.unit_price) AS spend FROM customers c "
     "JOIN orders o ON o.customer_id = c.customer_id JOIN order_items i ON i.order_id = o.order_id "
     "WHERE o.status = 'completed' GROUP BY c.customer_id, c.full_name ORDER BY spend DESC LIMIT 5"),
    ("SH-C15", "complex", "How much revenue from completed orders did each discount code generate?",
     "Per coupon code, sum of quantity * unit_price over completed orders that used the coupon.",
     "SELECT cp.code, sum(i.quantity * i.unit_price) FROM coupons cp JOIN orders o ON o.coupon_id = cp.coupon_id "
     "JOIN order_items i ON i.order_id = o.order_id WHERE o.status = 'completed' GROUP BY cp.code"),
]

# Development questions: used only to tune prompts and descriptions. Never part of the test set.
DEV = [
    ("SH-D01", "easy", "How many products do we sell?",
     "Rows in products.", "SELECT count(*) FROM products"),
    ("SH-D02", "easy", "How many customers are from Edinburgh?",
     "Customers with city Edinburgh.", "SELECT count(*) FROM customers WHERE city = 'Edinburgh'"),
    ("SH-D03", "medium", "How many orders has each sales channel received?",
     "Per channel, number of orders.", "SELECT channel, count(*) FROM orders GROUP BY channel"),
    ("SH-D04", "medium", "What was our revenue from completed orders in 2026?",
     "Sum of quantity * unit_price on completed orders dated 2026.",
     "SELECT sum(i.quantity * i.unit_price) FROM order_items i JOIN orders o ON o.order_id = i.order_id "
     "WHERE o.status = 'completed' AND o.order_date >= '2026-01-01' AND o.order_date < '2027-01-01'"),
    ("SH-D05", "complex", "What's the average rating of each product category's products reviewed in 2026?",
     "Per category name, average rating of reviews dated 2026.",
     "SELECT c.category_name, avg(r.rating) FROM categories c JOIN products p ON p.category_id = c.category_id "
     "JOIN reviews r ON r.product_id = p.product_id WHERE r.review_date >= '2026-01-01' AND r.review_date < '2027-01-01' "
     "GROUP BY c.category_name"),
]
