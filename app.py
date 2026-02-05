import streamlit as st
import requests
import json

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload
from sqlalchemy.sql import func
import time
import os
import math
from datetime import datetime
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, text, inspect

# Page Configuration
st.set_page_config(
    page_title="Jewelry ERP System",
    page_icon="💎",
    layout="wide"
)

# --- Constants ---
DIA_SHAPES = ['Round', 'Princess', 'Cushion', 'Oval', 'Emerald', 'Pear', 'Marquise', 'Asscher', 'Radiant', 'Heart', 'Etc']
DIA_COLORS = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'Fancy Yellow', 'Fancy Pink', 'Fancy Blue', 'Etc']
DIA_CLARITY = ['FL', 'IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1', 'I2', 'I3']
DIA_CUTS = ['Excellent', 'Very Good', 'Good', 'Fair', 'Poor']
DIA_FLUORESCENCE = ['None', 'Faint', 'Medium', 'Strong', 'Very Strong']

# --- ColorStone Constants ---
CS_TYPES = ['Ruby', 'Sapphire', 'Emerald', 'Pearl', 'Garnet', 'Amethyst', 'Peridot', 'Opal', 'Topaz', 'Turquoise', 'Etc']
CS_COLORS = ['Pink', 'Red', 'Blue', 'Yellow', 'Brown', 'Champagne', 'Green', 'Etc']
CS_TONES = ['Medium', 'Very Dark', 'Dark', 'Medium Dark', 'Medium Light', 'Light', 'Very Light']
CS_SATURATIONS = ['Vivid', 'Strong', 'Moderately Strong', 'Moderate', 'Slightly', 'Etc']
CS_SATURATIONS = ['Vivid', 'Strong', 'Moderately Strong', 'Moderate', 'Slightly', 'Etc']
CS_CLARITY = ['Eye Clean', 'Slightly Included', 'Moderately Included', 'Heavily Included', 'Severely Included']

# --- Watch Constants ---
WATCH_MATERIALS = ['순금(Pure Gold)', '18K', '14K', '백금(Platinum)', '실버(Silver)', '콤비(Combi)', '고무(Rubber)', '기타(Etc)']
WATCH_COLORS = ['화이트골드', '옐로우골드', '로즈골드', '멀티', '무광', '기타']
WATCH_MOVEMENTS = ['Automatic', 'Manual', 'Quartz', 'Smart', 'Etc']
WATCH_BANDS = ['Steel', 'Leather', 'Rubber', 'Fabric/Nato', 'Precious Metal', 'Etc']
WATCH_STATUS = ['신품(New)', '신동품(Mint)', '중고(Used)', '기타(Etc)']
YN_OPTIONS = ['유(Yes)', '무(No)']


# Database Configuration
DATABASE_URL = 'mysql+pymysql://root:dbpassword@127.0.0.1:3306/jewelry_db'

Base = declarative_base()

# Ensure image directory exists
IMAGE_DIR = "uploaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

import hashlib

# --- Models ---

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='Biz') # SuperUser, Biz, General
    shop_name = Column(String(100))
    shop_code = Column(String(10))

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_code = Column(String(50), unique=True, nullable=True) # NEW: Shop-aware ID
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Enforce FK
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50), nullable=True) # NEW: Sub-category
    name = Column(String(255), nullable=False)
    
    # Images (Paths)
    image_rep = Column(String(500))
    image_top = Column(String(500))
    image_front = Column(String(500))
    image_side = Column(String(500))
    
    # Phase 15: Factory Info
    factory_name = Column(String(100))
    factory_contact = Column(String(100))
    factory_contact = Column(String(100))
    production_time = Column(String(100))
    
    # Phase 18: Pricing Fields (Moved from JewelryDetail)
    labor_cost = Column(Float, default=0.0)
    margin_percentage = Column(Float, default=0.0)
    tax_percentage = Column(Float, default=0.0)
    card_fee_percentage = Column(Float, default=0.0)

    total_price = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=1) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    jewelry_details = relationship("ProductJewelry", back_populates="product", uselist=False, cascade="all, delete-orphan")
    stones = relationship("ProductStone", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    diamond_details = relationship("ProductDiamond", back_populates="product", uselist=False, cascade="all, delete-orphan")
    color_stone_details = relationship("ProductColorStone", back_populates="product", uselist=False, cascade="all, delete-orphan")
    watch_details = relationship("ProductWatch", back_populates="product", uselist=False, cascade="all, delete-orphan")
    etc_details = relationship("ProductEtc", back_populates="product", uselist=False, cascade="all, delete-orphan")

class ProductJewelry(Base):
    __tablename__ = 'product_jewelry'
    
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    
    # Gold Details
    gold_weight = Column(Float, default=0.0)
    gold_purity = Column(String(20), default="14k")
    gold_price_applied = Column(Integer, default=380000)
    
    # Pricing Factors
    labor_cost = Column(Integer, default=0)
    margin_pct = Column(Float, default=10.0)
    discount_pct = Column(Float, default=0.0)
    vat_pct = Column(Float, default=10.0)
    fee_pct = Column(Float, default=3.0)
    
    # Calculated Fields
    product_cost = Column(Integer, default=0)
    calc_selling_price = Column(Integer, default=0)
    final_price = Column(Integer, default=0)

    # Relationships
    product = relationship("Product", back_populates="jewelry_details")

class ProductStone(Base):
    __tablename__ = 'product_stones'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    stone_type = Column(String(20)) # "Main" or "Sub"
    name = Column(String(100))
    quantity = Column(Integer, default=0)
    unit_price = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="stones")

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100), nullable=True)
    total_amount = Column(Integer, default=0)
    status = Column(String(20), default="Completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    
    product_name = Column(String(255)) 
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, default=0)
    subtotal = Column(Integer, default=0)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class ProductDiamond(Base):
    __tablename__ = 'product_diamonds'
    
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    
    stone_type = Column(String(50), default="Natural")
    certificate = Column(String(50), default="GIA")
    shape = Column(String(50), default="Round")
    weight = Column(Float, default=0.3)
    color = Column(String(20), default="F")
    clarity = Column(String(20), default="VS1")
    cut = Column(String(20), default="Excellent")
    polish = Column(String(20), default="Excellent")
    symmetry = Column(String(20), default="Excellent")
    fluorescence = Column(String(50), default="None")
    
    purchase_cost = Column(Integer, default=0)
    margin_pct = Column(Float, default=10.0)
    vat_pct = Column(Float, default=10.0)
    final_price = Column(Integer, default=0)

    product = relationship("Product", back_populates="diamond_details")

class ProductColorStone(Base):
    __tablename__ = 'product_color_stones'
    
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    
    stone_type = Column(String(50))
    cert_agency = Column(String(50))
    shape = Column(String(50))
    weight = Column(Float, default=0.0)
    color = Column(String(50))
    tone = Column(String(50))
    saturation = Column(String(50))
    clarity = Column(String(50))
    origin = Column(String(100))
    comment = Column(String(500)) # Remarks
    
    # Pricing with Tax
    purchase_cost = Column(Integer, default=0)
    margin_pct = Column(Float, default=0.0)
    vat_pct = Column(Float, default=10.0)
    tax_rate = Column(Float, default=0.0) # Special Tax/Fee
    final_price = Column(Integer, default=0)

    product = relationship("Product", back_populates="color_stone_details")

class ProductWatch(Base):
    __tablename__ = 'product_watches'
    
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    
    brand = Column(String(100)) # Mapped from sub_category
    model_number = Column(String(100))
    year = Column(String(50))
    size = Column(String(50))
    
    material = Column(String(50))
    color = Column(String(50))
    movement = Column(String(50))
    band = Column(String(50))
    
    has_cert = Column(String(20))
    has_case = Column(String(20))
    status = Column(String(50))
    
    # Unique Pricing Logic
    purchase_cost = Column(Integer, default=0)
    margin_pct = Column(Float, default=0.0)
    vat_pct = Column(Float, default=10.0)
    tax_pct = Column(Float, default=0.0) # Special Tax
    final_price = Column(Integer, default=0)

    product = relationship("Product", back_populates="watch_details")

class ProductEtc(Base):
    __tablename__ = 'product_etc'
    
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    comments = Column(String(500))
    material = Column(String(100)) # Phase 17
    size = Column(String(100)) # Phase 17
    
    # Pricing
    purchase_cost = Column(Integer, default=0)
    margin_pct = Column(Float, default=0.0)
    vat_pct = Column(Float, default=10.0)
    tax_pct = Column(Float, default=0.0) # Special Tax
    final_price = Column(Integer, default=0)

    product = relationship("Product", back_populates="etc_details")

class CategorySetting(Base):
    __tablename__ = 'category_settings'
    
    id = Column(Integer, primary_key=True)
    main_category = Column(String(50))
    sub_category_name = Column(String(100))

# --- Database Utils ---

def get_db_session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def run_migrations():
    """Auto-migrate schema for new fields to prevent crashes."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine) # Ensure tables exist first!
    
    with engine.connect() as conn:
        # Check gold_price_applied
        try: conn.execute(text("SELECT gold_price_applied FROM product_jewelry LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Adding 'gold_price_applied'...", icon="🛠️")
                conn.execute(text("ALTER TABLE product_jewelry ADD COLUMN gold_price_applied INTEGER DEFAULT 380000"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (gold_price_applied): {e}")

        # Check stock_quantity
        try: conn.execute(text("SELECT stock_quantity FROM products LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Adding 'stock_quantity'...", icon="🛠️")
                conn.execute(text("ALTER TABLE products ADD COLUMN stock_quantity INTEGER DEFAULT 1"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (stock_quantity): {e}")
            
        # Check sub_category
        try: conn.execute(text("SELECT sub_category FROM products LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Adding 'sub_category'...", icon="🛠️")
                conn.execute(text("ALTER TABLE products ADD COLUMN sub_category VARCHAR(50)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (sub_category): {e}")
            
        # Rename Certificate -> ColorStone
        try:
             conn.execute(text("UPDATE category_settings SET main_category = 'ColorStone' WHERE main_category = 'Certificate'"))
             conn.execute(text("UPDATE products SET category = 'ColorStone' WHERE category = 'Certificate'"))
             conn.commit()
        except Exception as e: st.error(f"Migration Failed (Rename Certificate): {e}")

        # Check ProductColorStone Existence
        try: conn.execute(text("SELECT * FROM product_color_stones LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Creating 'product_color_stones'...", icon="🛠️")
                # Letting SQLAlchemy create it via Base.metadata.create_all(engine) at top is enough usually,
                # but if table is missing in existing DB, auto-create might not fire if Base thinks it exists?
                # Actually line 166 Base.metadata.create_all(engine) does this safely.
                # So we just rely on that.
                pass
            except Exception as e: st.error(f"Migration Failed (ColorStone): {e}")

        # Check ProductWatch Existence
        try: conn.execute(text("SELECT * FROM product_watches LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Creating 'product_watches'...", icon="🛠️")
                pass
            except Exception as e: st.error(f"Migration Failed (Watch): {e}")

        # Check ProductEtc Existence
        try: conn.execute(text("SELECT * FROM product_etc LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Creating 'product_etc'...", icon="🛠️")
                pass
            except Exception as e: st.error(f"Migration Failed (Etc): {e}")

        # Check product_code in products (Phase 10 Fix)
        try: conn.execute(text("SELECT product_code FROM products LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Adding 'product_code'...", icon="🛠️")
                conn.execute(text("ALTER TABLE products ADD COLUMN product_code VARCHAR(50)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (product_code): {e}")
            
        # Check shop_code in users (Phase 10 Fix - just in case)
        try: conn.execute(text("SELECT shop_code FROM users LIMIT 1"))
        except Exception:
            try:
                st.toast("Migrating DB: Adding 'shop_code' to users...", icon="🛠️")
                conn.execute(text("ALTER TABLE users ADD COLUMN shop_code VARCHAR(10)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (shop_code): {e}")
            
        # Phase 15: Add factory_name, factory_contact, production_time to products
        inspector = inspect(engine)
        columns = inspector.get_columns('products')
        column_names = [col['name'] for col in columns]

        if 'factory_name' not in column_names:
            try:
                st.toast("Migrating DB: Adding 'factory_name' to products...", icon="🛠️")
                conn.execute(text("ALTER TABLE products ADD COLUMN factory_name VARCHAR(100)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (factory_name): {e}")
        
        if 'factory_contact' not in column_names:
            try:
                st.toast("Migrating DB: Adding 'factory_contact' to products...", icon="🛠️")
                conn.execute(text("ALTER TABLE products ADD COLUMN factory_contact VARCHAR(100)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (factory_contact): {e}")

        if 'production_time' not in column_names:
            try:
                st.toast("Migrating DB: Adding 'production_time' to products...", icon="🛠️")
                conn.execute(text("ALTER TABLE products ADD COLUMN production_time VARCHAR(100)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (production_time): {e}")

        # Phase 17: Add material, size to product_etc
        etc_columns = inspector.get_columns('product_etc')
        etc_col_names = [col['name'] for col in etc_columns]
        
        if 'material' not in etc_col_names:
            try:
                st.toast("Migrating DB: Adding 'material' to product_etc...", icon="🛠️")
                conn.execute(text("ALTER TABLE product_etc ADD COLUMN material VARCHAR(100)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (etc_material): {e}")

        if 'size' not in etc_col_names:
            try:
                st.toast("Migrating DB: Adding 'size' to product_etc...", icon="🛠️")
                conn.execute(text("ALTER TABLE product_etc ADD COLUMN size VARCHAR(100)"))
                conn.commit()
            except Exception as e: st.error(f"Migration Failed (etc_size): {e}")

        # Phase 18: Add pricing fields to products
        if 'labor_cost' not in column_names:
             try:
                 st.toast("Migrating DB: Adding 'labor_cost' to products...", icon="🛠️")
                 conn.execute(text("ALTER TABLE products ADD COLUMN labor_cost FLOAT DEFAULT 0.0"))
                 conn.commit()
             except Exception as e: st.error(f"Migration Failed (labor_cost): {e}")
        
        if 'margin_percentage' not in column_names:
             try:
                 st.toast("Migrating DB: Adding 'margin_percentage' to products...", icon="🛠️")
                 conn.execute(text("ALTER TABLE products ADD COLUMN margin_percentage FLOAT DEFAULT 0.0"))
                 conn.commit()
             except Exception as e: st.error(f"Migration Failed (margin_percentage): {e}")

        if 'tax_percentage' not in column_names:
             try:
                 st.toast("Migrating DB: Adding 'tax_percentage' to products...", icon="🛠️")
                 conn.execute(text("ALTER TABLE products ADD COLUMN tax_percentage FLOAT DEFAULT 0.0"))
                 conn.commit()
             except Exception as e: st.error(f"Migration Failed (tax_percentage): {e}")

        if 'card_fee_percentage' not in column_names:
             try:
                 st.toast("Migrating DB: Adding 'card_fee_percentage' to products...", icon="🛠️")
                 conn.execute(text("ALTER TABLE products ADD COLUMN card_fee_percentage FLOAT DEFAULT 0.0"))
                 conn.commit()
             except Exception as e: st.error(f"Migration Failed (card_fee_percentage): {e}")


    # Initial Data for Categories
    Session = sessionmaker(bind=engine)
    session = Session()
    if session.query(CategorySetting).count() == 0:
        defaults = [
            ("Jewelry", "Ring"), ("Jewelry", "Necklace"), ("Jewelry", "Earring"), ("Jewelry", "Bracelet"),
            ("Gold", "Bar"), ("Gold", "Coin"),
            ("Watch", "Men"), ("Watch", "Women")
        ]
        for m, s in defaults:
            session.add(CategorySetting(main_category=m, sub_category_name=s))
        session.commit()
    session.close()

# Run migrations on app load
run_migrations()


# --- Helper Functions ---

@st.cache_data(ttl=1800)
def fetch_gold_price():
    """
    Fetches the current gold price from DiamondBank API.
    Refreshes every 30 minutes (1800 seconds).
    Returns the price per Don (aukd) as an integer.
    """
    url = "http://api.diamondbank.co.kr/outAPI.php"
    
    # 1. Add User-Agent header to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    # 2. Correct POST parameter as per user confirmation
    payload = {'key': 'limit'} 
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=5)
        
        # Raise error for bad status codes
        response.raise_for_status() 
        
        if response.status_code == 200:
            data = response.json()
            
            # Flexible extraction
            target_item = None
            if isinstance(data, list) and len(data) > 0:
                target_item = data[0]
            elif isinstance(data, dict):
                target_item = data
            
            if target_item and 'aukd' in target_item:
                # Remove commas if present and convert to int
                raw_price = str(target_item['aukd']).replace(',', '')
                return int(raw_price)
                
    except Exception as e:
        # Show specific error in UI for debugging
        st.error(f"⚠️ Gold Price Fetch Error: {e}")
        return None
    
    return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db_data():
    session = get_db_session()
    # Check if SuperUser exists
    admin = session.query(User).filter_by(username='admin').first()
    if not admin:
        # Create Default SuperUser
        admin_user = User(
            username='admin',
            password_hash=hash_password('1234'),
            role='SuperUser',
            shop_name='Master Shop',
            shop_code='MT'
        )
        session.add(admin_user)
        session.commit()
        print("Initialized SuperUser: admin / 1234")
    session.close()

def run_data_migration():
    """
    Migration Tool: Transfers ALL logic to 'diamondbank' and regenerates Product IDs.
    """
    session = get_db_session()
    try:
        # 1. Target User
        target_user = session.query(User).filter_by(username='diamondbank').first()
        if not target_user:
            st.error("Target user 'diamondbank' not found!")
            return

        shop_code = target_user.shop_code # Should be 'DB'
        
        # 2. Fetch ALL products sorted by created_at
        products = session.query(Product).order_by(Product.created_at.asc()).all()
        
        if not products:
            st.warning("No products to migrate.")
            return

        # 3. Processing
        count = 0
        
        # Sequence Tracker for regenerating IDs: {(cat_char, date_str): seq}
        seq_tracker = {} 
        
        cat_map = {"Jewelry": "J", "Gold": "G", "Watch": "W", "Dia/Stone": "D", "ColorStone": "C", "Etc": "E"}

        for p in products:
            # Transfer Ownership
            p.user_id = target_user.id
            
            # Regenerate ID
            cat_char = cat_map.get(p.category, "X")
            date_str = p.created_at.strftime("%y%m%d")
            
            key = (cat_char, date_str)
            if key not in seq_tracker:
                seq_tracker[key] = 0
            
            seq_tracker[key] += 1
            seq = seq_tracker[key]
            
            new_code = f"{shop_code}-{cat_char}{date_str}-{seq:03d}"
            p.product_code = new_code
            
            count += 1
            
        session.commit()
        st.toast(f"Migration Complete! Moved {count} products to {target_user.shop_name}.", icon="🚀")
        st.sidebar.success(f"Migrated {count} items!")
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        session.rollback()
        st.error(f"Migration Failed: {e}")
    finally:
        session.close()

def login_user(username, password):
    session = get_db_session()
    hashed_pw = hash_password(password)
    user = session.query(User).filter_by(username=username, password_hash=hashed_pw).first()
    session.close()
    return user

def show_login_page():
    # Centered Login Box
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("💎 Jewelry ERP Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted:
                user = login_user(username, password)
                if user:
                    st.success(f"Welcome back, {user.username}!")
                    # Set Session State
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user.id
                    st.session_state['user_name'] = user.username
                    st.session_state['user_role'] = user.role
                    st.session_state['shop_code'] = user.shop_code
                    st.session_state['shop_name'] = user.shop_name
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

def logout_user():
    keys = ['logged_in', 'user_id', 'user_name', 'user_role', 'shop_code', 'shop_name']
    for k in keys:
        if k in st.session_state: del st.session_state[k]
    st.rerun()



def save_uploaded_file(uploaded_file, prefix):
    if uploaded_file is not None:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}_{uploaded_file.name}"
            filepath = os.path.join(IMAGE_DIR, filename)

            # --- Phase 13-2: Force Maximize Logic ---
            image = Image.open(uploaded_file)
            
            # 1. Create White Background (500x500)
            final_size = (500, 500)
            new_img = Image.new("RGB", final_size, (255, 255, 255))
            
            # 2. Resize Logic (Force Maximize)
            w, h = image.size
            if w > h:
                new_w = 500
                new_h = int(500 * (h / w))
            else: 
                new_h = 500
                new_w = int(500 * (w / h))
            
            # Resize with LANCZOS for quality
            image_resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 3. Calculate Center Position
            x = (500 - new_w) // 2
            y = (500 - new_h) // 2
            
            # 4. Paste Image onto Background
            new_img.paste(image_resized, (x, y))
            
            # 5. Save Final Image
            new_img.save(filepath)
            
            return filepath
        except Exception as e:
            st.error(f"Error processing image: {e}")
            return None
    return None

def normalize_existing_images():
    """
    Retroactively applies 500x500 square padding to ALL images in IMAGE_DIR.
    Uses 'Force Maximize' logic with LANCZOS resampling.
    """
    if not os.path.exists(IMAGE_DIR):
        return 0
    
    count = 0
    progress_bar = st.progress(0)
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total = len(files)
    
    for i, filename in enumerate(files):
        try:
            filepath = os.path.join(IMAGE_DIR, filename)
            
            # Open & Process
            with Image.open(filepath) as img:
                img = img.convert("RGB") # Ensure RGB
                
                # --- Phase 13-2: Force Maximize Logic ---
                final_size = (500, 500)
                new_img = Image.new("RGB", final_size, (255, 255, 255))
                
                # Calculate New Dimensions (Force Maximize)
                w, h = img.size
                if w > h:
                    new_w = 500
                    new_h = int(500 * (h / w))
                else: 
                    new_h = 500
                    new_w = int(500 * (w / h))
                    
                # Resize with High Quality
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center
                x = (500 - new_w) // 2
                y = (500 - new_h) // 2
                
                new_img.paste(img_resized, (x, y))
                
                # Overwrite
                new_img.save(filepath)
                count += 1
                
            progress_bar.progress((i + 1) / total)
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
            
    progress_bar.empty()
    return count

def format_currency(value):
    return f"{value:,.0f} KRW"
    
def go_to_edit(product_id):
    st.session_state['edit_mode_id'] = product_id
    st.session_state['nav_selection'] = "Register Product"


# --- Session State Management ---

if 'main_stones' not in st.session_state:
    st.session_state.main_stones = [{'name': '', 'qty': 0, 'price': 0}]
if 'sub_stones' not in st.session_state:
    st.session_state.sub_stones = [{'name': '', 'qty': 0, 'price': 0}]
if 'cart' not in st.session_state:
    st.session_state.cart = [] 


def add_main_stone(): st.session_state.main_stones.append({'name': '', 'qty': 0, 'price': 0})
def remove_main_stone(): 
    if len(st.session_state.main_stones) > 0: st.session_state.main_stones.pop()

def add_sub_stone(): st.session_state.sub_stones.append({'name': '', 'qty': 0, 'price': 0})
def remove_sub_stone(): 
    if len(st.session_state.sub_stones) > 0: st.session_state.sub_stones.pop()

def add_to_cart(product):
    for item in st.session_state.cart:
        if item['product_id'] == product.id:
            if item['qty'] < item['max_qty']:
                item['qty'] += 1
                st.toast(f"Added another {product.name} to cart!", icon="🛒")
            else:
                st.warning("Max stock reached for this item.")
            return

    st.session_state.cart.append({
        'product_id': product.id,
        'name': product.name,
        'price': product.jewelry_details.final_price if product.jewelry_details else product.total_price,
        'qty': 1,
        'max_qty': product.stock_quantity if product.stock_quantity else 0
    })
    st.toast(f"Added {product.name} to cart!", icon="🛒")

def remove_from_cart(product_id):
    st.session_state.cart = [item for item in st.session_state.cart if item['product_id'] != product_id]

def clear_cart():
    st.session_state.cart = []


# --- Page Functions ---

def show_register_page():
    # Initialize variables to avoid UnboundLocalError
    e_comments = ""
    e_cost = 0
    e_margin = 0.0
    e_vat = 0.0
    e_tax = 0.0
    e_tax = 0.0
    final_price_e = 0
    
    # Define Lists FIRST (Fix UnboundLocalError)
    stone_types = ["None", "Diamond", "Ruby", "Sapphire", "Emerald", "Pearl", "Cubic Zirconia", "Direct Input"]
    
    # Initialize variables to prevent UnboundLocalError
    w_brand = w_model = w_year = w_size = w_movement = w_material = w_color = w_band = w_cert = w_case = w_status = ""
    d_weight, d_color, d_clarity, d_cert, d_shape, d_cut, d_polish, d_symmetry, d_fluo = 0.0, "F", "VS1", "GIA", "Round", "Excellent", "Excellent", "Excellent", "None"
    c_weight, c_color, c_type, c_cert, c_shape, c_tone, c_sat, c_clarity, c_origin, c_comment = 0.0, "Red", "Ruby", "", "Oval", "Medium", "Strong", "Eye Clean", "Burma", ""
    e_material, e_size, e_comments = "", "", ""
    final_price_w = final_price_dia = final_price_cs = final_price_e = 0

    # --- Edit Mode Pre-fill Logic ---
    edit_mode_id = st.session_state.get('edit_mode_id')
    
    if edit_mode_id and 'data_loaded' not in st.session_state:
        session = get_db_session()
        product = session.query(Product).options(joinedload(Product.jewelry_details), joinedload(Product.stones), joinedload(Product.diamond_details), joinedload(Product.color_stone_details), joinedload(Product.watch_details), joinedload(Product.etc_details)).filter(Product.id == edit_mode_id).first()
        session.close()
        
        if product:
            st.session_state['reg_name'] = product.name
            st.session_state['reg_category'] = product.category
            st.session_state['reg_subcategory'] = product.sub_category # Pre-fill SubCat
            st.session_state['reg_stock'] = product.stock_quantity 
            
            st.session_state['reg_img_rep'] = product.image_rep
            st.session_state['reg_img_top'] = product.image_top
            st.session_state['reg_img_front'] = product.image_front
            st.session_state['reg_img_side'] = product.image_side

            # Phase 15: Factory Info (Force String)
            st.session_state['reg_factory_name'] = str(product.factory_name) if product.factory_name else ""
            st.session_state['reg_factory_contact'] = str(product.factory_contact) if product.factory_contact else ""
            st.session_state['reg_production_time'] = str(product.production_time) if product.production_time else ""
            
            if product.jewelry_details:
                jd = product.jewelry_details
                st.session_state['reg_gold_purity'] = jd.gold_purity
                st.session_state['reg_gold_weight'] = float(jd.gold_weight)
                st.session_state['reg_gold_price_applied'] = int(jd.gold_price_applied)
                st.session_state['reg_labor'] = int(jd.labor_cost)
                st.session_state['reg_margin'] = float(jd.margin_pct)
                st.session_state['reg_discount'] = float(jd.discount_pct)
                st.session_state['reg_vat'] = float(jd.vat_pct)
                st.session_state['reg_fee'] = float(jd.fee_pct)

            if product.diamond_details:
                dd = product.diamond_details
                st.session_state['dia_type'] = dd.stone_type
                st.session_state['dia_cert'] = dd.certificate
                st.session_state['dia_shape'] = dd.shape
                st.session_state['dia_weight'] = float(dd.weight)
                st.session_state['dia_color'] = dd.color
                st.session_state['dia_clarity'] = dd.clarity
                st.session_state['dia_cut'] = dd.cut
                st.session_state['dia_polish'] = dd.polish
                st.session_state['dia_symmetry'] = dd.symmetry
                st.session_state['dia_fluo'] = dd.fluorescence
                st.session_state['dia_cost'] = int(dd.purchase_cost)
                st.session_state['dia_margin'] = float(dd.margin_pct)
                st.session_state['dia_vat'] = float(dd.vat_pct)

            if product.color_stone_details:
                cs = product.color_stone_details
                st.session_state['cs_type'] = cs.stone_type
                st.session_state['cs_cert'] = cs.cert_agency
                st.session_state['cs_shape'] = cs.shape
                st.session_state['cs_weight'] = float(cs.weight)
                st.session_state['cs_color'] = cs.color
                st.session_state['cs_tone'] = cs.tone
                st.session_state['cs_sat'] = cs.saturation
                st.session_state['cs_clarity'] = cs.clarity
                st.session_state['cs_origin'] = cs.origin
                st.session_state['cs_comment'] = cs.comment
                st.session_state['cs_cost'] = int(cs.purchase_cost)
                st.session_state['cs_margin'] = float(cs.margin_pct)
                st.session_state['cs_vat'] = float(cs.vat_pct)
                st.session_state['cs_tax'] = float(cs.tax_rate)

            if product.watch_details:
                wd = product.watch_details
                # Brand is SubCategory, already handled
                st.session_state['w_model'] = wd.model_number
                st.session_state['w_year'] = wd.year
                st.session_state['w_size'] = wd.size
                st.session_state['w_material'] = wd.material
                st.session_state['w_color'] = wd.color
                st.session_state['w_movement'] = wd.movement
                st.session_state['w_band'] = wd.band
                st.session_state['w_cert'] = wd.has_cert
                st.session_state['w_case'] = wd.has_case
                st.session_state['w_status'] = wd.status
                st.session_state['w_cost'] = int(wd.purchase_cost)
                st.session_state['w_margin'] = float(wd.margin_pct)
                st.session_state['w_vat'] = float(wd.vat_pct)
                st.session_state['w_tax'] = float(wd.tax_pct)

            if product.etc_details:
                ed = product.etc_details
                st.session_state['e_name'] = product.name
                st.session_state['e_stock'] = product.stock_quantity
                st.session_state['e_comments'] = ed.comments
                st.session_state['e_cost'] = int(ed.purchase_cost)
                st.session_state['e_margin'] = float(ed.margin_pct)
                st.session_state['e_vat'] = float(ed.vat_pct)
                st.session_state['e_tax'] = float(ed.tax_pct)
                st.session_state['e_tax'] = float(ed.tax_pct)
                # Phase 17: Load Material/Size
                st.session_state['e_material'] =  getattr(ed, 'material', "")
                st.session_state['e_size'] = getattr(ed, 'size', "")
                
            # [최종 수정] 장부 이름을 'ProductJewelry'로 정정하여 조회
            # 1. 현재 제품 ID로 저장된 금/보석 정보(ProductJewelry 테이블)를 직접 조회
            saved_gold = session.query(ProductJewelry).filter(ProductJewelry.product_id == product.id).first()

            # 2. 정보가 있으면 가져옵니다. (속성 이름도 기존 DB에 맞춰 gold_weight로 통일)
            if saved_gold:
                st.session_state['reg_gold_purity'] = saved_gold.gold_purity
                st.session_state['reg_gold_weight'] = float(saved_gold.gold_weight)
                st.session_state['reg_gold_price_applied'] = int(saved_gold.gold_price_applied or 0)
            
            # Phase 18: Load Pricing from Product (fallback to JD if needed)
            if product.labor_cost is not None and product.labor_cost > 0:
                 st.session_state['reg_labor'] = int(product.labor_cost)
            elif product.jewelry_details:
                 st.session_state['reg_labor'] = int(product.jewelry_details.labor_cost)
                 
            if product.margin_percentage: st.session_state['reg_margin'] = float(product.margin_percentage)
            elif product.jewelry_details: st.session_state['reg_margin'] = float(product.jewelry_details.margin_pct)
            
            if product.tax_percentage: st.session_state['reg_vat'] = float(product.tax_percentage)
            elif product.jewelry_details: st.session_state['reg_vat'] = float(product.jewelry_details.vat_pct)
            
            if product.card_fee_percentage: st.session_state['reg_fee'] = float(product.card_fee_percentage)
            elif product.jewelry_details: st.session_state['reg_fee'] = float(product.jewelry_details.fee_pct)

            
            # --- Universal Data Rehydration (Fix for Watch/Etc Name) ---
            # Ensure name/stock is pre-filled for ALL category specific keys
            st.session_state['w_name'] = product.name
            st.session_state['e_name'] = product.name
            st.session_state['cs_name'] = product.name
            st.session_state['dia_name'] = product.name
            st.session_state['w_stock'] = product.stock_quantity
            st.session_state['e_stock'] = product.stock_quantity
            st.session_state['cs_stock'] = product.stock_quantity
            st.session_state['dia_stock'] = product.stock_quantity

            m_stones = []
            s_stones = []
            if product.stones:
                for s in product.stones:
                    # Casting qty/price safely
                    s_data = {'name': s.name, 'qty': int(s.quantity), 'price': int(s.unit_price)}
                    if s.stone_type == "Main": m_stones.append(s_data)
                    elif s.stone_type == "Sub": s_stones.append(s_data)
            
            if not m_stones: m_stones = [{'name': '', 'qty': 0, 'price': 0}]
            if not s_stones: s_stones = [{'name': '', 'qty': 0, 'price': 0}]
            
            st.session_state.main_stones = m_stones
            st.session_state.sub_stones = s_stones
            
            # --- FIX: Explicitly set Widget Keys for Stones to ensure pre-fill ---
            # Main Stones
            for i, stone in enumerate(m_stones):
                 st.session_state[f"ms_qty_{i}"] = stone['qty']
                 st.session_state[f"ms_price_{i}"] = stone['price']
                 st.session_state[f"ms_type_{i}"] = stone_types.index(stone['name']) if stone['name'] in stone_types else 0
                 if stone['name'] not in stone_types:
                     st.session_state[f"ms_manual_{i}"] = stone['name']

            # Sub Stones
            for i, stone in enumerate(s_stones):
                 st.session_state[f"ss_qty_{i}"] = stone['qty']
                 st.session_state[f"ss_price_{i}"] = stone['price']
                 st.session_state[f"ss_type_{i}"] = stone_types.index(stone['name']) if stone['name'] in stone_types else 0
                 if stone['name'] not in stone_types:
                     st.session_state[f"ss_manual_{i}"] = stone['name']

            st.session_state['data_loaded'] = True
            st.rerun()

    if not edit_mode_id and 'data_loaded' in st.session_state:
         del st.session_state['data_loaded']
         keys_to_clear = ['reg_name', 'reg_stock', 'reg_category', 'reg_subcategory', 'reg_gold_weight', 'reg_gold_price_applied', 'reg_labor', 'reg_margin', 'reg_discount', 'reg_vat', 'reg_fee', 'reg_img_rep', 'reg_img_top', 'reg_img_front', 'reg_img_side', 'dia_name', 'dia_type', 'dia_cert', 'dia_shape', 'dia_weight', 'dia_color', 'dia_clarity', 'dia_cut', 'dia_polish', 'dia_symmetry', 'dia_fluo', 'dia_cost', 'dia_margin', 'dia_vat', 'reg_factory_name', 'reg_factory_contact', 'reg_production_time']
         for k in keys_to_clear:
             if k in st.session_state: del st.session_state[k]
         st.session_state.main_stones = [{'name': '', 'qty': 0, 'price': 0}]
         st.session_state.sub_stones = [{'name': '', 'qty': 0, 'price': 0}]
         
    # --- UI Rendering ---
    
    if edit_mode_id:
        st.header(f"✏️ Edit Product (ID: {edit_mode_id})")
        submit_label = "🔄 Update Product"
    else:
        st.header("📝 Register New Product")
        submit_label = "✅ Register Product"
        
    st.markdown("---")

    def render_gold_stone_inputs():
        st.subheader("2. Materials (Gold & Stones)")
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            purity_options = ["24K", "18K", "14K", "PT", "Silver", "Etc"]
            current_purity = st.session_state.get('reg_gold_purity', '18K')
            default_idx = 1
            if not edit_mode_id and product_type == "Gold": default_idx = 0
            if current_purity in purity_options: default_idx = purity_options.index(current_purity)
            elif current_purity: default_idx = purity_options.index("Etc")

            purity_sel = st.selectbox("Gold Purity", purity_options, index=default_idx, key="reg_gold_purity_sel")
            if purity_sel == "Etc":
                custom_val = current_purity if current_purity not in purity_options else ""
                gold_purity = st.text_input("Enter Material Name", value=custom_val, key="reg_gold_purity_manual")
            else: gold_purity = purity_sel
            st.session_state['reg_gold_purity'] = gold_purity
        with g_col2:
            gold_weight = st.number_input("Gold Weight (g)", min_value=0.0, format="%.2f", key="reg_gold_weight")
            
            # Dynamic Price Label
            multiplier = 1.0
            price_label = "Today's Pure Gold (24K) Price (per Don)"
            if gold_purity == "18K": multiplier = 0.825
            elif gold_purity == "14K": multiplier = 0.6435
            elif gold_purity == "PT": price_label = "Today's Platinum Price (per Don)"
            elif gold_purity == "Silver": price_label = "Today's Silver Price (per Don)"
            
            current_applied_per_g = st.session_state.get('reg_gold_price_applied', 380000)
            try: approx_base_don = int((current_applied_per_g * 3.75) / multiplier)
            except: approx_base_don = 450000
            if 'reg_base_price_don' not in st.session_state: st.session_state['reg_base_price_don'] = approx_base_don

            base_price_don = st.number_input(price_label, min_value=0, value=st.session_state['reg_base_price_don'], step=1000, key="reg_base_price_don_input")
            st.session_state['reg_base_price_don'] = base_price_don 
            applied_price_don = base_price_don * multiplier
            gold_price_applied = math.floor((applied_price_don / 3.75) / 100) * 100
            st.caption(f"≈ {format_currency(gold_price_applied)} / g (Stored)")
            st.session_state['reg_gold_price_applied'] = gold_price_applied
        
        st.markdown("**Stones Details**")
        def stone_input_row(prefix, index, obj):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                current_name = obj['name']
                current_type = "None"
                manual_text = ""
                if current_name in stone_types: current_type = current_name
                elif current_name: current_type = "Direct Input"; manual_text = current_name
                sel_type = st.selectbox(f"Type {index+1}", stone_types, index=stone_types.index(current_type) if current_type in stone_types else 0, key=f"{prefix}_type_{index}")
                final_name = st.text_input(f"Name {index+1}", value=manual_text, key=f"{prefix}_manual_{index}") if sel_type == "Direct Input" else sel_type
                st.session_state[prefix == "ms" and "main_stones" or "sub_stones"][index]['name'] = final_name
            with c2: st.session_state[prefix == "ms" and "main_stones" or "sub_stones"][index]['qty'] = st.number_input(f"Qty", min_value=0, value=obj['qty'], key=f"{prefix}_qty_{index}")
            with c3: st.session_state[prefix == "ms" and "main_stones" or "sub_stones"][index]['price'] = st.number_input(f"Price", min_value=0, step=1000, value=obj['price'], key=f"{prefix}_price_{index}")

        st.caption("Main Stones")
        for i, stone in enumerate(st.session_state.main_stones): stone_input_row("ms", i, stone)
        m_btn_c1, m_btn_c2 = st.columns([1, 5])
        with m_btn_c1: st.button("➕ Add", on_click=add_main_stone, key='add_main_btn')
        with m_btn_c2: st.button("➖ Remove", on_click=remove_main_stone, key='remove_main_btn')
        
        st.caption("Sub Stones")
        for i, stone in enumerate(st.session_state.sub_stones): stone_input_row("ss", i, stone)
        s_btn_c1, s_btn_c2 = st.columns([1, 5])
        with s_btn_c1: st.button("➕ Add", on_click=add_sub_stone, key='add_sub_btn')
        with s_btn_c2: st.button("➖ Remove", on_click=remove_sub_stone, key='remove_sub_btn')
        
        # Return calculated costs for display/logic if needed
        g_cost = gold_weight * gold_price_applied
        s_cost = sum([s['qty'] * s['price'] for s in st.session_state.main_stones]) + sum([s['qty'] * s['price'] for s in st.session_state.sub_stones])
        return g_cost, s_cost

    # Initialize Pricing & Cost Variables (Unified)
    labor_cost, margin_pct, discount_pct, vat_pct, fee_pct, tax_pct = 0, 0, 0, 0, 0, 0
    gold_cost, stone_cost = 0, 0

    col_main_cat, col_sub_cat = st.columns(2)
    with col_main_cat:
        category_options = ["Jewelry", "Gold", "Watch", "Dia/Stone", "ColorStone", "Etc"]
        # Pre-select matching main category if editing
        default_cat_idx = 0
        if 'reg_category' in st.session_state and st.session_state.reg_category in category_options:
            default_cat_idx = category_options.index(st.session_state.reg_category)
            
        product_type = st.selectbox("Main Category", category_options, index=default_cat_idx, key="reg_category_input")

    # Fetch Sub Categories
    session = get_db_session()
    sub_cats_db = session.query(CategorySetting).filter(CategorySetting.main_category == product_type).all()
    session.close()
    
    sub_cat_options = [c.sub_category_name for c in sub_cats_db]
    if not sub_cat_options: sub_cat_options = ["General"]
    
    with col_sub_cat:
         # Pre-select matching sub category if editing
        default_sub_idx = 0
        if 'reg_subcategory' in st.session_state and st.session_state.reg_subcategory in sub_cat_options:
            default_sub_idx = sub_cat_options.index(st.session_state.reg_subcategory)
        
        sub_category = st.selectbox("Sub Category", sub_cat_options, index=default_sub_idx, key="reg_subcategory_input")

    if product_type in ["Jewelry", "Gold"]:
        st.subheader("1. Basic Info & Images")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            name = st.text_input("Product Name", placeholder="Enter product name", key="reg_name")
        with c2:
            st.text_input("Category Path", value=f"{product_type} > {sub_category}", disabled=True)
        with c3:
            stock_qty = st.number_input("Stock Quantity", min_value=0, value=1, step=1, key="reg_stock")
            
        # Phase 15: Factory Info Inputs
        st.markdown("---")
        st.subheader("Factory Information (Optional)")
        fc1, fc2, fc3 = st.columns(3)
        with fc1: factory_name = st.text_input("🏭 Factory Name", key='reg_factory_name', placeholder="e.g. Gold Smith Co.")
        with fc2: factory_contact = st.text_input("📞 Factory Contact", key='reg_factory_contact', placeholder="e.g. 010-9999-8888")
        with fc3: production_time = st.text_input("⏱️ Production Time", key='reg_production_time', placeholder="e.g. 7-10 days")

        st.markdown("---")
        st.subheader("Product Images")
        if edit_mode_id: st.caption("Upload new images to replace existing ones.")
        
        img_col1, img_col2, img_col3, img_col4 = st.columns(4)
        
        def show_existing_image(key_name):
            path = st.session_state.get(key_name)
            if path and os.path.exists(path):
                st.image(path, caption="Current")

        with img_col1:
            if edit_mode_id: show_existing_image('reg_img_rep')
            img_rep = st.file_uploader("Representative", type=['png', 'jpg', 'jpeg'])
        with img_col2:
            if edit_mode_id: show_existing_image('reg_img_top')
            img_top = st.file_uploader("Top View", type=['png', 'jpg', 'jpeg'])
        with img_col3:
            if edit_mode_id: show_existing_image('reg_img_front')
            img_front = st.file_uploader("Front View", type=['png', 'jpg', 'jpeg'])
        with img_col4:
            if edit_mode_id: show_existing_image('reg_img_side')
            img_side = st.file_uploader("Side View", type=['png', 'jpg', 'jpeg'])

        st.markdown("---")

        st.markdown("---")
        
    elif product_type == "Dia/Stone":
        st.subheader("1. Diamond / Loose Stone Details")
        
        # Row 1: Basic Info
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            name = st.text_input("Product Name / Description", placeholder="e.g. 0.5ct GIA F SI1 Round", key="dia_name")
        with dc2:
            d_type = st.selectbox("Stone Type", ["Natural", "Synthetic (Lab)", "Treated", "Mono"], key="dia_type")
        with dc3:
             stock_qty = st.number_input("Stock Quantity", min_value=0, value=1, step=1, key="dia_stock")

        # Phase 15: Factory Info Inputs
        st.markdown("---")
        st.subheader("Factory Information (Optional)")
        fc1, fc2, fc3 = st.columns(3)
        with fc1: factory_name = st.text_input("🏭 Factory Name", key='reg_factory_name', placeholder="e.g. Gold Smith Co.")
        with fc2: factory_contact = st.text_input("📞 Factory Contact", key='reg_factory_contact', placeholder="e.g. 010-9999-8888")
        with fc3: production_time = st.text_input("⏱️ Production Time", key='reg_production_time', placeholder="e.g. 7-10 days")

        # Row 2: Cert & Shape
        dc4, dc5 = st.columns(2)
        with dc4:
            d_cert = st.text_input("Certificate (e.g. GIA, Wooshin)", value="GIA", key="dia_cert")
        with dc5:
            d_shape = st.selectbox("Shape", DIA_SHAPES, key="dia_shape")

        st.markdown("### 💎 4C Grading")
        gc1, gc2, gc3, gc4 = st.columns(4)
        with gc1: d_weight = st.number_input("Carat Weight", min_value=0.0, step=0.01, format="%.2f", key="dia_weight")
        with gc2: d_color = st.selectbox("Color", DIA_COLORS, index=2, key="dia_color") # Default F
        with gc3: d_clarity = st.selectbox("Clarity", DIA_CLARITY, index=4, key="dia_clarity") # Default VS1
        with gc4: d_cut = st.selectbox("Cut Grade", DIA_CUTS, key="dia_cut")

        st.markdown("### 🔬 Detailed Grading")
        zc1, zc2, zc3 = st.columns(3)
        with zc1: d_polish = st.selectbox("Polish", DIA_CUTS, key="dia_polish")
        with zc2: d_symmetry = st.selectbox("Symmetry", DIA_CUTS, key="dia_symmetry")
        with zc3: d_fluo = st.selectbox("Fluorescence", DIA_FLUORESCENCE, key="dia_fluo")
        
        st.markdown("---")
        st.markdown("### Images")
        img_col1, img_col2, img_col3, img_col4 = st.columns(4)
        with img_col1: img_rep = st.file_uploader("Certificate Image", type=['png', 'jpg', 'jpeg'], key="dia_img_rep")
        with img_col2: img_top = st.file_uploader("Stone View", type=['png', 'jpg', 'jpeg'], key="dia_img_top")
        img_front = None # Unused for loose stone usually
        img_side = None

        st.markdown("---")
        st.markdown("---")
        
    elif product_type == "ColorStone":
        st.subheader("1. Colored Stone Details")
        
        # Grid Layout Row 1: Type | Cert | Shape
        csc1, csc2, csc3 = st.columns(3)
        with csc1: cs_type = st.selectbox("Stone Type", CS_TYPES, key="cs_type")
        with csc2: cs_cert = st.text_input("Certificate", placeholder="e.g. GRS, GIA...", key="cs_cert")
        with csc3: cs_shape = st.selectbox("Shape", DIA_SHAPES, key="cs_shape") # Reusing DIA shapes usually fine
        
        # Grid Layout Row 2: Image | Name
        # For simplicity, we put Name first then Images below or side-by-side
        csc4, csc5 = st.columns([1, 2])
        with csc4: stock_qty = st.number_input("Stock Qty", min_value=1, value=1, key="cs_stock")
        with csc5: name = st.text_input("Product Name / Description", placeholder="e.g. 2.0ct Pigeon Blood Ruby", key="cs_name")
        
        # Phase 15: Factory Info Inputs
        st.markdown("---")
        st.subheader("Factory Information (Optional)")
        fc1, fc2, fc3 = st.columns(3)
        with fc1: factory_name = st.text_input("🏭 Factory Name", key='reg_factory_name', placeholder="e.g. Gold Smith Co.")
        with fc2: factory_contact = st.text_input("📞 Factory Contact", key='reg_factory_contact', placeholder="e.g. 010-9999-8888")
        with fc3: production_time = st.text_input("⏱️ Production Time", key='reg_production_time', placeholder="e.g. 7-10 days")

        # Grid Layout Row 3 (Specs): Weight | Color | Tone | Saturation | Clarity
        st.markdown("### 🌈 Grading")
        gc1, gc2, gc3, gc4, gc5 = st.columns(5)
        with gc1: cs_weight = st.number_input("Weight (ct)", min_value=0.0, step=0.01, format="%.2f", key="cs_weight")
        with gc2: cs_color = st.selectbox("Color", CS_COLORS, key="cs_color")
        with gc3: cs_tone = st.selectbox("Tone", CS_TONES, key="cs_tone")
        with gc4: cs_sat = st.selectbox("Saturation", CS_SATURATIONS, key="cs_sat")
        with gc5: cs_clarity = st.selectbox("Clarity", CS_CLARITY, key="cs_clarity")
        
        # Origin & Comments
        oc1, oc2 = st.columns([1, 2])
        with oc1: cs_origin = st.text_input("Origin (Optional)", placeholder="e.g. Burma, Ceylon", key="cs_origin")
        with oc2: cs_comment = st.text_area("Remarks / Comment", height=68, placeholder="Enter detailed remarks...", key="cs_comment")
        
        st.markdown("---")
        st.markdown("### Images")
        img_col1, img_col2, img_col3, img_col4 = st.columns(4)
        with img_col1: img_rep = st.file_uploader("Main Image", type=['png', 'jpg', 'jpeg'], key="cs_img_rep")
        with img_col2: img_top = st.file_uploader("Certificate", type=['png', 'jpg', 'jpeg'], key="cs_img_top")
        img_front = None
        img_side = None
        
        st.markdown("---")
        st.markdown("---")

    elif product_type == "Watch":
        st.subheader("1. Luxury Watch Details")
        
        # Row 1: Brand (SubCat) | Model | Year | Size
        wc1, wc2, wc3, wc4 = st.columns(4)
        with wc1: 
            # Brand is derived from SubCategory
            st.text_input("Brand", value=sub_category, disabled=True, key="w_brand_display")
        with wc2: w_model = st.text_input("Model Number", placeholder="e.g. 116500LN", key="w_model")
        with wc3: w_year = st.text_input("Year", placeholder="e.g. 2023", key="w_year")
        with wc4: w_size = st.text_input("Size", placeholder="e.g. 40mm", key="w_size")

        # Phase 15: Factory Info Inputs
        st.markdown("---")
        st.subheader("Factory Information (Optional)")
        fc1, fc2, fc3 = st.columns(3)
        with fc1: factory_name = st.text_input("🏭 Factory Name", key='reg_factory_name', placeholder="e.g. Gold Smith Co.")
        with fc2: factory_contact = st.text_input("📞 Factory Contact", key='reg_factory_contact', placeholder="e.g. 010-9999-8888")
        with fc3: production_time = st.text_input("⏱️ Production Time", key='reg_production_time', placeholder="e.g. 7-10 days")

        # Row 2: Material | Color | Movement | Band
        wc5, wc6, wc7, wc8 = st.columns(4)
        with wc5: w_material = st.selectbox("Material", WATCH_MATERIALS, key="w_material")
        with wc6: w_color = st.selectbox("Dial Color", WATCH_COLORS, key="w_color")
        with wc7: w_movement = st.selectbox("Movement", WATCH_MOVEMENTS, key="w_movement")
        with wc8: w_band = st.selectbox("Band Type", WATCH_BANDS, key="w_band")
        
        # Row 3: Cert | Case | Status
        wc9, wc10, wc11 = st.columns(3)
        with wc9: w_cert = st.selectbox("Certificate", YN_OPTIONS, key="w_cert")
        with wc10: w_case = st.selectbox("Case", YN_OPTIONS, key="w_case")
        with wc11: w_status = st.selectbox("Condition", WATCH_STATUS, key="w_status")
        
        # Row 4: Name | Image
        wc12, wc13 = st.columns([2, 1])
        with wc12: 
            name = st.text_input("Product Name / Description", placeholder="e.g. Rolex Daytona Panda 116500LN", key="w_name")
            stock_qty = st.number_input("Stock Qty", min_value=1, value=1, key="w_stock")

        with wc13:
            img_rep = st.file_uploader("Main Image", type=['png', 'jpg', 'jpeg'], key="w_img_rep")
        
        img_top = None
        img_front = None
        img_side = None

        st.markdown("---")

        


        st.markdown("---")

    elif product_type == "Etc":
        st.subheader("1. General Item Details")
        
        # Row 1: Name | SubCat
        ec1, ec2 = st.columns([2, 1])
        with ec1: name = st.text_input("Product Name", placeholder="e.g. Leather Strap, Watch Box", key="e_name")
        with ec2: 
             # Sub Category is handled at top, just display stock
             stock_qty = st.number_input("Stock Qty", min_value=1, value=1, key="e_stock")
        
        # Phase 17: Etc Material/Size
        ec3, ec4 = st.columns(2)
        with ec3: e_material = st.text_input("Material", key="e_material", placeholder="e.g. Leather, Wood")
        with ec4: e_size = st.text_input("Size", key="e_size", placeholder="e.g. 20mm, Large")

        # Phase 15: Factory Info Inputs
        st.markdown("---")
        st.subheader("Factory Information (Optional)")
        fc1, fc2, fc3 = st.columns(3)
        with fc1: factory_name = st.text_input("🏭 Factory Name", key='reg_factory_name', placeholder="e.g. Gold Smith Co.")
        with fc2: factory_contact = st.text_input("📞 Factory Contact", key='reg_factory_contact', placeholder="e.g. 010-9999-8888")
        with fc3: production_time = st.text_input("⏱️ Production Time", key='reg_production_time', placeholder="e.g. 7-10 days")

        # Row 2: Images
        st.markdown("### Images")
        img_col1, img_col2, img_col3, img_col4 = st.columns(4)
        with img_col1: img_rep = st.file_uploader("Main Image", type=['png', 'jpg', 'jpeg'], key="e_img_rep")
        with img_col2: img_top = st.file_uploader("Top View", type=['png', 'jpg', 'jpeg'], key="e_img_top")
        with img_col3: img_front = st.file_uploader("Front View", type=['png', 'jpg', 'jpeg'], key="e_img_front")
        with img_col4: img_side = st.file_uploader("Side View", type=['png', 'jpg', 'jpeg'], key="e_img_side")
        
        st.markdown("---")
        st.markdown("---")
        


        # Row 4: Remarks
        e_comments = st.text_area("Remarks", height=100, key="e_comments")
        st.markdown("---")

    # --- Global Materials Section (Unified) ---
    gold_cost, stone_cost = render_gold_stone_inputs()
    # Refresh vars
    gold_weight = st.session_state.get('reg_gold_weight', 0.0)
    gold_price_applied = st.session_state.get('reg_gold_price_applied', 0)
    st.markdown("---")
    
    # --- Phase 20: Unified Pricing Section (For All Categories) ---
    st.markdown("### 💰 Pricing Factors")
    
    # Inputs
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1: labor_cost = st.number_input("Labor Cost / Base Cost (공임/원가)", min_value=0, step=5000, key="reg_labor")
    with p_col2: margin_pct = st.number_input("Margin (%)", min_value=0.0, value=10.0, key="reg_margin")
    with p_col3: discount_pct = st.number_input("Discount (%)", min_value=0.0, value=0.0, key="reg_discount")
        
    p_col4, p_col5, p_col6 = st.columns(3)
    with p_col4: vat_pct = st.number_input("VAT (%)", min_value=0.0, value=10.0, key="reg_vat")
    with p_col5: fee_pct = st.number_input("Card Fee (%)", min_value=0.0, value=3.0, key="reg_fee")
    with p_col6: tax_pct = st.number_input("Special Tax (%)", min_value=0.0, value=0.0, key="reg_tax_special") # Added for Watch/Etc compat

    # Calculations (Unified Logic)
    # 1. Total Base Cost (Materials + Labor/Base)
    product_cost = gold_cost + stone_cost + labor_cost
    
    # 2. Selling Price (Base + Margin)
    selling_price = product_cost * (1 + margin_pct/100)
    expected_profit = selling_price - product_cost
    
    # 3. Final Price (Selling + VAT + Fees + Taxes)
    vat_amount = selling_price * (vat_pct / 100)
    fee_amount = selling_price * (fee_pct / 100)
    tax_amount = selling_price * (tax_pct / 100)
    
    final_price = selling_price + vat_amount + fee_amount + tax_amount
    
    # Preview
    st.markdown("#### Preview")
    calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
    calc_col1.metric("Total Cost", format_currency(product_cost), help="Gold + Stones + Labor/Base")
    calc_col2.metric("Margin Profit", format_currency(expected_profit), delta_color="normal")
    calc_col3.metric("Selling Price", format_currency(selling_price))
    calc_col4.metric("Final Price", format_currency(final_price), delta_color="normal")
    
    st.markdown("---")

    submit_btn = st.button(submit_label, key="save_update_product_btn", type="primary")
    
    if submit_btn:
        if not name:
            st.error("Please enter a product name.")
        else:
            try:
                session = get_db_session()
                target_product = None
                if edit_mode_id:
                    target_product = session.query(Product).filter(Product.id == edit_mode_id).first()
                else:
                    # Generic Product Creation
                    target_product = Product(user_id=st.session_state.user_id, category=product_type)
                    
                    # Generate Product Code: {shop_code}-{Category}-{YYMMDD}-{Seq}
                    shop_code = st.session_state.shop_code
                    cat_map = {"Jewelry": "J", "Gold": "G", "Watch": "W", "Dia/Stone": "D", "ColorStone": "C", "Etc": "E"}
                    cat_char = cat_map.get(product_type, "X")
                    date_str = datetime.now().strftime("%y%m%d")
                    prefix = f"{shop_code}-{cat_char}{date_str}-"
                    
                    # Count existing products for this shop/category today
                    # We look for product_code LIKE prefix%
                    count = session.query(Product).filter(Product.product_code.like(f"{prefix}%")).count()
                    seq = count + 1
                    target_product.product_code = f"{prefix}{seq:03d}"
                    
                    session.add(target_product)
                
                # Common Fields
                target_product.category = product_type
                target_product.sub_category = sub_category
                target_product.name = name
                target_product.total_price = final_price
                target_product.stock_quantity = stock_qty 

                # Phase 15: Factory Info
                target_product.factory_name = factory_name
                target_product.factory_contact = factory_contact
                target_product.factory_contact = factory_contact
                target_product.production_time = production_time
                
                # Phase 18: Save Pricing to Product
                target_product.labor_cost = labor_cost
                target_product.margin_percentage = margin_pct
                target_product.tax_percentage = vat_pct
                target_product.card_fee_percentage = fee_pct

                # Image Saving
                if img_rep: target_product.image_rep = save_uploaded_file(img_rep, "rep")
                if img_top: target_product.image_top = save_uploaded_file(img_top, "top")
                if img_front: target_product.image_front = save_uploaded_file(img_front, "front")
                if img_side: target_product.image_side = save_uploaded_file(img_side, "side")
                
                # Type Specific Logic
                
                # Retrieve Gold/Stone data from session just in case it was updated in helper
                gold_weight = st.session_state.get('reg_gold_weight', 0.0)
                gold_purity = st.session_state.get('reg_gold_purity', '18K')
                gold_price_applied = st.session_state.get('reg_gold_price_applied', 0)
                
                # Check for stones
                has_stones_check = False
                for s in st.session_state.main_stones: 
                    if s['name']: has_stones_check = True
                for s in st.session_state.sub_stones: 
                    if s['name']: has_stones_check = True

                # Phase 19: Universal Gold/Jewelry Saving
                # If category is Jewelry/Gold OR if we have material info (Gold > 0 or Stones exist)
                is_jewelry_cat = product_type in ["Jewelry", "Gold"]
                has_material_data = (gold_weight > 0) or has_stones_check
                
                if is_jewelry_cat or has_material_data:
                    # Create/Update ProductJewelry
                     if edit_mode_id and target_product.jewelry_details:
                        jd = target_product.jewelry_details
                     else:
                        jd = ProductJewelry(product=target_product)
                        # Only add if not editing (edit mode attached via backref usually, but safe to check)
                        if not edit_mode_id or not target_product.jewelry_details: 
                             session.add(jd)
                        
                     jd.gold_weight = gold_weight
                     jd.gold_purity = gold_purity
                     jd.gold_price_applied = gold_price_applied
                     # Pricing factors primarily on Product now (Phase 18), but keep legacy sync or 0
                     jd.labor_cost = labor_cost
                     jd.margin_pct = margin_pct
                     jd.discount_pct = discount_pct
                     jd.vat_pct = vat_pct
                     jd.fee_pct = fee_pct
                     
                     # Recalc Cost/Price if it's an "Etc/Watch" item with added materials?
                     # If it's Watch, the price logic was specific.
                     # But if user adds Gold, the total cost increases.
                     # Let's update product_cost on JD to reflect Materials + Labor
                     # Note: labor_cost is now on Product (Phase 18) but we have 'reg_labor' here too.
                     
                     jd.product_cost = product_cost # This variable 'product_cost' comes from Jewelry calc block...
                     # Wait, 'product_cost' variable was calculated in the Jewelry block (Line 1201).
                     # If we are in Watch/Etc block, 'product_cost' variable is NOT defined or is stale!
                     
                     # Fix: Recalculate cost here universal
                     g_c = gold_weight * gold_price_applied
                     s_c = 0
                     for s in st.session_state.main_stones: s_c += (s['qty'] * s['price'])
                     for s in st.session_state.sub_stones: s_c += (s['qty'] * s['price'])
                     
                     jd.product_cost = g_c + s_c + labor_cost
                     jd.calc_selling_price = selling_price
                     jd.final_price = final_price

                # 1. Main Table Updates (Legacy Block wrapper removed, logic merged above)
                # But we still need to handle specific logic if it was strictly Jewelry?
                # The above block handles JD creation.
                
                if product_type in ["Jewelry", "Gold"]:
                     # Any Jewelry specific strictly things?
                     # Already covered above.
                     pass 

                    
                # Universal Material Saving (Gold & Stones for ALL tables if input exists)
                # Check if we have active gold/stone inputs even if not "Jewelry" category
                # NOTE: For Watch/Etc, the UI might not show these inputs, so values might be default 0/empty.
                # However, if user ADDS inputs to those sections later, we want this to work. 
                # Currently, UI only shows materials for Jewelry/Gold. 
                # But the user REQUESTED this fix "Regardless of category".
                
                # Check if we should save/update JewelryDetails for "Material Info"
                # Only if gold_weight > 0 implies there's material info to save?
                # The user said: "if gold_weight > 0 or stones are added, save them".
                
                has_gold = False
                has_stones = False
                for ms in st.session_state.main_stones: 
                    if ms['name']: has_stones = True
                for ss in st.session_state.sub_stones: 
                    if ss['name']: has_stones = True
                
                if 'reg_gold_weight' in st.session_state and st.session_state.reg_gold_weight > 0: has_gold = True
                if 'gold_weight' in locals() and gold_weight > 0: has_gold = True # use local var
                
                # If we are NOT in Jewelry/Gold category, but have material data, we might need a JewelryDetail record or similar?
                # Actually, if the category is Watch, we don't usually create JewelryDetail. 
                # BUT the user wants "Universal Material Saving". 
                # Let's assume if it's NOT Jewelry/Gold, we attach stones to ProductStone, and maybe ignore gold unless needed.
                # BUT the prompt says "Save GoldDetail...". 
                # If I attach ProductJewelry to a Watch, it works (One-to-One).
                
                # Universal Stone Saving (Moved OUT of if/elif)
                if edit_mode_id:
                     session.query(ProductStone).filter(ProductStone.product_id == target_product.id).delete()
                
                for ms in st.session_state.main_stones:
                    if ms['name']: session.add(ProductStone(product=target_product, stone_type="Main", name=ms['name'], quantity=ms['qty'], unit_price=ms['price']))
                for ss in st.session_state.sub_stones:
                    if ss['name']: session.add(ProductStone(product=target_product, stone_type="Sub", name=ss['name'], quantity=ss['qty'], unit_price=ss['price']))

                # Continue Type Specific...
                if product_type == "Dia/Stone":
                    if edit_mode_id and target_product.diamond_details:
                        dd = target_product.diamond_details
                    else:
                        dd = ProductDiamond(product=target_product)
                        if not edit_mode_id: session.add(dd)
                    
                    dd.stone_type = d_type
                    dd.certificate = d_cert
                    dd.shape = d_shape
                    dd.weight = d_weight
                    dd.color = d_color
                    dd.clarity = d_clarity
                    dd.cut = d_cut
                    dd.polish = d_polish
                    dd.symmetry = d_symmetry
                    dd.fluorescence = d_fluo
                    
                    dd.purchase_cost = d_cost
                    dd.margin_pct = d_margin
                    dd.vat_pct = d_vat
                    dd.final_price = final_price_dia
                    
                elif product_type == "ColorStone":
                    if edit_mode_id and target_product.color_stone_details:
                        cs = target_product.color_stone_details
                    else:
                        cs = ProductColorStone(product=target_product)
                        if not edit_mode_id: session.add(cs)
                        
                    cs.stone_type = cs_type
                    cs.cert_agency = cs_cert
                    cs.shape = cs_shape
                    cs.weight = cs_weight
                    cs.color = cs_color
                    cs.tone = cs_tone
                    cs.saturation = cs_sat
                    cs.clarity = cs_clarity
                    cs.origin = cs_origin
                    cs.comment = cs_comment
                    
                    cs.purchase_cost = cs_cost
                    cs.margin_pct = cs_margin
                    cs.vat_pct = cs_vat
                    cs.tax_rate = cs_tax
                    cs.final_price = final_price_cs

                elif product_type == "Watch":
                    if edit_mode_id and target_product.watch_details:
                        wd = target_product.watch_details
                    else:
                        wd = ProductWatch(product=target_product)
                        if not edit_mode_id: session.add(wd)
                    
                    wd.brand = sub_category # SubCat is Brand
                    wd.model_number = w_model
                    wd.year = w_year
                    wd.size = w_size
                    wd.material = w_material
                    wd.color = w_color
                    wd.movement = w_movement
                    wd.band = w_band
                    wd.has_cert = w_cert
                    wd.has_case = w_case
                    wd.status = w_status
                    
                    wd.purchase_cost = w_cost
                    wd.margin_pct = w_margin
                    wd.vat_pct = w_vat
                    wd.tax_pct = w_tax
                    wd.final_price = final_price_w

                elif product_type == "Etc":
                    if not target_product.etc_details:
                        target_product.etc_details = ProductEtc(product=target_product)
                        if not edit_mode_id: session.add(target_product.etc_details)
                    
                    target_product.etc_details.comments = e_comments
                    target_product.etc_details.purchase_cost = e_cost
                    target_product.etc_details.margin_pct = e_margin
                    target_product.etc_details.vat_pct = e_vat
                    target_product.etc_details.tax_pct = e_tax
                    target_product.etc_details.final_price = final_price_e
                    # Phase 17: Save Material/Size
                    target_product.etc_details.material = e_material
                    target_product.etc_details.size = e_size
                
                # [긴급 추가] 카테고리 불문하고 금 중량 강제 저장 (ETC/시계 데이터 증발 방지)
                # 1. 입력된 금 중량을 확인합니다.
                current_gold_weight = st.session_state.get('reg_gold_weight', 0.0)
                
                # 2. 금 중량이 0보다 크면 무조건 저장을 시도합니다.
                if current_gold_weight > 0:
                    # 만약 저장할 '주얼리 정보(ProductJewelry)' 방이 없으면 새로 만듭니다.
                    if target_product.jewelry_details is None:
                        target_product.jewelry_details = ProductJewelry(product_id=target_product.id)
                        session.add(target_product.jewelry_details)
                    
                    # 3. 데이터를 강제로 집어넣습니다.
                    target_product.jewelry_details.gold_weight = current_gold_weight
                    target_product.jewelry_details.gold_purity = st.session_state.get('reg_gold_purity', '18K')
                    target_product.jewelry_details.gold_price_applied = st.session_state.get('reg_gold_price_applied', 0)
                    
                session.commit()
                st.toast(f"Product '{name}' saved!", icon="🎉")
                
                if edit_mode_id:
                    del st.session_state['edit_mode_id']
                    del st.session_state['data_loaded']
                    keys_to_clear = ['reg_name', 'reg_stock', 'reg_category', 'reg_subcategory', 
                                     'reg_factory_name', 'reg_factory_contact', 'reg_production_time', # Phase 15
                                     'reg_gold_weight', 'reg_gold_price_applied', 'reg_labor', 'reg_margin', 'reg_discount', 'reg_vat', 'reg_fee', 'reg_img_rep', 'reg_img_top', 'reg_img_front', 'reg_img_side', 'dia_name', 'dia_type', 'dia_cert', 'dia_shape', 'dia_weight', 'dia_color', 'dia_clarity', 'dia_cut', 'dia_polish', 'dia_symmetry', 'dia_fluo', 'dia_cost', 'dia_margin', 'dia_vat', 'cs_name', 'cs_type', 'cs_cert', 'cs_shape', 'cs_weight', 'cs_color', 'cs_tone', 'cs_sat', 'cs_clarity', 'cs_origin', 'cs_comment', 'cs_cost', 'cs_margin', 'cs_vat', 'cs_tax', 'w_model', 'w_year', 'w_size', 'w_material', 'w_color', 'w_movement', 'w_band', 'w_cert', 'w_case', 'w_status', 'w_name', 'w_stock', 'w_cost', 'w_margin', 'w_vat', 'w_tax', 'e_name', 'e_stock', 'e_cost', 'e_margin', 'e_vat', 'e_tax', 'e_comments', 'e_material', 'e_size']
                    for k in keys_to_clear:
                        if k in st.session_state: del st.session_state[k]
                    st.button("Return to Gallery", on_click=lambda: st.session_state.update({'nav_selection': 'Gallery'}))
                    
                session.close()

            except Exception as e:
                session.rollback()
                st.error(f"Error saving product: {e}")
            finally:
                if 'session' in locals():
                    session.close()

    if edit_mode_id:
        if st.button("Cancel Edit"):
            del st.session_state['edit_mode_id']
            if 'data_loaded' in st.session_state: del st.session_state['data_loaded']
            keys_to_clear = ['reg_name', 'reg_stock', 'reg_category', 'reg_subcategory', 'reg_gold_weight', 'reg_labor', 'reg_margin', 'reg_discount', 'reg_vat', 'reg_fee']
            for k in keys_to_clear:
                 if k in st.session_state: del st.session_state[k]
            st.rerun()

def show_settings_page():
    st.header("⚙️ Settings")
    st.markdown("### Category Management")
    
    session = get_db_session()
    
    col1, col2 = st.columns(2)
    with col1:
        main_cat_sel = st.selectbox("Select Main Category", ["Jewelry", "Gold", "Watch", "Dia/Stone", "ColorStone", "Etc"])
        new_sub = st.text_input("New Sub Category Name")
        if st.button("➕ Add Category", type="primary"):
            if new_sub:
                exists = session.query(CategorySetting).filter_by(main_category=main_cat_sel, sub_category_name=new_sub).first()
                if not exists:
                    session.add(CategorySetting(main_category=main_cat_sel, sub_category_name=new_sub))
                    session.commit()
                    st.success(f"Added {new_sub} to {main_cat_sel}")
                    st.rerun()
                else:
                    st.warning("Category already exists.")
    
    with col2:
        st.caption(f"Current Sub-Categories for {main_cat_sel}")
        current_subs = session.query(CategorySetting).filter_by(main_category=main_cat_sel).all()
        if current_subs:
            for sub in current_subs:
                c1, c2 = st.columns([4, 1])
                c1.write(f"• {sub.sub_category_name}")
                if c2.button("🗑️", key=f"del_cat_{sub.id}"):
                    session.delete(sub)
                    session.commit()
                    st.rerun()
    with col2:
        st.caption(f"Current Sub-Categories for {main_cat_sel}")
        current_subs = session.query(CategorySetting).filter_by(main_category=main_cat_sel).all()
        if current_subs:
            for sub in current_subs:
                c1, c2 = st.columns([4, 1])
                c1.write(f"• {sub.sub_category_name}")
                if c2.button("🗑️", key=f"del_cat_{sub.id}_unique"):
                    session.delete(sub)
                    session.commit()
                    st.rerun()
        else:
            st.info("No sub-categories defined.")

    session.close()

    st.markdown("---")
    
    # Image Normalization (SuperUser)
    if st.session_state.get('user_role') == 'SuperUser':
        st.markdown("### 🖼️ Image Maintenance")
        if st.button("Example: Process All Images to Square", key="btn_normalize_imgs"):
            processed_count = normalize_existing_images()
            st.success(f"Processed {processed_count} images to 500x500 square format!")
            
    st.markdown("### 🔐 Security Settings")
    
    with st.form("change_password_form"):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Password", type="primary"):
            if new_pw != confirm_pw:
                st.error("New passwords do not match.")
            elif not new_pw:
                st.error("Password cannot be empty.")
            else:
                session = get_db_session()
                # Use current user session ID
                user = session.query(User).filter_by(id=st.session_state.user_id).first()
                if user:
                    # Check current hash
                    if user.password_hash == hash_password(current_pw):
                        user.password_hash = hash_password(new_pw)
                        session.commit()
                        st.success("User password updated! Please re-login.")
                    else:
                        st.error("Incorrect current password.")
                session.close()

def show_sales_page():
    st.header("🛍️ POS / Sales")
    session = get_db_session()
    
    st.subheader("1. Add Items")
    search_term = st.text_input("Search Product", placeholder="Name or Category...")
    
    query = session.query(Product).filter(Product.stock_quantity > 0)
    
    # Isolation Logic
    if st.session_state.user_role != 'SuperUser':
        query = query.filter(Product.user_id == st.session_state.user_id)
    if search_term:
        query = query.filter(Product.name.ilike(f"%{search_term}%"))
    
    available_products = query.limit(10).all()
    
    if available_products:
        sc1, sc2, sc3 = st.columns(3)
        for i, p in enumerate(available_products):
            with [sc1, sc2, sc3][i % 3]:
                with st.container(border=True):
                    st.write(f"**{p.name}**")
                    if p.jewelry_details: price = p.jewelry_details.final_price
                    else: price = p.total_price
                    st.caption(f"{format_currency(price)}")
                    st.caption(f"Stock: {p.stock_quantity}")
                    if st.button("Add to Cart", key=f"add_cart_{p.id}"): add_to_cart(p)
    else:
        st.warning("No products found in stock.")

    st.markdown("---")
    st.subheader("2. Current Order")
    
    if st.session_state.cart:
        total_order_amount = 0
        h1, h2, h3, h4, h5 = st.columns([3, 2, 1, 2, 1])
        h1.markdown("**Product**")
        h2.markdown("**Price**")
        h3.markdown("**Qty**")
        h4.markdown("**Subtotal**")
        h5.markdown("**Action**")
        
        for item in st.session_state.cart:
            subtotal = item['price'] * item['qty']
            total_order_amount += subtotal
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 2, 1])
            c1.write(item['name'])
            c2.write(format_currency(item['price']))
            c3.write(item['qty'])
            c4.write(format_currency(subtotal))
            if c5.button("❌", key=f"del_cart_{item['product_id']}"):
                remove_from_cart(item['product_id'])
                st.rerun()
        
        st.markdown(f"### Total: :blue[{format_currency(total_order_amount)}]")
        
        with st.form("checkout_form"):
            customer_name = st.text_input("Customer Name", placeholder="Optional")
            submitted = st.form_submit_button("✅ Complete Sale", type="primary")
            if submitted:
                try:
                    new_order = Order(customer_name=customer_name, total_amount=total_order_amount)
                    session.add(new_order)
                    session.flush() 
                    
                    for item in st.session_state.cart:
                        db_product = session.query(Product).filter(Product.id == item['product_id']).first()
                        if db_product.stock_quantity < item['qty']:
                            raise ValueError(f"Not enough stock for {db_product.name}")
                        db_product.stock_quantity -= item['qty']
                        session.add(OrderItem(order_id=new_order.id, product_id=db_product.id, product_name=db_product.name, quantity=item['qty'], unit_price=item['price'], subtotal=item['price'] * item['qty']))
                    
                    session.commit()
                    clear_cart()
                    st.toast("Order confirmed!", icon="🚀")
                    st.success(f"Sale completed! Order ID: #{new_order.id}")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Checkout Failed: {e}")
    else:
        st.info("Cart is empty.")
    session.close()

def show_gallery_page():
    st.header("🛒 Product Gallery")
    
    # 1. Sidebar Settings (Updated for 'Don' and removed Category Selectbox)
    st.sidebar.markdown("### ⚙️ Global Settings")
    
    # Auto-fetch Gold Price
    fetched_price = fetch_gold_price()
    
    # 2026-02-05 Upgrade: Force update the session state to reflect the live price
    # The user specifically requested to overwrite the manual input if a live price is available.
    if fetched_price:
        st.session_state['gold_price_don'] = fetched_price

    # Gold Price Input (Don System)
    # We use session_state for persistence
    gold_price_don = st.sidebar.number_input(
        "Today's Gold Price (per 1 Don / 3.75g)", 
        min_value=0, 
        value=st.session_state.get('gold_price_don', 450000),
        step=1000, 
        format="%d",
        key="gold_price_don"
    )
    
    if fetched_price:
        st.sidebar.caption(f"✅ Live Price Applied: {format_currency(fetched_price)}")
    else:
        st.sidebar.error("⚠️ Failed to fetch live price")
    
    # Calculate Per Gram (Floor to nearest 100)
    gold_price_per_g = math.floor((gold_price_don / 3.75) / 100) * 100
    st.sidebar.caption(f"Applied: {format_currency(gold_price_per_g)} / g")
    
    show_admin_details = st.sidebar.checkbox("Show Admin Details (Cost & Margin)", value=False)
    
    # 2. Fetch All Products
    session = get_db_session()
    
    query = session.query(Product)
    
    # Isolation Logic
    if st.session_state.user_role != 'SuperUser':
        query = query.filter(Product.user_id == st.session_state.user_id)
        
    all_products = query.order_by(Product.created_at.desc()).all()
    
    if not all_products:
        st.info("No products found.")
        session.close()
        return

    # --- Phase 14: Advanced Gallery Features ---
    
    # 3. Search & Filter
    search_term = st.text_input("🔍 Search Product", placeholder="Name, Brand, Code, or Serial No...")
    
    filtered_products = all_products
    if search_term:
        term = search_term.lower()
        filtered_products = [
            p for p in all_products 
            if term in p.name.lower() 
            or (p.product_code and term in p.product_code.lower())
            or (p.category and term in p.category.lower())
            or (p.sub_category and term in p.sub_category.lower())
        ]
        
    # 4. Total Asset Dashboard
    total_asset_value = 0
    cat_counts = {
        "ALL": len(filtered_products),
        "Jewelry": 0, "Gold": 0, "Watch": 0, "Dia/Stone": 0, "ColorStone": 0, "Etc": 0
    }
    
    for p in filtered_products:
        # Calculate Value (Simplified Fix)
        # Use simple attribute total_price which should be populated on save
        price = p.total_price if p.total_price else 0
        total_asset_value += price
        
        # Count
        if p.category in cat_counts:
            cat_counts[p.category] += 1
            
    # Display Dashboard
    today_str = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="margin:0; color: #31333F;">📅 As of {today_str} | Total Inventory Value</h4>
        <h2 style="margin:0; color: #0068C9;">{format_currency(total_asset_value)}</h2>
    </div>
    """, unsafe_allow_html=True)

    # 5. Dynamic Tabs
    tab_names = ["ALL", "Jewelry", "Gold", "Watch", "Diamond", "ColorStone", "Etc"]
    
    # Generate Labels
    tab_labels = [f"{t} ({cat_counts.get(t if t!='Diamond' else 'Dia/Stone', 0)})" for t in tab_names]
    
    tabs = st.tabs(tab_labels)
    
    for i, tab in enumerate(tabs):
        with tab:
            current_cat = tab_names[i]
            
            # Filter Products
            if current_cat == "ALL":
                products_to_show = filtered_products
            else:
                # Handle Display Name vs DB Name
                db_cat = "Dia/Stone" if current_cat == "Diamond" else current_cat
                products_to_show = [p for p in filtered_products if p.category == db_cat]
                
            if not products_to_show:
                st.info(f"No products in {current_cat}.")
                continue
                
            # Render Grid
            cols = st.columns(5)
            for idx, product in enumerate(products_to_show):
                with cols[idx % 5]:
                    with st.container(border=True):
                        # Stock Badge
                        if product.stock_quantity > 0:
                            st.markdown(f":green[In Stock: {product.stock_quantity}]")
                        else:
                            st.markdown(":red[Out of Stock]")
                        
                        # Image
                        if product.image_rep and os.path.exists(product.image_rep):
                            st.image(product.image_rep, use_container_width=True)
                        else:
                            st.empty() 
                        
                        # Compact Title
                        display_name = (product.name[:18] + '..') if len(product.name) > 20 else product.name
                        st.markdown(f"**{display_name}**", help=product.name)
                        
                        # Display Product Code
                        if product.product_code:
                            st.caption(f"ID: {product.product_code}")
                            
                        # st.caption(f"{product.category} / {product.sub_category if product.sub_category else '-'}")
                        
                        # Price Calculation using dynamic gold_price_per_g
                        final_price_display = 0
                        current_product_cost = 0
                        margin_pct = 0
                        
                        if product.jewelry_details:
                            jd = product.jewelry_details
                            current_gold_cost = jd.gold_weight * gold_price_per_g
                            current_stone_cost = sum(s.quantity * s.unit_price for s in product.stones) if product.stones else 0
                            current_product_cost = current_gold_cost + current_stone_cost + jd.labor_cost
                            current_selling_price = current_product_cost * (1 + jd.margin_pct / 100)
                            vat_amt = current_selling_price * (jd.vat_pct / 100)
                            fee_amt = current_selling_price * (jd.fee_pct / 100)
                            final_price_display = current_selling_price + vat_amt + fee_amt
                            
                            st.markdown(f"**{format_currency(final_price_display)}**")
                            margin_pct = jd.margin_pct
                        else:
                            final_price_display = product.total_price
                            st.markdown(f"**{format_currency(final_price_display)}**")
                            
                        if show_admin_details and product.jewelry_details:
                            st.markdown("---")
                            st.caption("🔒 Admin Details")
                            st.text(f"Cost: {format_currency(current_product_cost)}")
                            st.text(f"Margin: {margin_pct}%")

                        # Actions
                        ac1, ac2, ac3 = st.columns(3)
                        with ac1:
                            if st.button("👁️", key=f"view_{current_cat}_{product.id}"): view_product_details(product.id, gold_price_per_g)
                        with ac2:
                            st.button("✏️", key=f"edit_{current_cat}_{product.id}", on_click=go_to_edit, args=(product.id,))
                        with ac3:
                            if st.button("🗑️", key=f"del_{current_cat}_{product.id}"):
                                try:
                                     session.delete(product)
                                     session.commit()
                                     st.toast("Deleted!", icon="🗑️")
                                     time.sleep(1)
                                     st.rerun()
                                except Exception as e: st.error(f"Error: {e}")
    session.close()

@st.dialog("Product Details")
def view_product_details(product_id, current_gold_price):
    session = get_db_session()
    product = session.query(Product).filter(Product.id == product_id).first()
    
    # 닫기 버튼 스타일
    st.markdown("""<style>div[data-testid="stDialog"] div[data-testid="column"]:nth-of-type(2) button {color: red !important; border-color: red !important;}</style>""", unsafe_allow_html=True)
    
    if product:
        # [헤더]
        st.header(product.name)
        st.caption(f"Category: {product.category} > {product.sub_category} | Stock: {product.stock_quantity}")
        st.markdown("---")

        # [이미지]
        if product.image_rep: st.image(product.image_rep, caption="Representative")
        imgs = [x for x in [product.image_top, product.image_front, product.image_side] if x and os.path.exists(x)]
        if imgs:
            st.markdown("##### Additional Views")
            ic1, ic2, ic3 = st.columns(3)
            for i, img_path in enumerate(imgs):
                with [ic1, ic2, ic3][i]: st.image(img_path)
        
        st.markdown("---")

        # 1. [스펙 표시] 카테고리별 고유 정보 (가격 계산 로직 제거됨)
        if product.watch_details:
             wd = product.watch_details
             st.markdown("### ⌚ Watch Specs")
             wc1, wc2 = st.columns(2)
             wc1.markdown(f"**Model:** {wd.model_number}")
             wc2.markdown(f"**Brand:** {product.sub_category}")
             st.markdown(f"**Material:** {wd.material} | **Dial:** {wd.color}")
             st.caption(f"Status: {wd.status} | Year: {wd.year}")

        elif product.diamond_details:
             dd = product.diamond_details
             st.markdown("### 💎 Diamond Specs")
             st.markdown(f"**{dd.weight}ct / {dd.color} / {dd.clarity} / {dd.cut}**")
             st.markdown(f"**Cert:** {dd.certificate} ({dd.stone_type})")

        elif product.color_stone_details:
             cs = product.color_stone_details
             st.markdown("### 🌈 Stone Specs")
             st.markdown(f"**{cs.stone_type}** ({cs.weight}ct) - {cs.color}")
             st.caption(f"Origin: {cs.origin}")

        elif product.etc_details:
             ed = product.etc_details
             st.markdown("### 📦 Item Specs")
             st.markdown(f"**Material:** {ed.material or '-'} | **Size:** {ed.size or '-'}")
             st.markdown(f"**Description:** {ed.comments}")

        # 2. [통합 재료 정보] 주얼리 장부(ProductJewelry) 직접 조회
        saved_gold_view = session.query(ProductJewelry).filter(ProductJewelry.product_id == product.id).first()
        
        has_materials = saved_gold_view or product.stones
        
        if has_materials:
            st.divider()
            st.markdown("### 🏗️ Materials")
            if saved_gold_view:
                 st.markdown(f"**🥇 Gold:** {saved_gold_view.gold_purity} | **{saved_gold_view.gold_weight}g**")
            
            if product.stones:
                 st.markdown("**💎 Stones:**")
                 for s in product.stones:
                     st.write(f"- {s.stone_type}: {s.name} ({s.quantity} pcs)")

        # 3. [최종 가격] DB에 저장된 진짜 가격(total_price)을 그대로 표시
        st.divider()
        st.markdown(f"### 💰 Final Price: {format_currency(product.total_price)}")
        
        # (관리자용) 원가 공개
        if product.labor_cost > 0 or product.margin_percentage > 0:
            with st.expander("🔒 Cost Breakdown (Admin Only)"):
                st.write(f"Labor/Base Cost: {format_currency(product.labor_cost)}")
                st.write(f"Margin: {product.margin_percentage}%")

        # [공장 정보]
        if product.factory_name:
            st.divider()
            st.caption(f"🏭 Factory: {product.factory_name}")

    else:
        st.error("Product not found.")
        
    session.close()

def show_order_history_page():
    st.header("📜 Order History")
    session = get_db_session()
    
    # Fetch Orders
    orders = session.query(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc()).all()
    
    if not orders:
        st.info("No orders found.")
        session.close()
        return
    
    # Summary Metrics
    total_sales = sum(o.total_amount for o in orders if o.status == "Completed")
    col1, col2 = st.columns(2)
    col1.metric("Total Sales", format_currency(total_sales))
    col2.metric("Total Orders", len(orders))
    
    st.markdown("---")
    
    # Loop for "Table" rows (Streamlit Dataframe is read-only, so we use cols for actions)
    # Header
    h1, h2, h3, h4, h5, h6 = st.columns([1, 2, 2, 2, 2, 2])
    h1.markdown("**ID**")
    h2.markdown("**Date**")
    h3.markdown("**Customer**")
    h4.markdown("**Total**")
    h5.markdown("**Status**")
    h6.markdown("**Action**")
    
    for order in orders:
        with st.container(border=True):
            r1, r2, r3, r4, r5, r6 = st.columns([1, 2, 2, 2, 2, 2])
            r1.write(f"#{order.id}")
            r2.write(order.created_at.strftime("%Y-%m-%d %H:%M"))
            r3.write(order.customer_name if order.customer_name else "-")
            r4.write(format_currency(order.total_amount))
            
            status_color = "green" if order.status == "Completed" else "red"
            r5.markdown(f":{status_color}[{order.status}]")
            
            with r6:
                if st.button("📄 Details", key=f"hist_view_{order.id}"):
                    view_order_details(order.id)

    session.close()

@st.dialog("Order Details")
def view_order_details(order_id):
    session = get_db_session()
    order = session.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
    
    if order:
        st.subheader(f"Order #{order.id}")
        st.caption(f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"Customer: {order.customer_name}")
        st.markdown("---")
        
        st.markdown("**Items**")
        for item in order.items:
            c1, c2, c3, c4 = st.columns([4, 1, 2, 2])
            c1.write(item.product_name)
            c2.write(f"x{item.quantity}")
            c3.write(format_currency(item.unit_price))
            c4.write(format_currency(item.subtotal))
            
        st.markdown("---")
        st.markdown(f"### Total: {format_currency(order.total_amount)}")
        
        if order.status == "Completed":
            st.markdown("---")
            if st.button("❌ Cancel & Refund Order", type="primary", key=f"cancel_order_{order.id}"):
                try:
                    # Logic: Restore Stock
                    for item in order.items:
                        product = session.query(Product).filter(Product.id == item.product_id).first()
                        if product:
                            product.stock_quantity += item.quantity
                    
                    order.status = "Cancelled"
                    session.commit()
                    st.toast("Order Cancelled & Stock Restored!", icon="↩️")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Cancellation Failed: {e}")
        else:
            st.warning("This order is cancelled.")

    session.close()

def show_admin_page():
    st.header("👥 Admin / Member Management")
    # Security Check
    if st.session_state.get('user_role') != 'SuperUser':
        st.error("⛔ Access Denied: SuperUser only.")
        return
    session = get_db_session()
    # 1. Create New Biz User
    with st.expander("➕ Register New Biz Member", expanded=True):
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            new_username = col1.text_input("Username (ID)")
            new_password = col2.text_input("Password", type="password")
            
            col3, col4 = st.columns(2)
            shop_name = col3.text_input("Shop Name (e.g. Diamond Bank)")
            shop_code = col4.text_input("Shop Code (e.g. DB)").upper()
            
            submit_user = st.form_submit_button("Create Member")
            
            if submit_user:
                if new_username and new_password and shop_code:
                    # Check if user exists
                    existing = session.query(User).filter(User.username == new_username).first()
                    if existing:
                        st.error("Username already exists.")
                    else:
                        # Create User
                        # Note: In production, use hashing. For now, simple storage as requested or use same hash logic.
                        import hashlib
                        pw_hash = hashlib.sha256(new_password.encode()).hexdigest()
                        
                        new_user = User(
                            username=new_username, 
                            password_hash=pw_hash,
                            shop_name=shop_name,
                            shop_code=shop_code,
                            role='Biz'
                        )
                        session.add(new_user)
                        session.commit()
                        st.success(f"✅ Member '{new_username}' ({shop_name}) created!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Please fill in all fields.")
    # 2. List Existing Users
    st.subheader("📋 Member List")
    users = session.query(User).all()
    
    # Header
    c1, c2, c3, c4 = st.columns([1, 2, 2, 1]) 
    c1.markdown("ID") 
    c2.markdown("Shop Name") 
    c3.markdown("Shop Code") 
    c4.markdown("Role") 
    st.divider()

    for u in users: 
        c1, c2, c3, c4 = st.columns([1, 2, 2, 1]) 
        c1.write(u.username) 
        c2.write(u.shop_name) 
        c3.write(u.shop_code) 
        c4.write(u.role)

    session.close()


# --- Main Logic ---

# Initialize Data
run_migrations()
init_db_data()

st.sidebar.title("💎 Jewelry ERP")

if 'logged_in' not in st.session_state:
    show_login_page()
else:
    # Sidebar Info
    st.sidebar.markdown(f"User: **{st.session_state.user_name}** ({st.session_state.shop_code})")
    if st.sidebar.button("Logout"):
        logout_user()

    # --- Phase 13-2: Auto-Run Image Maximization (One-time check) ---
    if st.session_state.user_role == 'SuperUser':
        if 'img_optimized_v2' not in st.session_state:
            # We treat this as a "Notify" or auto-run
            # To prevent blocking, we can just show a toast or run it
            # The prompt says: "Automatically re-run... so the user sees the change immediately upon refresh."
            # Running it here might be slow, but it's requested.
            count = normalize_existing_images()
            st.session_state['img_optimized_v2'] = True
            if count > 0:
                st.toast(f"✅ Optimized {count} images to Maximize Size!", icon="🖼️")

    # Migration Tool (SuperUser Only)
    if st.session_state.user_role == 'SuperUser':
        if st.sidebar.button("⚠️ Run Data Migration"):
            run_data_migration()

    if 'edit_mode_id' in st.session_state and st.session_state['edit_mode_id']:
        st.session_state['nav_selection'] = "Register Product"
    elif 'nav_selection' not in st.session_state:
        st.session_state['nav_selection'] = "Gallery"

    # Define Menu
    menu_options = ["Gallery", "Register Product", "Sales / POS", "Order History", "Settings"]
    
    # Admin Menu
    if st.session_state.user_role == 'SuperUser':
        menu_options.insert(4, "Admin / Members")
        
    page = st.sidebar.radio("Navigate", menu_options, key="nav_selection")

    if page == "Gallery": show_gallery_page()
    elif page == "Register Product": show_register_page()
    elif page == "Sales / POS": show_sales_page()
    elif page == "Order History": show_order_history_page()
    elif page == "Admin / Members": show_admin_page()
    elif page == "Settings": show_settings_page()

    st.sidebar.divider()
    st.sidebar.caption("System v1.4 | Auth Enabled")


