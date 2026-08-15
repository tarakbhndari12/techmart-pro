# TechMart Pro - Electronics Shop Management System
# Module 8 Submission: Backup and Export Module — Complete Application
# All modules fully enabled. This is the final complete submission.

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import csv
import os
import shutil
import matplotlib.pyplot as plt
from datetime import datetime

# ─────────────────────────────────────────────
# App-wide color and font settings
# ─────────────────────────────────────────────

BG_DARK   = '#0d1117'
BG_MID    = '#161b22'
BG_CARD   = '#1c2128'
SIDEBAR   = '#0d1117'
ENTRY_BG  = '#21262d'
LIST_BG   = '#0d1117'
RO_BG     = '#1a1f27'
ACCENT    = '#2f81f7'
ACCENT2   = '#f78166'
SUCCESS   = '#3fb950'
BLUE      = '#388bfd'
DANGER    = '#da3633'
MUTED     = '#30363d'
TEXT      = '#e6edf3'
TEXT_DIM  = '#8b949e'
BTN_HOVER = '#1f6feb'
WARN      = '#d29922'

FONT_TITLE   = ('Georgia', 20, 'bold')
FONT_HEADING = ('Georgia', 14, 'bold')
FONT_LABEL   = ('Helvetica', 11)
FONT_ENTRY   = ('Helvetica', 11)
FONT_BUTTON  = ('Helvetica', 10, 'bold')
FONT_MONO    = ('Courier', 10)
FONT_SMALL   = ('Helvetica', 9)

DB_PATH    = 'techmart.db'
BACKUP_DIR = 'techmart_backups'
EXPORT_DIR = 'techmart_exports'

# ─────────────────────────────────────────────
# Database setup
# ─────────────────────────────────────────────

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sku           TEXT UNIQUE,
            name          TEXT,
            brand         TEXT,
            category      TEXT,
            cost_price    REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            margin        REAL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sku           TEXT UNIQUE,
            name          TEXT,
            opening_stock INTEGER DEFAULT 0,
            stock_in      INTEGER DEFAULT 0,
            stock_out     INTEGER DEFAULT 0,
            closing_stock INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 5
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            sku          TEXT,
            product_name TEXT,
            quantity     INTEGER,
            unit_price   REAL,
            discount     REAL DEFAULT 0,
            cogs         REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            payment_mode TEXT,
            staff        TEXT,
            timestamp    TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor       TEXT,
            sku          TEXT,
            product_name TEXT,
            qty          INTEGER,
            unit_cost    REAL,
            total        REAL,
            date         TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            amount   REAL,
            date     TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT,
            role       TEXT,
            salary     REAL,
            attendance INTEGER DEFAULT 0
        )
    """)

    # Migration fix: rename old column 'margin_percent' to 'margin' if needed
    cur.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cur.fetchall()]
    if 'margin_percent' in columns and 'margin' not in columns:
        cur.execute("ALTER TABLE products RENAME COLUMN margin_percent TO margin")
    elif 'margin' not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN margin REAL DEFAULT 0")

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# Simple database helper functions
# ─────────────────────────────────────────────

def db_fetchall(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def db_fetchone(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row

def db_execute(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# Product lookup helpers (used across modules)
# ─────────────────────────────────────────────

def get_all_sku_options():
    # Returns list like ["SKU001 — Samsung TV", ...]
    rows = db_fetchall("SELECT sku, name FROM products ORDER BY name")
    result = []
    for r in rows:
        result.append(r[0] + "  —  " + r[1])
    return result

def extract_sku(combo_value):
    # Pulls just the SKU part from "SKU001 — Samsung TV"
    if "  —  " in combo_value:
        return combo_value.split("  —  ")[0].strip()
    return combo_value.strip()

def get_product_selling_price(sku):
    row = db_fetchone("SELECT selling_price FROM products WHERE sku=?", (sku,))
    if row:
        return row[0]
    return None

def get_product_cost_price(sku):
    row = db_fetchone("SELECT cost_price FROM products WHERE sku=?", (sku,))
    if row:
        return row[0]
    return 0.0

def get_product_name(sku):
    row = db_fetchone("SELECT name FROM products WHERE sku=?", (sku,))
    if row:
        return row[0]
    return sku

def get_product_details(sku):
    # Returns (name, brand, category, cost_price, selling_price) or None
    row = db_fetchone(
        "SELECT name, brand, category, cost_price, selling_price FROM products WHERE sku=?",
        (sku,)
    )
    return row

def get_all_vendors():
    rows = db_fetchall(
        "SELECT DISTINCT vendor FROM purchases WHERE vendor IS NOT NULL AND vendor != '' ORDER BY vendor"
    )
    return [r[0] for r in rows]

def get_all_brands():
    rows = db_fetchall(
        "SELECT DISTINCT brand FROM products WHERE brand IS NOT NULL AND brand != '' ORDER BY brand"
    )
    return [r[0] for r in rows]

def get_all_categories():
    rows = db_fetchall(
        "SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category"
    )
    return [r[0] for r in rows]

def get_all_staff_names():
    rows = db_fetchall("SELECT name FROM staff ORDER BY name")
    return [r[0] for r in rows]

def get_payment_modes():
    defaults = ['Cash', 'UPI', 'Card', 'Net Banking', 'EMI']
    rows = db_fetchall(
        "SELECT DISTINCT payment_mode FROM sales WHERE payment_mode IS NOT NULL AND payment_mode != ''"
    )
    existing = [r[0] for r in rows]
    for mode in existing:
        if mode not in defaults:
            defaults.append(mode)
    return defaults

def get_all_roles():
    defaults = ['Sales Executive', 'Technician', 'Cashier', 'Manager', 'Storekeeper']
    rows = db_fetchall(
        "SELECT DISTINCT role FROM staff WHERE role IS NOT NULL AND role != ''"
    )
    existing = [r[0] for r in rows]
    for role in existing:
        if role not in defaults:
            defaults.append(role)
    return defaults

def get_expense_categories():
    defaults = ['Rent', 'Electricity', 'Internet', 'Salary', 'Maintenance', 'Marketing', 'Miscellaneous']
    rows = db_fetchall(
        "SELECT DISTINCT category FROM expenses WHERE category IS NOT NULL AND category != ''"
    )
    existing = [r[0] for r in rows]
    for cat in existing:
        if cat not in defaults:
            defaults.append(cat)
    return defaults


# ─────────────────────────────────────────────
# Inventory update helpers
# ─────────────────────────────────────────────

def ensure_inventory_row(sku, name=''):
    # Creates an inventory row for this SKU if it doesn't exist yet
    existing = db_fetchone("SELECT id FROM inventory WHERE sku=?", (sku,))
    if not existing:
        db_execute(
            "INSERT INTO inventory (sku, name, opening_stock, stock_in, stock_out, closing_stock, reorder_level) "
            "VALUES (?, ?, 0, 0, 0, 0, 5)",
            (sku, name)
        )

def check_stock_available(sku, qty_needed):
    row = db_fetchone("SELECT closing_stock, name FROM inventory WHERE sku=?", (sku,))
    if row is None:
        raise ValueError(f'No inventory record found for SKU "{sku}". Please add it in Inventory first.')
    available = row[0]
    product_name = row[1]
    if available < qty_needed:
        raise ValueError(
            f'Not enough stock for "{product_name}" (SKU: {sku}).\n'
            f'Available: {available}  |  Needed: {qty_needed}'
        )

def deduct_stock_for_sale(sku, qty):
    ensure_inventory_row(sku)
    check_stock_available(sku, qty)
    db_execute(
        "UPDATE inventory SET stock_out = stock_out + ?, closing_stock = closing_stock - ? WHERE sku=?",
        (qty, qty, sku)
    )

def restore_stock_after_delete(sku, qty):
    ensure_inventory_row(sku)
    db_execute(
        "UPDATE inventory SET stock_out = MAX(0, stock_out - ?), closing_stock = closing_stock + ? WHERE sku=?",
        (qty, qty, sku)
    )

def add_stock_from_purchase(sku, name, qty):
    ensure_inventory_row(sku, name)
    db_execute(
        "UPDATE inventory SET stock_in = stock_in + ?, closing_stock = closing_stock + ?, name=? WHERE sku=?",
        (qty, qty, name, sku)
    )

def remove_stock_from_purchase(sku, qty):
    db_execute(
        "UPDATE inventory SET stock_in = MAX(0, stock_in - ?), closing_stock = closing_stock - ? WHERE sku=?",
        (qty, qty, sku)
    )


# ─────────────────────────────────────────────
# Date helpers
# ─────────────────────────────────────────────

def get_today():
    return datetime.now().strftime('%Y-%m-%d')

def get_now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def is_valid_date(text):
    try:
        datetime.strptime(text.strip(), '%Y-%m-%d')
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────────
# Backup and Export
# ─────────────────────────────────────────────

def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, 'techmart_backup_' + timestamp + '.db')
    shutil.copyfile(DB_PATH, dest)
    return dest

def export_to_csv():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    tables = ['products', 'inventory', 'sales', 'purchases', 'expenses', 'staff']
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    for table in tables:
        cur.execute("SELECT * FROM " + table)
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
        filepath = os.path.join(EXPORT_DIR, table + '.csv')
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    conn.close()
    return EXPORT_DIR


# ─────────────────────────────────────────────
# Report data
# ─────────────────────────────────────────────

def get_report_data(date_from=None, date_to=None):
    if date_from and date_to:
        sales_row = db_fetchone(
            "SELECT COUNT(*), SUM(total_amount), SUM(cogs) FROM sales "
            "WHERE date(timestamp) BETWEEN ? AND ?",
            (date_from, date_to)
        )
        exp_row = db_fetchone(
            "SELECT SUM(amount) FROM expenses WHERE date(date) BETWEEN ? AND ?",
            (date_from, date_to)
        )
        pur_row = db_fetchone(
            "SELECT SUM(total) FROM purchases WHERE date(date) BETWEEN ? AND ?",
            (date_from, date_to)
        )
        best_row = db_fetchone(
            "SELECT product_name, SUM(quantity) AS q FROM sales "
            "WHERE date(timestamp) BETWEEN ? AND ? "
            "GROUP BY product_name ORDER BY q DESC LIMIT 1",
            (date_from, date_to)
        )
    else:
        sales_row = db_fetchone("SELECT COUNT(*), SUM(total_amount), SUM(cogs) FROM sales")
        exp_row   = db_fetchone("SELECT SUM(amount) FROM expenses")
        pur_row   = db_fetchone("SELECT SUM(total) FROM purchases")
        best_row  = db_fetchone(
            "SELECT product_name, SUM(quantity) AS q FROM sales "
            "GROUP BY product_name ORDER BY q DESC LIMIT 1"
        )

    total_orders = sales_row[0] or 0
    total_sales  = round(sales_row[1] or 0, 2)
    total_cogs   = round(sales_row[2] or 0, 2)
    total_exp    = round(exp_row[0] or 0, 2)
    total_pur    = round(pur_row[0] or 0, 2)
    gross_profit = round(total_sales - total_cogs, 2)
    net_profit   = round(total_sales - total_cogs - total_exp, 2)
    best_seller  = best_row[0] if best_row else 'N/A'

    return {
        'orders':    total_orders,
        'sales':     total_sales,
        'cogs':      total_cogs,
        'expenses':  total_exp,
        'purchases': total_pur,
        'gross':     gross_profit,
        'profit':    net_profit,
        'best':      best_seller,
    }


# ─────────────────────────────────────────────
# Combobox style (applied once at startup)
# ─────────────────────────────────────────────

def setup_combobox_style():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TM.TCombobox',
                    fieldbackground=ENTRY_BG,
                    background=ENTRY_BG,
                    foreground=TEXT,
                    selectbackground=ACCENT,
                    selectforeground=TEXT,
                    borderwidth=0,
                    relief='flat',
                    arrowcolor=TEXT_DIM)
    style.map('TM.TCombobox',
              fieldbackground=[('readonly', RO_BG)],
              foreground=[('readonly', TEXT_DIM)])


# ─────────────────────────────────────────────
# Reusable widget builders
# ─────────────────────────────────────────────

def make_label(parent, text, font=None, fg=None, bg=None):
    if font is None: font = FONT_LABEL
    if fg   is None: fg   = TEXT_DIM
    if bg   is None: bg   = BG_MID
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg)

def make_entry(parent, width=24):
    return tk.Entry(
        parent,
        bg=ENTRY_BG, fg=TEXT,
        font=FONT_ENTRY,
        relief='flat', bd=0,
        insertbackground=TEXT,
        width=width
    )

def make_readonly_entry(parent, width=24):
    # These are auto-filled fields the user cannot type into
    e = tk.Entry(
        parent,
        bg=RO_BG, fg=TEXT_DIM,
        font=FONT_ENTRY,
        relief='flat', bd=0,
        disabledbackground=RO_BG,
        disabledforeground=TEXT_DIM,
        width=width,
        state='disabled'
    )
    return e

def fill_readonly(entry_widget, value):
    # Helper to put a value into a disabled entry
    entry_widget.config(state='normal')
    entry_widget.delete(0, tk.END)
    if value is not None:
        entry_widget.insert(0, str(value))
    entry_widget.config(state='disabled')

def make_combobox(parent, values_list, width=22):
    cb = ttk.Combobox(
        parent,
        values=values_list,
        font=FONT_ENTRY,
        width=width,
        style='TM.TCombobox'
    )
    return cb

def make_button(parent, text, command, bg_color, width=16):
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg='white',
        font=FONT_BUTTON,
        relief='flat',
        bd=0,
        padx=10,
        pady=6,
        activebackground=BTN_HOVER,
        cursor='hand2',
        width=width
    )
    return btn

def make_listbox(parent, height=10):
    frame = tk.Frame(parent, bg=BG_MID)
    frame.pack(fill='x', padx=24, pady=4)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side='right', fill='y')
    lb = tk.Listbox(
        frame,
        bg=LIST_BG,
        fg=TEXT,
        font=FONT_MONO,
        relief='flat', bd=0,
        height=height,
        selectbackground=ACCENT,
        selectforeground='white',
        yscrollcommand=scrollbar.set,
        activestyle='none'
    )
    lb.pack(fill='x')
    scrollbar.config(command=lb.yview)
    return lb

def make_date_entry(parent):
    e = make_entry(parent, 14)
    e.insert(0, get_today())
    return e

def add_search_bar(parent, listbox_widget, get_data_func):
    # A search bar that filters the given listbox in real time
    bar = tk.Frame(parent, bg=BG_MID)
    bar.pack(fill='x', padx=24, pady=(4, 0))
    make_label(bar, 'Search:', bg=BG_MID).pack(side='left')
    search_var = tk.StringVar(master=parent)
    search_entry = tk.Entry(
        bar, textvariable=search_var,
        bg=ENTRY_BG, fg=TEXT,
        font=FONT_ENTRY, relief='flat', bd=0,
        insertbackground=TEXT, width=34
    )
    search_entry.pack(side='left', padx=(6, 0), ipady=3)

    def filter_list(*args):
        keyword = search_var.get().lower()
        listbox_widget.delete(0, tk.END)
        for row_text in get_data_func():
            if keyword in row_text.lower():
                listbox_widget.insert(tk.END, row_text)

    search_var.trace_add('write', filter_list)
    return search_var

def get_selected_id(listbox_widget, selected_index):
    # Parses the ID from a listbox row like "  #12  |  ..."
    row_text = listbox_widget.get(selected_index)
    id_part = row_text.strip().split('|')[0]
    id_part = id_part.replace('#', '').strip()
    return int(id_part)


# ─────────────────────────────────────────────
# Welcome / Splash screen
# ─────────────────────────────────────────────

class WelcomeScreen:
    def __init__(self, root, on_enter_callback):
        self.frame = tk.Frame(root, bg=BG_DARK)
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Top accent line
        tk.Frame(self.frame, bg=ACCENT, height=5).pack(fill='x')

        # Centre container
        center = tk.Frame(self.frame, bg=BG_DARK)
        center.place(relx=0.5, rely=0.5, anchor='center')

        # Logo badge
        badge = tk.Frame(center, bg=ACCENT, width=100, height=100)
        badge.pack_propagate(False)
        badge.pack(pady=(0, 20))
        tk.Label(badge, text='TM', font=('Georgia', 38, 'bold'), bg=ACCENT, fg='white').place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(center, text='TECHMART PRO', font=('Georgia', 46, 'bold'), bg=BG_DARK, fg=TEXT).pack()
        tk.Frame(center, bg=ACCENT, height=3).pack(fill='x', pady=8)
        tk.Label(center, text='Electronics Shop Management System', font=('Helvetica', 15, 'italic'), bg=BG_DARK, fg=ACCENT2).pack()
        tk.Label(center, text='', bg=BG_DARK).pack(pady=8)
        tk.Label(center, text='Sales  ·  Inventory  ·  Purchases  ·  Staff  ·  Reports',
                 font=('Helvetica', 12), bg=BG_DARK, fg=TEXT_DIM).pack()
        tk.Label(center, text='', bg=BG_DARK).pack(pady=14)

        # ── Login form ──────────────────────────
        login_frame = tk.Frame(center, bg=BG_DARK)
        login_frame.pack()

        # Username row
        user_row = tk.Frame(login_frame, bg=BG_DARK)
        user_row.pack(pady=(0, 8))
        tk.Label(user_row, text='Username', font=('Helvetica', 11),
                 bg=BG_DARK, fg=TEXT_DIM, width=10, anchor='e').pack(side='left', padx=(0, 10))
        username_entry = tk.Entry(user_row, bg=ENTRY_BG, fg=TEXT,
                                  font=('Helvetica', 11), relief='flat', bd=0,
                                  insertbackground=TEXT, width=22)
        username_entry.pack(side='left', ipady=6, padx=4)

        # Password row
        pass_row = tk.Frame(login_frame, bg=BG_DARK)
        pass_row.pack(pady=(0, 6))
        tk.Label(pass_row, text='Password', font=('Helvetica', 11),
                 bg=BG_DARK, fg=TEXT_DIM, width=10, anchor='e').pack(side='left', padx=(0, 10))
        password_entry = tk.Entry(pass_row, bg=ENTRY_BG, fg=TEXT,
                                  font=('Helvetica', 11), relief='flat', bd=0,
                                  insertbackground=TEXT, width=22, show='*')
        password_entry.pack(side='left', ipady=6, padx=4)

        # Error message label (hidden until a wrong login attempt)
        error_label = tk.Label(center, text='', font=('Helvetica', 10),
                               bg=BG_DARK, fg=DANGER)
        error_label.pack()

        # Login button
        def do_login():
            username = username_entry.get()
            password = password_entry.get()
            if username == 'tarak' and password == '12345':
                on_enter_callback()
            else:
                error_label.config(text='Invalid username or password. Please try again.')
                password_entry.delete(0, tk.END)

        # Allow pressing Enter key to login
        username_entry.bind('<Return>', lambda e: do_login())
        password_entry.bind('<Return>', lambda e: do_login())

        tk.Button(center, text='   LOGIN   ',
                  command=do_login,
                  bg=ACCENT, fg='white',
                  font=('Helvetica', 13, 'bold'),
                  relief='flat', padx=30, pady=12,
                  activebackground=BTN_HOVER,
                  cursor='hand2').pack(pady=(10, 0))

        year = datetime.now().year
        tk.Label(center, text=f'(c) {year}  TechMart Pro  |  All rights reserved',
                 font=FONT_SMALL, bg=BG_DARK, fg='#30363d').pack(pady=28)

        # Bottom accent line
        tk.Frame(self.frame, bg=ACCENT2, height=5).pack(side='bottom', fill='x')

        # Focus username field on load
        username_entry.focus()

    def destroy(self):
        self.frame.destroy()


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────

class TechMartApp:

    def __init__(self, root):
        self.root = root
        self.main_frame = None
        self.root.title('TechMart Pro — Electronics Shop Management')
        self.root.geometry('1360x800')
        self.root.configure(bg=BG_DARK)

        self.splash = WelcomeScreen(root, self.enter_dashboard)

    def enter_dashboard(self):
        self.splash.destroy()
        self.build_sidebar()
        self.show_dashboard()

    # ── Sidebar ──────────────────────────────

    def build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=SIDEBAR, width=220)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        # Header strip
        header = tk.Frame(sidebar, bg=ACCENT, height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text='TECHMART PRO', font=('Georgia', 12, 'bold'), bg=ACCENT, fg='white').place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(sidebar, text='NAVIGATION', font=('Helvetica', 8, 'bold'), bg=SIDEBAR, fg=MUTED).pack(pady=(18, 4))

        nav_items = [
            ('Dashboard',       self.show_dashboard),
            ('Point of Sale',   self.show_sales),
            ('Products',        self.show_products),
            ('Inventory',       self.show_inventory),
            ('Purchases',       self.show_purchases),
            ('Expenses',        self.show_expenses),
            ('Staff',           self.show_staff),
            ('Reports',         self.show_reports),
            ('Analytics',       self.show_analytics),
            ('Backup / Export', self.show_backup_export),
        ]

        for label, command in nav_items:
            btn = tk.Button(
                sidebar, text=label, command=command,
                bg=SIDEBAR, fg=TEXT,
                font=('Helvetica', 11),
                relief='flat', anchor='w',
                padx=18, pady=8, bd=0,
                activebackground=ACCENT,
                activeforeground='white',
                cursor='hand2'
            )
            btn.pack(fill='x')
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#1c2128'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=SIDEBAR))

        tk.Label(sidebar, text='v3.0  |  TechMart Pro', font=FONT_SMALL, bg=SIDEBAR, fg=MUTED).pack(side='bottom', pady=10)

    # ── Layout helpers ────────────────────────

    def get_content_frame(self):
        # Destroys the old content area and returns a fresh one
        if self.main_frame and self.main_frame.winfo_exists():
            self.main_frame.destroy()
        self.main_frame = tk.Frame(self.root, bg=BG_MID)
        self.main_frame.pack(side='right', expand=True, fill='both')
        return self.main_frame

    def add_page_header(self, parent, title):
        header = tk.Frame(parent, bg=BG_CARD, height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Frame(header, bg=ACCENT, width=5).pack(side='left', fill='y')
        tk.Label(header, text=title, font=FONT_TITLE, bg=BG_CARD, fg=TEXT).pack(side='left', padx=20, pady=10)

    def add_date_filter_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_MID)
        bar.pack(fill='x', padx=24, pady=(4, 0))
        make_label(bar, 'From:', bg=BG_MID).pack(side='left')
        from_entry = make_date_entry(bar)
        from_entry.pack(side='left', padx=(4, 16))
        make_label(bar, 'To:', bg=BG_MID).pack(side='left')
        to_entry = make_date_entry(bar)
        to_entry.pack(side='left', padx=(4, 0))
        return from_entry, to_entry

    def add_summary_label(self, parent):
        lbl = tk.Label(parent, text='', font=('Helvetica', 12, 'bold'), bg=BG_MID, fg=ACCENT2)
        lbl.pack(anchor='w', padx=24, pady=2)
        return lbl

    def add_action_buttons(self, parent, button_specs):
        # button_specs is a list of (label, command, color)
        row = tk.Frame(parent, bg=BG_MID)
        row.pack(pady=6, padx=24, anchor='w')
        for label, command, color in button_specs:
            make_button(row, label, command, color).pack(side='left', padx=5)

    def add_form_label(self, parent, text, row, col):
        tk.Label(parent, text=text, font=FONT_LABEL, bg=BG_MID, fg=TEXT_DIM).grid(
            row=row, column=col, padx=(0, 20), pady=(8, 2), sticky='w'
        )

    def add_form_separator(self, parent, row, col, colspan=1):
        tk.Frame(parent, bg=ACCENT, height=1).grid(
            row=row, column=col, columnspan=colspan,
            sticky='we', padx=(0, 20), pady=(0, 6)
        )

    # ── Dashboard ────────────────────────────

    def show_dashboard(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Dashboard')

        # Fetch summary numbers
        sales_data = db_fetchone("SELECT SUM(total_amount), SUM(cogs), COUNT(*) FROM sales")
        exp_data   = db_fetchone("SELECT SUM(amount) FROM expenses")

        total_sales  = round(sales_data[0] or 0, 2)
        total_cogs   = round(sales_data[1] or 0, 2)
        total_orders = sales_data[2] or 0
        total_exp    = round(exp_data[0] or 0, 2)
        net_profit   = round(total_sales - total_cogs - total_exp, 2)

        # KPI cards
        cards_frame = tk.Frame(page, bg=BG_MID)
        cards_frame.pack(pady=22, padx=24)

        card_data = [
            ('Revenue',      'Rs.' + str(total_sales),  ACCENT),
            ('Expenses',     'Rs.' + str(total_exp),     WARN),
            ('Net Profit',   'Rs.' + str(net_profit),    SUCCESS),
            ('Transactions', str(total_orders),           ACCENT2),
        ]

        for title, value, color in card_data:
            card = tk.Frame(page, bg=BG_CARD, width=220, height=120)
            card.pack_propagate(False)
            card.pack(side='left', padx=10, in_=cards_frame)
            tk.Frame(card, bg=color, height=4).pack(fill='x')
            tk.Label(card, text=title, font=('Helvetica', 11), bg=BG_CARD, fg=TEXT_DIM).pack(pady=(14, 2))
            tk.Label(card, text=value, font=('Georgia', 18, 'bold'), bg=BG_CARD, fg=color).pack()

        # Low stock alerts
        low_stock = db_fetchall(
            "SELECT name, sku, closing_stock, reorder_level FROM inventory "
            "WHERE closing_stock <= reorder_level ORDER BY closing_stock"
        )
        if low_stock:
            make_label(page, '⚠  Low Stock Alerts', font=FONT_HEADING, fg=WARN).pack(anchor='w', padx=24, pady=(12, 4))
            alert_lb = make_listbox(page, min(len(low_stock), 4))
            for item in low_stock:
                alert_lb.insert(tk.END, f'  {item[0]}  (SKU: {item[1]})  |  Stock: {item[2]}  |  Reorder at: {item[3]}')

        # Recent transactions
        make_label(page, 'Recent Transactions', font=FONT_HEADING, fg=ACCENT2).pack(anchor='w', padx=24, pady=(12, 4))
        recent_lb = make_listbox(page, 8)
        recent_rows = db_fetchall("SELECT * FROM sales ORDER BY id DESC LIMIT 20")
        for r in recent_rows:
            recent_lb.insert(tk.END,
                f'  #{r[0]}  SKU:{r[1]}  {r[2]}  Qty:{r[3]}  '
                f'Price:Rs.{r[4]}  Disc:Rs.{r[5]}  Total:Rs.{r[7]}  {r[9]}'
            )

    # ── Analytics ────────────────────────────

    def show_analytics(self):
        sales_rows = db_fetchall("SELECT product_name, SUM(quantity) FROM sales GROUP BY product_name")
        if not sales_rows:
            messagebox.showinfo('Analytics', 'No sales data available yet.')
            return

        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        fig.patch.set_facecolor('#0d1117')

        # Units sold chart
        names = [r[0][:20] for r in sales_rows]
        qtys  = [r[1] for r in sales_rows]
        bars  = ax1.bar(names, qtys, color=ACCENT, edgecolor='none')
        ax1.set_title('Units Sold by Product', color=TEXT, fontsize=13)
        ax1.set_facecolor('#161b22')
        ax1.set_xlabel('Product', color=TEXT_DIM)
        ax1.set_ylabel('Units Sold', color=TEXT_DIM)
        ax1.tick_params(colors=TEXT_DIM, rotation=30)
        for bar, q in zip(bars, qtys):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                     str(q), ha='center', va='bottom', color=TEXT, fontsize=9)

        # Revenue chart
        rev_rows = db_fetchall("SELECT product_name, SUM(total_amount) FROM sales GROUP BY product_name")
        rev_names = [r[0][:20] for r in rev_rows]
        revenues  = [r[1] for r in rev_rows]
        ax2.bar(rev_names, revenues, color=SUCCESS, edgecolor='none')
        ax2.set_title('Revenue by Product (Rs.)', color=TEXT, fontsize=13)
        ax2.set_facecolor('#161b22')
        ax2.set_xlabel('Product', color=TEXT_DIM)
        ax2.set_ylabel('Revenue (Rs.)', color=TEXT_DIM)
        ax2.tick_params(colors=TEXT_DIM, rotation=30)

        plt.suptitle('TechMart Pro — Sales Analytics', color=TEXT, fontsize=15, y=1.02)
        plt.tight_layout()
        plt.show()

    # ── Point of Sale ─────────────────────────

    def show_sales(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Point of Sale')

        form = tk.Frame(page, bg=BG_MID)
        form.pack(pady=10, padx=24, anchor='w')

        # Row 1 labels
        for col, text in enumerate(['Product  (SKU — Name)', 'Quantity', 'Unit Price  (Auto)', 'Discount (Rs.)']):
            self.add_form_label(form, text, 0, col)
        self.add_form_separator(form, 2, 0, 4)

        # Row 2 labels
        for col, text in enumerate(['Payment Mode', 'Staff / Cashier', 'Total Amount']):
            self.add_form_label(form, text, 3, col)
        self.add_form_separator(form, 5, 0, 3)

        # Row 1 widgets
        sku_var = tk.StringVar(master=self.root)
        sku_cb  = make_combobox(form, get_all_sku_options(), width=30)
        sku_cb.config(textvariable=sku_var)
        sku_cb.grid(row=1, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        qty_entry   = make_entry(form, 12)
        qty_entry.grid(row=1, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        price_entry = make_readonly_entry(form, 14)
        price_entry.grid(row=1, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        disc_entry  = make_entry(form, 12)
        disc_entry.grid(row=1, column=3, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        # Row 2 widgets
        pay_cb   = make_combobox(form, get_payment_modes(), width=22)
        pay_cb.grid(row=4, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        staff_cb = make_combobox(form, get_all_staff_names(), width=20)
        staff_cb.grid(row=4, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        total_var = tk.StringVar(master=self.root, value='Rs. 0.00')
        tk.Label(form, textvariable=total_var, font=('Georgia', 15, 'bold'), bg=BG_MID, fg=SUCCESS).grid(
            row=4, column=2, padx=(0, 20), sticky='w'
        )

        # Live total recalculation
        def recalculate_total(*args):
            try:
                price = float(price_entry.get() or 0)
                qty   = float(qty_entry.get() or 0)
                disc  = float(disc_entry.get() or 0)
                total_var.set('Rs. ' + str(round(price * qty - disc, 2)))
            except ValueError:
                total_var.set('Rs. --')

        def on_sku_selected(*args):
            sku = extract_sku(sku_var.get())
            price = get_product_selling_price(sku)
            fill_readonly(price_entry, price)
            recalculate_total()
            pay_cb['values']   = get_payment_modes()
            staff_cb['values'] = get_all_staff_names()

        sku_cb.bind('<<ComboboxSelected>>', on_sku_selected)
        sku_var.trace_add('write', on_sku_selected)
        qty_entry.bind('<KeyRelease>',  recalculate_total)
        disc_entry.bind('<KeyRelease>', recalculate_total)

        # Date filter + listbox
        from_entry, to_entry = self.add_date_filter_bar(page)
        sales_lb = make_listbox(page, 9)
        selected_id = [None]
        all_rows_cache = [None]

        add_search_bar(page, sales_lb, lambda: all_rows_cache[0] or [])

        def load_sales_list():
            sku_cb['values']   = get_all_sku_options()
            pay_cb['values']   = get_payment_modes()
            staff_cb['values'] = get_all_staff_names()

            d0 = from_entry.get().strip()
            d1 = to_entry.get().strip()

            if d0 and not is_valid_date(d0):
                messagebox.showerror('Error', f'Invalid From date: {d0}')
                return
            if d1 and not is_valid_date(d1):
                messagebox.showerror('Error', f'Invalid To date: {d1}')
                return

            if d0 and d1:
                rows = db_fetchall(
                    "SELECT * FROM sales WHERE date(timestamp) BETWEEN ? AND ? ORDER BY id DESC",
                    (d0, d1)
                )
            else:
                rows = db_fetchall("SELECT * FROM sales ORDER BY id DESC")

            formatted = []
            for r in rows:
                line = (f'  #{r[0]}  |  SKU:{r[1]}  |  {r[2]}  |  Qty:{r[3]}  |  '
                        f'Price:Rs.{r[4]}  |  Disc:Rs.{r[5]}  |  Total:Rs.{r[7]}  |  '
                        f'{r[8]}  |  {r[9]}  |  {r[10]}')
                formatted.append(line)

            all_rows_cache[0] = formatted
            sales_lb.delete(0, tk.END)
            for line in formatted:
                sales_lb.insert(tk.END, line)

        def on_sale_selected(event):
            selection = sales_lb.curselection()
            if not selection:
                return
            selected_id[0] = get_selected_id(sales_lb, selection[0])
            row = db_fetchone("SELECT * FROM sales WHERE id=?", (selected_id[0],))
            if row:
                sku_var.set(row[1] + "  —  " + row[2])
                fill_readonly(price_entry, row[4])
                qty_entry.delete(0, tk.END);  qty_entry.insert(0, str(row[3]))
                disc_entry.delete(0, tk.END); disc_entry.insert(0, str(row[5]))
                pay_cb.set(row[8] or '')
                staff_cb.set(row[9] or '')
                recalculate_total()

        sales_lb.bind('<<ListboxSelect>>', on_sale_selected)

        def clear_sale_form():
            sku_var.set('')
            fill_readonly(price_entry, None)
            qty_entry.delete(0, tk.END)
            disc_entry.delete(0, tk.END)
            pay_cb.set('')
            staff_cb.set('')
            total_var.set('Rs. 0.00')
            selected_id[0] = None

        def add_sale():
            sku = extract_sku(sku_var.get())
            if not sku:
                messagebox.showerror('Error', 'Please select a product.')
                return
            try:
                qty  = int(qty_entry.get())
                disc = float(disc_entry.get() or 0)
                if qty <= 0:
                    messagebox.showerror('Error', 'Quantity must be greater than 0.')
                    return
                if disc < 0:
                    messagebox.showerror('Error', 'Discount cannot be negative.')
                    return
                price = get_product_selling_price(sku)
                if price is None:
                    messagebox.showerror('Error', f'Product with SKU "{sku}" not found.')
                    return
                if disc > price * qty:
                    messagebox.showerror('Error', 'Discount cannot exceed the total sale amount.')
                    return
                cogs  = round(get_product_cost_price(sku) * qty, 2)
                total = round(price * qty - disc, 2)
                name  = get_product_name(sku)

                # Deduct from inventory
                deduct_stock_for_sale(sku, qty)

                db_execute(
                    "INSERT INTO sales (sku, product_name, quantity, unit_price, discount, cogs, total_amount, payment_mode, staff, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (sku, name, qty, price, disc, cogs, total, pay_cb.get(), staff_cb.get(), get_now())
                )
                clear_sale_form()
                load_sales_list()
            except ValueError as e:
                messagebox.showerror('Error', str(e))

        def edit_sale():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a sale record first.')
                return
            sku = extract_sku(sku_var.get())
            if not sku:
                messagebox.showerror('Error', 'Please select a product.')
                return
            try:
                qty  = int(qty_entry.get())
                disc = float(disc_entry.get() or 0)
                if qty <= 0:
                    messagebox.showerror('Error', 'Quantity must be greater than 0.')
                    return
                if disc < 0:
                    messagebox.showerror('Error', 'Discount cannot be negative.')
                    return

                # Restore old stock first
                old = db_fetchone("SELECT sku, quantity FROM sales WHERE id=?", (selected_id[0],))
                if old:
                    restore_stock_after_delete(old[0], old[1])

                price = get_product_selling_price(sku)
                if price is None:
                    # Fallback to the stored price if product was deleted
                    stored = db_fetchone("SELECT unit_price FROM sales WHERE id=?", (selected_id[0],))
                    price  = stored[0] if stored else 0

                if disc > price * qty:
                    messagebox.showerror('Error', 'Discount cannot exceed the total sale amount.')
                    return

                cogs  = round(get_product_cost_price(sku) * qty, 2)
                total = round(price * qty - disc, 2)
                name  = get_product_name(sku)

                deduct_stock_for_sale(sku, qty)

                db_execute(
                    "UPDATE sales SET sku=?, product_name=?, quantity=?, unit_price=?, "
                    "discount=?, cogs=?, total_amount=?, payment_mode=?, staff=? WHERE id=?",
                    (sku, name, qty, price, disc, cogs, total, pay_cb.get(), staff_cb.get(), selected_id[0])
                )
                clear_sale_form()
                load_sales_list()
            except ValueError as e:
                messagebox.showerror('Error', str(e))

        def delete_sale():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a sale record first.')
                return
            confirm = messagebox.askyesno('Confirm Delete', 'Permanently delete this transaction?')
            if confirm:
                try:
                    old = db_fetchone("SELECT sku, quantity FROM sales WHERE id=?", (selected_id[0],))
                    if old:
                        restore_stock_after_delete(old[0], old[1])
                    db_execute("DELETE FROM sales WHERE id=?", (selected_id[0],))
                    clear_sale_form()
                    load_sales_list()
                except ValueError as e:
                    messagebox.showerror('Error', str(e))

        self.add_action_buttons(page, [
            ('Record Sale', add_sale,    ACCENT),
            ('Edit',        edit_sale,   BLUE),
            ('Delete',      delete_sale, DANGER),
            ('Refresh',     load_sales_list, MUTED),
        ])
        load_sales_list()

    # ── Products ─────────────────────────────

    def show_products(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Product Catalogue')

        form = tk.Frame(page, bg=BG_MID)
        form.pack(pady=10, padx=24, anchor='w')

        # Row 1 — SKU, Name, Brand, Category
        for col, text in enumerate(['SKU', 'Product Name', 'Brand', 'Category']):
            self.add_form_label(form, text, 0, col)
        self.add_form_separator(form, 2, 0, 4)

        sku_entry  = make_entry(form, 16)
        sku_entry.grid(row=1, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        name_entry = make_entry(form, 24)
        name_entry.grid(row=1, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        brand_cb = make_combobox(form, get_all_brands(), width=18)
        brand_cb.grid(row=1, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        cat_cb = make_combobox(form, get_all_categories(), width=18)
        cat_cb.grid(row=1, column=3, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        # Row 2 — Cost, Selling Price, Margin
        for col, text in enumerate(['Cost Price (Rs.)', 'Selling Price (Rs.)', 'Margin %  (Auto)']):
            self.add_form_label(form, text, 3, col)
        self.add_form_separator(form, 5, 0, 3)

        cost_entry = make_entry(form, 14)
        cost_entry.grid(row=4, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        sell_entry = make_entry(form, 14)
        sell_entry.grid(row=4, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        margin_entry = make_readonly_entry(form, 12)
        margin_entry.grid(row=4, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        def update_margin(*args):
            try:
                cost = float(cost_entry.get() or 0)
                sell = float(sell_entry.get() or 0)
                if sell > 0:
                    margin = round((sell - cost) / sell * 100, 2)
                    fill_readonly(margin_entry, str(margin) + '%')
                else:
                    fill_readonly(margin_entry, '—')
            except ValueError:
                fill_readonly(margin_entry, '—')

        cost_entry.bind('<KeyRelease>', update_margin)
        sell_entry.bind('<KeyRelease>', update_margin)

        products_lb = make_listbox(page, 10)
        selected_id = [None]
        all_rows_cache = [None]

        add_search_bar(page, products_lb, lambda: all_rows_cache[0] or [])

        def load_products_list():
            brand_cb['values'] = get_all_brands()
            cat_cb['values']   = get_all_categories()
            rows = db_fetchall("SELECT * FROM products ORDER BY name")
            formatted = []
            for r in rows:
                line = (f'  #{r[0]}  |  SKU:{r[1]}  |  {r[2]}  |  '
                        f'Brand:{r[3]}  |  Cat:{r[4]}  |  '
                        f'Cost:Rs.{r[5]}  |  Sell:Rs.{r[6]}  |  Margin:{r[7]}%')
                formatted.append(line)
            all_rows_cache[0] = formatted
            products_lb.delete(0, tk.END)
            for line in formatted:
                products_lb.insert(tk.END, line)

        def on_product_selected(event):
            selection = products_lb.curselection()
            if not selection:
                return
            selected_id[0] = get_selected_id(products_lb, selection[0])
            row = db_fetchone("SELECT * FROM products WHERE id=?", (selected_id[0],))
            if row:
                sku_entry.delete(0, tk.END);  sku_entry.insert(0, row[1])
                name_entry.delete(0, tk.END); name_entry.insert(0, row[2])
                brand_cb.set(row[3] or '')
                cat_cb.set(row[4] or '')
                cost_entry.delete(0, tk.END); cost_entry.insert(0, str(row[5]))
                sell_entry.delete(0, tk.END); sell_entry.insert(0, str(row[6]))
                fill_readonly(margin_entry, str(row[7]) + '%')

        products_lb.bind('<<ListboxSelect>>', on_product_selected)

        def clear_product_form():
            sku_entry.delete(0, tk.END)
            name_entry.delete(0, tk.END)
            brand_cb.set('')
            cat_cb.set('')
            cost_entry.delete(0, tk.END)
            sell_entry.delete(0, tk.END)
            fill_readonly(margin_entry, '')
            selected_id[0] = None

        def add_product():
            sku  = sku_entry.get().strip()
            name = name_entry.get().strip()
            if not sku:
                messagebox.showerror('Error', 'SKU cannot be blank.')
                return
            if not name:
                messagebox.showerror('Error', 'Product Name cannot be blank.')
                return
            # Check duplicate SKU
            existing = db_fetchone("SELECT id FROM products WHERE sku=?", (sku,))
            if existing:
                messagebox.showwarning('Duplicate SKU', f'A product with SKU "{sku}" already exists.')
                return
            try:
                cost = float(cost_entry.get())
                sell = float(sell_entry.get())
                if sell <= 0:
                    messagebox.showerror('Error', 'Selling Price must be greater than 0.')
                    return
                if cost < 0:
                    messagebox.showerror('Error', 'Cost Price cannot be negative.')
                    return
                margin = round((sell - cost) / sell * 100, 2) if sell > 0 else 0
                db_execute(
                    "INSERT INTO products (sku, name, brand, category, cost_price, selling_price, margin) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (sku, name, brand_cb.get(), cat_cb.get(), cost, sell, margin)
                )
                clear_product_form()
                load_products_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for Cost and Selling Price.')

        def edit_product():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a product first.')
                return
            sku  = sku_entry.get().strip()
            name = name_entry.get().strip()
            if not sku:
                messagebox.showerror('Error', 'SKU cannot be blank.')
                return
            if not name:
                messagebox.showerror('Error', 'Product Name cannot be blank.')
                return
            try:
                cost = float(cost_entry.get())
                sell = float(sell_entry.get())
                if sell <= 0:
                    messagebox.showerror('Error', 'Selling Price must be greater than 0.')
                    return
                margin = round((sell - cost) / sell * 100, 2) if sell > 0 else 0
                db_execute(
                    "UPDATE products SET sku=?, name=?, brand=?, category=?, cost_price=?, selling_price=?, margin=? WHERE id=?",
                    (sku, name, brand_cb.get(), cat_cb.get(), cost, sell, margin, selected_id[0])
                )
                clear_product_form()
                load_products_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for Cost and Selling Price.')

        def delete_product():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a product first.')
                return
            row = db_fetchone("SELECT sku, name FROM products WHERE id=?", (selected_id[0],))
            if not row:
                return
            sku, name = row
            has_sales = db_fetchone("SELECT id FROM sales WHERE sku=? LIMIT 1", (sku,))
            if has_sales:
                msg = f'"{name}" has existing sales records. The product will be deleted but sales history will remain.\n\nDelete anyway?'
            else:
                msg = f'Delete "{name}" (SKU: {sku})?'
            if messagebox.askyesno('Confirm Delete', msg):
                db_execute("DELETE FROM products WHERE id=?", (selected_id[0],))
                clear_product_form()
                load_products_list()

        self.add_action_buttons(page, [
            ('Add Product',  add_product,    ACCENT),
            ('Edit Product', edit_product,   BLUE),
            ('Delete',       delete_product, DANGER),
            ('Refresh',      load_products_list, MUTED),
        ])
        load_products_list()

    # ── Inventory ────────────────────────────

    def show_inventory(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Inventory')

        form = tk.Frame(page, bg=BG_MID)
        form.pack(pady=10, padx=24, anchor='w')

        for col, text in enumerate(['SKU  (select to auto-fill)', 'Product Name  (Auto)', 'Opening Stock', 'Reorder Level']):
            self.add_form_label(form, text, 0, col)
        self.add_form_separator(form, 2, 0, 4)

        sku_var = tk.StringVar(master=self.root)
        sku_cb  = make_combobox(form, get_all_sku_options(), width=28)
        sku_cb.config(textvariable=sku_var)
        sku_cb.grid(row=1, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        name_entry    = make_readonly_entry(form, 24)
        name_entry.grid(row=1, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        opening_entry = make_entry(form, 12)
        opening_entry.grid(row=1, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        reorder_entry = make_entry(form, 12)
        reorder_entry.grid(row=1, column=3, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        def on_sku_selected(*args):
            sku  = extract_sku(sku_var.get())
            info = get_product_details(sku)
            fill_readonly(name_entry, info[0] if info else '')
            # Pre-fill reorder level if inventory record already exists
            inv_row = db_fetchone("SELECT reorder_level FROM inventory WHERE sku=?", (sku,))
            if inv_row:
                reorder_entry.delete(0, tk.END)
                reorder_entry.insert(0, str(inv_row[0]))

        sku_cb.bind('<<ComboboxSelected>>', on_sku_selected)
        sku_var.trace_add('write', on_sku_selected)

        inv_lb = make_listbox(page, 12)
        selected_id = [None]
        all_rows_cache = [None]

        add_search_bar(page, inv_lb, lambda: all_rows_cache[0] or [])

        def load_inventory_list():
            sku_cb['values'] = get_all_sku_options()
            rows = db_fetchall("SELECT * FROM inventory ORDER BY name")
            formatted = []
            for r in rows:
                low_flag = '  [⚠ LOW]' if int(r[6] or 0) <= int(r[7] or 0) else ''
                line = (f'  #{r[0]}  |  SKU:{r[1]}  |  {r[2]}  |  '
                        f'Open:{r[3]}  |  In:{r[4]}  |  Out:{r[5]}  |  '
                        f'Closing:{r[6]}  |  Reorder:{r[7]}' + low_flag)
                formatted.append(line)
            all_rows_cache[0] = formatted
            inv_lb.delete(0, tk.END)
            for line in formatted:
                inv_lb.insert(tk.END, line)

        def on_inv_selected(event):
            selection = inv_lb.curselection()
            if not selection:
                return
            selected_id[0] = get_selected_id(inv_lb, selection[0])
            row = db_fetchone("SELECT * FROM inventory WHERE id=?", (selected_id[0],))
            if row:
                sku_var.set(row[1] + "  —  " + row[2])
                fill_readonly(name_entry, row[2])
                opening_entry.delete(0, tk.END); opening_entry.insert(0, str(row[3]))
                reorder_entry.delete(0, tk.END); reorder_entry.insert(0, str(row[7]))

        inv_lb.bind('<<ListboxSelect>>', on_inv_selected)

        def clear_inv_form():
            sku_var.set('')
            fill_readonly(name_entry, '')
            opening_entry.delete(0, tk.END)
            reorder_entry.delete(0, tk.END)
            selected_id[0] = None

        def add_inventory():
            sku = extract_sku(sku_var.get())
            if not sku:
                messagebox.showerror('Error', 'Please select a SKU.')
                return
            existing = db_fetchone("SELECT id FROM inventory WHERE sku=?", (sku,))
            if existing:
                messagebox.showwarning('Already Exists', f'An inventory record for SKU "{sku}" already exists.')
                return
            try:
                opening = int(opening_entry.get() or 0)
                reorder = int(reorder_entry.get() or 5)
                if opening < 0:
                    messagebox.showerror('Error', 'Opening Stock cannot be negative.')
                    return
                if reorder < 0:
                    messagebox.showerror('Error', 'Reorder Level cannot be negative.')
                    return
                name = get_product_name(sku)
                db_execute(
                    "INSERT INTO inventory (sku, name, opening_stock, stock_in, stock_out, closing_stock, reorder_level) "
                    "VALUES (?, ?, ?, 0, 0, ?, ?)",
                    (sku, name, opening, opening, reorder)
                )
                clear_inv_form()
                load_inventory_list()
            except ValueError:
                messagebox.showerror('Error', 'Opening Stock and Reorder Level must be whole numbers.')

        def edit_inventory():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select an inventory record first.')
                return
            sku = extract_sku(sku_var.get())
            if not sku:
                messagebox.showerror('Error', 'SKU cannot be blank.')
                return
            try:
                reorder = int(reorder_entry.get() or 5)
                if reorder < 0:
                    messagebox.showerror('Error', 'Reorder Level cannot be negative.')
                    return
                name = get_product_name(sku)
                db_execute(
                    "UPDATE inventory SET sku=?, name=?, reorder_level=? WHERE id=?",
                    (sku, name, reorder, selected_id[0])
                )
                clear_inv_form()
                load_inventory_list()
            except ValueError:
                messagebox.showerror('Error', 'Reorder Level must be a whole number.')

        def delete_inventory():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a record first.')
                return
            sku = extract_sku(sku_var.get())
            linked = db_fetchone("SELECT id FROM purchases WHERE sku=? LIMIT 1", (sku,))
            if linked:
                msg = 'This SKU has purchase history linked to it.\nDeleting will not remove that data.\n\nDelete anyway?'
            else:
                msg = 'Permanently delete this inventory record?'
            if messagebox.askyesno('Confirm Delete', msg):
                db_execute("DELETE FROM inventory WHERE id=?", (selected_id[0],))
                clear_inv_form()
                load_inventory_list()

        self.add_action_buttons(page, [
            ('Add',     add_inventory,    ACCENT),
            ('Edit',    edit_inventory,   BLUE),
            ('Delete',  delete_inventory, DANGER),
            ('Refresh', load_inventory_list, MUTED),
        ])
        load_inventory_list()

    # ── Purchases ────────────────────────────

    def show_purchases(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Purchase Orders')

        form = tk.Frame(page, bg=BG_MID)
        form.pack(pady=10, padx=24, anchor='w')

        # Row 1 — Vendor, SKU, Name (auto), Brand (auto), Category (auto)
        for col, text in enumerate(['Vendor / Supplier', 'SKU  (select to auto-fill)', 'Product Name  (Auto)', 'Brand  (Auto)', 'Category  (Auto)']):
            self.add_form_label(form, text, 0, col)
        self.add_form_separator(form, 2, 0, 5)

        # Row 2 — Qty, Unit Cost, Total (auto)
        for col, text in enumerate(['Quantity', 'Unit Cost (Rs.)', 'Total  (Auto)']):
            self.add_form_label(form, text, 3, col)
        self.add_form_separator(form, 5, 0, 3)

        vendor_cb = make_combobox(form, get_all_vendors(), width=20)
        vendor_cb.grid(row=1, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        sku_var = tk.StringVar(master=self.root)
        sku_cb  = make_combobox(form, get_all_sku_options(), width=26)
        sku_cb.config(textvariable=sku_var)
        sku_cb.grid(row=1, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        pname_entry = make_readonly_entry(form, 20)
        pname_entry.grid(row=1, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        brand_entry = make_readonly_entry(form, 14)
        brand_entry.grid(row=1, column=3, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        cat_entry = make_readonly_entry(form, 14)
        cat_entry.grid(row=1, column=4, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        qty_entry  = make_entry(form, 12)
        qty_entry.grid(row=4, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        cost_entry = make_entry(form, 14)
        cost_entry.grid(row=4, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        total_entry = make_readonly_entry(form, 14)
        total_entry.grid(row=4, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        def on_sku_selected(*args):
            sku  = extract_sku(sku_var.get())
            info = get_product_details(sku)
            if info:
                fill_readonly(pname_entry, info[0])
                fill_readonly(brand_entry, info[1])
                fill_readonly(cat_entry,   info[2])
                # Pre-fill last recorded cost for this SKU
                last_cost = db_fetchone(
                    "SELECT unit_cost FROM purchases WHERE sku=? ORDER BY id DESC LIMIT 1", (sku,)
                )
                if last_cost:
                    cost_entry.delete(0, tk.END)
                    cost_entry.insert(0, str(last_cost[0]))
            else:
                fill_readonly(pname_entry, '')
                fill_readonly(brand_entry, '')
                fill_readonly(cat_entry,   '')
            recalc_purchase_total()

        def recalc_purchase_total(*args):
            try:
                qty  = float(qty_entry.get() or 0)
                cost = float(cost_entry.get() or 0)
                fill_readonly(total_entry, round(qty * cost, 2))
            except ValueError:
                fill_readonly(total_entry, '')

        sku_cb.bind('<<ComboboxSelected>>', on_sku_selected)
        sku_var.trace_add('write', on_sku_selected)
        qty_entry.bind('<KeyRelease>',  recalc_purchase_total)
        cost_entry.bind('<KeyRelease>', recalc_purchase_total)

        from_entry, to_entry = self.add_date_filter_bar(page)
        purchases_lb = make_listbox(page, 9)
        sum_label    = self.add_summary_label(page)
        selected_id  = [None]
        all_rows_cache = [None]

        add_search_bar(page, purchases_lb, lambda: all_rows_cache[0] or [])

        def load_purchases_list():
            sku_cb['values']    = get_all_sku_options()
            vendor_cb['values'] = get_all_vendors()
            d0 = from_entry.get().strip()
            d1 = to_entry.get().strip()
            if d0 and not is_valid_date(d0):
                messagebox.showerror('Error', f'Invalid From date: {d0}')
                return
            if d1 and not is_valid_date(d1):
                messagebox.showerror('Error', f'Invalid To date: {d1}')
                return
            if d0 and d1:
                rows = db_fetchall(
                    "SELECT * FROM purchases WHERE date(date) BETWEEN ? AND ? ORDER BY id DESC",
                    (d0, d1)
                )
            else:
                rows = db_fetchall("SELECT * FROM purchases ORDER BY id DESC")

            formatted = []
            for r in rows:
                line = (f'  #{r[0]}  |  {r[1]}  |  SKU:{r[2]}  |  {r[3]}  |  '
                        f'Qty:{r[4]}  |  Cost:Rs.{r[5]}  |  Total:Rs.{r[6]}  |  {r[7]}')
                formatted.append(line)
            all_rows_cache[0] = formatted
            purchases_lb.delete(0, tk.END)
            for line in formatted:
                purchases_lb.insert(tk.END, line)

            total_spend = sum(r[6] for r in rows)
            sum_label.config(text='Total Purchase Value :  Rs.' + str(round(total_spend, 2)))

        def on_purchase_selected(event):
            selection = purchases_lb.curselection()
            if not selection:
                return
            selected_id[0] = get_selected_id(purchases_lb, selection[0])
            row = db_fetchone("SELECT * FROM purchases WHERE id=?", (selected_id[0],))
            if row:
                vendor_cb.set(row[1] or '')
                sku_var.set(row[2] + "  —  " + row[3])
                on_sku_selected()
                qty_entry.delete(0, tk.END);  qty_entry.insert(0, str(row[4]))
                cost_entry.delete(0, tk.END); cost_entry.insert(0, str(row[5]))
                recalc_purchase_total()

        purchases_lb.bind('<<ListboxSelect>>', on_purchase_selected)

        def clear_purchase_form():
            vendor_cb.set('')
            sku_var.set('')
            fill_readonly(pname_entry, '')
            fill_readonly(brand_entry, '')
            fill_readonly(cat_entry,   '')
            qty_entry.delete(0, tk.END)
            cost_entry.delete(0, tk.END)
            fill_readonly(total_entry, '')
            selected_id[0] = None

        def add_purchase():
            vendor = vendor_cb.get().strip()
            sku    = extract_sku(sku_var.get())
            if not vendor:
                messagebox.showerror('Error', 'Vendor cannot be blank.')
                return
            if not sku:
                messagebox.showerror('Error', 'Please select a product SKU.')
                return
            try:
                qty  = int(qty_entry.get())
                cost = float(cost_entry.get())
                if qty <= 0:
                    messagebox.showerror('Error', 'Quantity must be greater than 0.')
                    return
                if cost <= 0:
                    messagebox.showerror('Error', 'Unit Cost must be greater than 0.')
                    return
                name = pname_entry.get().strip() or get_product_name(sku)
                total = round(qty * cost, 2)
                db_execute(
                    "INSERT INTO purchases (vendor, sku, product_name, qty, unit_cost, total, date) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (vendor, sku, name, qty, cost, total, get_today())
                )
                add_stock_from_purchase(sku, name, qty)
                clear_purchase_form()
                load_purchases_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for Quantity and Cost.')

        def edit_purchase():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a purchase record first.')
                return
            vendor = vendor_cb.get().strip()
            sku    = extract_sku(sku_var.get())
            if not vendor:
                messagebox.showerror('Error', 'Vendor cannot be blank.')
                return
            if not sku:
                messagebox.showerror('Error', 'Please select a product SKU.')
                return
            try:
                qty  = int(qty_entry.get())
                cost = float(cost_entry.get())
                if qty <= 0:
                    messagebox.showerror('Error', 'Quantity must be greater than 0.')
                    return
                if cost <= 0:
                    messagebox.showerror('Error', 'Unit Cost must be greater than 0.')
                    return
                # Reverse the old stock change
                old = db_fetchone("SELECT sku, qty FROM purchases WHERE id=?", (selected_id[0],))
                if old:
                    remove_stock_from_purchase(old[0], old[1])
                name  = pname_entry.get().strip() or get_product_name(sku)
                total = round(qty * cost, 2)
                db_execute(
                    "UPDATE purchases SET vendor=?, sku=?, product_name=?, qty=?, unit_cost=?, total=? WHERE id=?",
                    (vendor, sku, name, qty, cost, total, selected_id[0])
                )
                add_stock_from_purchase(sku, name, qty)
                clear_purchase_form()
                load_purchases_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter valid numbers for Quantity and Cost.')

        def delete_purchase():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a purchase record first.')
                return
            confirm = messagebox.askyesno('Confirm Delete', 'Delete this purchase and reverse the stock update?')
            if confirm:
                old = db_fetchone("SELECT sku, qty FROM purchases WHERE id=?", (selected_id[0],))
                if old:
                    remove_stock_from_purchase(old[0], old[1])
                db_execute("DELETE FROM purchases WHERE id=?", (selected_id[0],))
                clear_purchase_form()
                load_purchases_list()

        self.add_action_buttons(page, [
            ('Record Purchase', add_purchase,    ACCENT),
            ('Edit',            edit_purchase,   BLUE),
            ('Delete',          delete_purchase, DANGER),
            ('Refresh',         load_purchases_list, MUTED),
        ])
        load_purchases_list()

    # ── Expenses ─────────────────────────────

    def show_expenses(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Expense Management')

        form = tk.Frame(page, bg=BG_MID)
        form.pack(pady=10, padx=24, anchor='w')

        for col, text in enumerate(['Category', 'Amount (Rs.)']):
            self.add_form_label(form, text, 0, col)
        self.add_form_separator(form, 2, 0, 2)

        cat_cb    = make_combobox(form, get_expense_categories(), width=26)
        cat_cb.grid(row=1, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        amt_entry = make_entry(form, 16)
        amt_entry.grid(row=1, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        from_entry, to_entry = self.add_date_filter_bar(page)
        expenses_lb = make_listbox(page, 12)
        sum_label   = self.add_summary_label(page)
        selected_id = [None]

        def load_expenses_list():
            cat_cb['values'] = get_expense_categories()
            d0 = from_entry.get().strip()
            d1 = to_entry.get().strip()
            if d0 and not is_valid_date(d0):
                messagebox.showerror('Error', f'Invalid From date: {d0}')
                return
            if d1 and not is_valid_date(d1):
                messagebox.showerror('Error', f'Invalid To date: {d1}')
                return
            if d0 and d1:
                rows = db_fetchall(
                    "SELECT * FROM expenses WHERE date(date) BETWEEN ? AND ? ORDER BY id DESC",
                    (d0, d1)
                )
            else:
                rows = db_fetchall("SELECT * FROM expenses ORDER BY id DESC")

            expenses_lb.delete(0, tk.END)
            for r in rows:
                expenses_lb.insert(tk.END, f'  #{r[0]}  |  {r[1]}  |  Rs.{r[2]}  |  {r[3]}')
            total = sum(r[2] for r in rows)
            sum_label.config(text='Total Expenses :  Rs.' + str(round(total, 2)))

        def on_expense_selected(event):
            selection = expenses_lb.curselection()
            if not selection:
                return
            selected_id[0] = get_selected_id(expenses_lb, selection[0])
            row = db_fetchone("SELECT * FROM expenses WHERE id=?", (selected_id[0],))
            if row:
                cat_cb.set(row[1])
                amt_entry.delete(0, tk.END)
                amt_entry.insert(0, str(row[2]))

        expenses_lb.bind('<<ListboxSelect>>', on_expense_selected)

        def clear_expense_form():
            cat_cb.set('')
            amt_entry.delete(0, tk.END)
            selected_id[0] = None

        def add_expense():
            cat = cat_cb.get().strip()
            if not cat:
                messagebox.showerror('Error', 'Category cannot be blank.')
                return
            try:
                amt = float(amt_entry.get())
                if amt <= 0:
                    messagebox.showerror('Error', 'Amount must be greater than 0.')
                    return
                db_execute(
                    "INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)",
                    (cat, amt, get_today())
                )
                clear_expense_form()
                load_expenses_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter a valid number for Amount.')

        def edit_expense():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a record first.')
                return
            cat = cat_cb.get().strip()
            if not cat:
                messagebox.showerror('Error', 'Category cannot be blank.')
                return
            try:
                amt = float(amt_entry.get())
                if amt <= 0:
                    messagebox.showerror('Error', 'Amount must be greater than 0.')
                    return
                db_execute(
                    "UPDATE expenses SET category=?, amount=? WHERE id=?",
                    (cat, amt, selected_id[0])
                )
                clear_expense_form()
                load_expenses_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter a valid number for Amount.')

        def delete_expense():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a record first.')
                return
            if messagebox.askyesno('Confirm Delete', 'Permanently delete this expense record?'):
                db_execute("DELETE FROM expenses WHERE id=?", (selected_id[0],))
                clear_expense_form()
                load_expenses_list()

        self.add_action_buttons(page, [
            ('Add',     add_expense,    ACCENT),
            ('Edit',    edit_expense,   BLUE),
            ('Delete',  delete_expense, DANGER),
            ('Refresh', load_expenses_list, MUTED),
        ])
        load_expenses_list()

    # ── Staff ────────────────────────────────

    def show_staff(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Staff Management')

        form = tk.Frame(page, bg=BG_MID)
        form.pack(pady=10, padx=24, anchor='w')

        for col, text in enumerate(['Name', 'Role / Designation', 'Salary (Rs.)']):
            self.add_form_label(form, text, 0, col)
        self.add_form_separator(form, 2, 0, 3)

        name_entry = make_entry(form, 22)
        name_entry.grid(row=1, column=0, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        role_cb = make_combobox(form, get_all_roles(), width=22)
        role_cb.grid(row=1, column=1, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        salary_entry = make_entry(form, 16)
        salary_entry.grid(row=1, column=2, padx=(0, 20), pady=(0, 2), sticky='w', ipady=4)

        staff_lb    = make_listbox(page, 12)
        sum_label   = self.add_summary_label(page)
        selected_id = [None]

        def load_staff_list():
            role_cb['values'] = get_all_roles()
            rows = db_fetchall("SELECT * FROM staff ORDER BY name")
            staff_lb.delete(0, tk.END)
            for r in rows:
                staff_lb.insert(tk.END,
                    f'  #{r[0]}  |  {r[1]}  |  Role:{r[2]}  |  '
                    f'Salary:Rs.{r[3]}  |  Attendance:{r[4]} days'
                )
            total_salary = sum(r[3] for r in rows)
            sum_label.config(text='Total Salary Liability :  Rs.' + str(round(total_salary, 2)))

        def on_staff_selected(event):
            selection = staff_lb.curselection()
            if not selection:
                return
            selected_id[0] = get_selected_id(staff_lb, selection[0])
            row = db_fetchone("SELECT * FROM staff WHERE id=?", (selected_id[0],))
            if row:
                name_entry.delete(0, tk.END);   name_entry.insert(0, row[1])
                role_cb.set(row[2] or '')
                salary_entry.delete(0, tk.END); salary_entry.insert(0, str(row[3]))

        staff_lb.bind('<<ListboxSelect>>', on_staff_selected)

        def clear_staff_form():
            name_entry.delete(0, tk.END)
            role_cb.set('')
            salary_entry.delete(0, tk.END)
            selected_id[0] = None

        def add_staff():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror('Error', 'Name cannot be blank.')
                return
            try:
                salary = float(salary_entry.get())
                if salary < 0:
                    messagebox.showerror('Error', 'Salary cannot be negative.')
                    return
                db_execute(
                    "INSERT INTO staff (name, role, salary) VALUES (?, ?, ?)",
                    (name, role_cb.get(), salary)
                )
                clear_staff_form()
                load_staff_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter a valid number for Salary.')

        def edit_staff():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a staff member first.')
                return
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror('Error', 'Name cannot be blank.')
                return
            try:
                salary = float(salary_entry.get())
                if salary < 0:
                    messagebox.showerror('Error', 'Salary cannot be negative.')
                    return
                db_execute(
                    "UPDATE staff SET name=?, role=?, salary=? WHERE id=?",
                    (name, role_cb.get(), salary, selected_id[0])
                )
                clear_staff_form()
                load_staff_list()
            except ValueError:
                messagebox.showerror('Error', 'Please enter a valid number for Salary.')

        def delete_staff():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a staff member first.')
                return
            if messagebox.askyesno('Confirm Delete', 'Permanently delete this staff record?'):
                db_execute("DELETE FROM staff WHERE id=?", (selected_id[0],))
                clear_staff_form()
                load_staff_list()

        def mark_attendance():
            if not selected_id[0]:
                messagebox.showwarning('No Selection', 'Please select a staff member first.')
                return
            db_execute(
                "UPDATE staff SET attendance = attendance + 1 WHERE id=?",
                (selected_id[0],)
            )
            load_staff_list()

        self.add_action_buttons(page, [
            ('Add',              add_staff,       ACCENT),
            ('Edit',             edit_staff,      BLUE),
            ('Delete',           delete_staff,    DANGER),
            ('Mark Attendance',  mark_attendance, SUCCESS),
            ('Refresh',          load_staff_list, MUTED),
        ])
        load_staff_list()

    # ── Reports ──────────────────────────────

    def show_reports(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Business Reports')

        from_entry, to_entry = self.add_date_filter_bar(page)

        report_box = tk.Text(
            page,
            bg=LIST_BG, fg=TEXT,
            font=('Courier', 11),
            relief='flat', bd=0,
            padx=16, pady=12,
            height=26
        )
        report_box.pack(fill='both', expand=True, padx=24, pady=10)

        def generate_report():
            d0 = from_entry.get().strip() or None
            d1 = to_entry.get().strip() or None

            if d0 and not is_valid_date(d0):
                messagebox.showerror('Error', f'Invalid From date: {d0}')
                return
            if d1 and not is_valid_date(d1):
                messagebox.showerror('Error', f'Invalid To date: {d1}')
                return

            data   = get_report_data(d0, d1)
            period = (d0 + '  to  ' + d1) if (d0 and d1) else 'All Time'

            report_text = (
                '\n  ' + '=' * 62 + '\n'
                '    TECHMART PRO  |  BUSINESS PERFORMANCE REPORT\n'
                '    Period  :  ' + period + '\n'
                '  ' + '=' * 62 + '\n\n'
                '  Total Transactions       :  ' + str(data['orders'])    + '\n'
                '  Total Sales Revenue      :  Rs.' + str(data['sales'])  + '\n'
                '  Cost of Goods Sold       :  Rs.' + str(data['cogs'])   + '\n'
                '  Gross Profit             :  Rs.' + str(data['gross'])  + '\n'
                '  Total Expenses           :  Rs.' + str(data['expenses']) + '\n'
                '  Total Purchases          :  Rs.' + str(data['purchases']) + '\n\n'
                '  ' + '-' * 62 + '\n'
                '  Net Profit               :  Rs.' + str(data['profit']) + '\n'
                '  Top Selling Product      :  ' + data['best'] + '\n'
                '  ' + '-' * 62 + '\n\n'
                '  Generated On  :  ' + get_now() + '\n'
                '  ' + '=' * 62 + '\n'
            )

            report_box.delete('1.0', tk.END)
            report_box.insert(tk.END, report_text)

        self.add_action_buttons(page, [('Generate Report', generate_report, ACCENT)])

    # ── Backup / Export ───────────────────────

    def show_backup_export(self):
        page = self.get_content_frame()
        self.add_page_header(page, 'Backup and Export')

        info_box = tk.Text(
            page,
            bg=LIST_BG, fg=TEXT,
            font=('Courier', 11),
            relief='flat', bd=0,
            padx=16, pady=12,
            height=20
        )
        info_box.pack(fill='both', expand=True, padx=24, pady=16)

        def do_backup():
            try:
                saved_path = backup_database()
                info_box.delete('1.0', tk.END)
                info_box.insert(tk.END,
                    '\n  DATABASE BACKUP SUCCESSFUL\n\n'
                    '  Saved to  :  ' + os.path.abspath(saved_path) + '\n\n'
                    '  Timestamp :  ' + get_now() + '\n'
                )
                messagebox.showinfo('Backup Complete', 'Database backed up to:\n' + os.path.abspath(saved_path))
            except Exception as e:
                messagebox.showerror('Backup Failed', str(e))

        def do_export():
            try:
                folder = export_to_csv()
                info_box.delete('1.0', tk.END)
                info_box.insert(tk.END,
                    '\n  CSV EXPORT SUCCESSFUL\n\n'
                    '  Folder    :  ' + os.path.abspath(folder) + '\n\n'
                    '  Files     :  products, inventory, sales,\n'
                    '               purchases, expenses, staff\n\n'
                    '  Timestamp :  ' + get_now() + '\n'
                )
                messagebox.showinfo('Export Complete', 'Data exported to:\n' + os.path.abspath(folder))
            except Exception as e:
                messagebox.showerror('Export Failed', str(e))

        self.add_action_buttons(page, [
            ('Backup Database', do_backup, BLUE),
            ('Export to CSV',   do_export, SUCCESS),
        ])


# ─────────────────────────────────────────────
# Run the app
# ─────────────────────────────────────────────

if __name__ == '__main__':
    create_tables()
    root = tk.Tk()
    setup_combobox_style()
    app  = TechMartApp(root)
    root.mainloop()
