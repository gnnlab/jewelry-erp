import streamlit as st
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload
from sqlalchemy.sql import func
import time
import os
import math
from datetime import datetime

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

# --- Models ---

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50), nullable=True) # NEW: Sub-category
    name = Column(String(255), nullable=False)
    
    # Images (Paths)
    image_rep = Column(String(500))
    image_top = Column(String(500))
    image_front = Column(String(500))
    image_side = Column(String(500))
    
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

def save_uploaded_file(uploaded_file, prefix):
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}_{uploaded_file.name}"
        filepath = os.path.join(IMAGE_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath
    return None

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
    final_price_e = 0
    
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
            
            if product.jewelry_details:
                jd = product.jewelry_details
                st.session_state['reg_gold_purity'] = jd.gold_purity
                st.session_state['reg_gold_weight'] = jd.gold_weight
                st.session_state['reg_gold_price_applied'] = jd.gold_price_applied
                st.session_state['reg_labor'] = jd.labor_cost
                st.session_state['reg_margin'] = jd.margin_pct
                st.session_state['reg_discount'] = jd.discount_pct
                st.session_state['reg_vat'] = jd.vat_pct
                st.session_state['reg_fee'] = jd.fee_pct

            if product.diamond_details:
                dd = product.diamond_details
                st.session_state['dia_type'] = dd.stone_type
                st.session_state['dia_cert'] = dd.certificate
                st.session_state['dia_shape'] = dd.shape
                st.session_state['dia_weight'] = dd.weight
                st.session_state['dia_color'] = dd.color
                st.session_state['dia_clarity'] = dd.clarity
                st.session_state['dia_cut'] = dd.cut
                st.session_state['dia_polish'] = dd.polish
                st.session_state['dia_symmetry'] = dd.symmetry
                st.session_state['dia_fluo'] = dd.fluorescence
                st.session_state['dia_cost'] = dd.purchase_cost
                st.session_state['dia_margin'] = dd.margin_pct
                st.session_state['dia_vat'] = dd.vat_pct

            if product.color_stone_details:
                cs = product.color_stone_details
                st.session_state['cs_type'] = cs.stone_type
                st.session_state['cs_cert'] = cs.cert_agency
                st.session_state['cs_shape'] = cs.shape
                st.session_state['cs_weight'] = cs.weight
                st.session_state['cs_color'] = cs.color
                st.session_state['cs_tone'] = cs.tone
                st.session_state['cs_sat'] = cs.saturation
                st.session_state['cs_clarity'] = cs.clarity
                st.session_state['cs_origin'] = cs.origin
                st.session_state['cs_comment'] = cs.comment
                st.session_state['cs_cost'] = cs.purchase_cost
                st.session_state['cs_margin'] = cs.margin_pct
                st.session_state['cs_vat'] = cs.vat_pct
                st.session_state['cs_tax'] = cs.tax_rate

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
                st.session_state['w_cost'] = wd.purchase_cost
                st.session_state['w_margin'] = wd.margin_pct
                st.session_state['w_vat'] = wd.vat_pct
                st.session_state['w_tax'] = wd.tax_pct

            if product.etc_details:
                ed = product.etc_details
                st.session_state['e_name'] = product.name # Name handles itself but just in case
                st.session_state['e_stock'] = product.stock_quantity
                st.session_state['e_comments'] = ed.comments
                st.session_state['e_cost'] = ed.purchase_cost
                st.session_state['e_margin'] = ed.margin_pct
                st.session_state['e_vat'] = ed.vat_pct
                st.session_state['e_tax'] = ed.tax_pct

            m_stones = []
            s_stones = []
            if product.stones:
                for s in product.stones:
                    s_data = {'name': s.name, 'qty': s.quantity, 'price': s.unit_price}
                    if s.stone_type == "Main": m_stones.append(s_data)
                    elif s.stone_type == "Sub": s_stones.append(s_data)
            
            if not m_stones: m_stones = [{'name': '', 'qty': 0, 'price': 0}]
            if not s_stones: s_stones = [{'name': '', 'qty': 0, 'price': 0}]
            
            st.session_state.main_stones = m_stones
            st.session_state.sub_stones = s_stones
            st.session_state['data_loaded'] = True
            st.rerun()

    if not edit_mode_id and 'data_loaded' in st.session_state:
         del st.session_state['data_loaded']
         keys_to_clear = ['reg_name', 'reg_stock', 'reg_category', 'reg_subcategory', 'reg_gold_weight', 'reg_gold_price_applied', 'reg_labor', 'reg_margin', 'reg_discount', 'reg_vat', 'reg_fee', 'reg_img_rep', 'reg_img_top', 'reg_img_front', 'reg_img_side', 'dia_name', 'dia_type', 'dia_cert', 'dia_shape', 'dia_weight', 'dia_color', 'dia_clarity', 'dia_cut', 'dia_polish', 'dia_symmetry', 'dia_fluo', 'dia_cost', 'dia_margin', 'dia_vat']
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

    if product_type in ["Jewelry", "Gold", "Etc"]:
        st.subheader("1. Basic Info & Images")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            name = st.text_input("Product Name", placeholder="Enter product name", key="reg_name")
        with c2:
            st.text_input("Category Path", value=f"{product_type} > {sub_category}", disabled=True)
        with c3:
            stock_qty = st.number_input("Stock Quantity", min_value=0, value=1, step=1, key="reg_stock")
            
        st.markdown("**Product Images**")
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
        st.subheader("2. Materials")
        
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            purity_options = ["24K", "18K", "14K", "PT", "Silver", "Etc"]
            
            # Helper to handle pre-filled custom values
            current_purity = st.session_state.get('reg_gold_purity', '18K')
            
            # Default logic: If new product and category is Gold, default to 24K. Else default to 18K (index 1)
            default_idx = 1
            if not edit_mode_id and product_type == "Gold":
                 default_idx = 0 # 24K
                 
            if current_purity in purity_options:
                default_idx = purity_options.index(current_purity)
            elif current_purity: # Custom value exists
                default_idx = purity_options.index("Etc")

            purity_sel = st.selectbox("Gold Purity", purity_options, index=default_idx, key="reg_gold_purity_sel")
            
            if purity_sel == "Etc":
                custom_val = current_purity if current_purity not in purity_options else ""
                gold_purity = st.text_input("Enter Material Name", value=custom_val, key="reg_gold_purity_manual")
            else:
                gold_purity = purity_sel
            
            # Sync to session state for persistence
            st.session_state['reg_gold_purity'] = gold_purity
        with g_col2:
            gold_weight = st.number_input("Gold Weight (g)", min_value=0.0, format="%.2f", key="reg_gold_weight")
            
            # Determine Multiplier & Label
            multiplier = 1.0
            price_label = "Today's Pure Gold (24K) Price (per Don)"
            
            if gold_purity == "18K":
                multiplier = 0.825
            elif gold_purity == "14K":
                multiplier = 0.6435
            elif gold_purity == "PT":
                price_label = "Today's Platinum Price (per Don)"
            elif gold_purity == "Silver":
                price_label = "Today's Silver Price (per Don)"
                
            # Gold Price (Don System) - Input BASE Price
            # If editing, we need to reverse calc the base price from the applied per-gram price
            # But simpler to just store/recall the Base Don Price in session? 
            # For now, let's use the current 'reg_gold_price_don' if set, else approximate from applied.
            
            current_applied_per_g = st.session_state.get('reg_gold_price_applied', 380000)
            # Reverse engineer default base don price for initial load
            try:
                approx_base_don = int((current_applied_per_g * 3.75) / multiplier)
            except:
                approx_base_don = 450000

            # If we already have a manual input in session, respect it
            if 'reg_base_price_don' not in st.session_state:
                st.session_state['reg_base_price_don'] = approx_base_don

            base_price_don = st.number_input(price_label, min_value=0, value=st.session_state['reg_base_price_don'], step=1000, key="reg_base_price_don_input")
            st.session_state['reg_base_price_don'] = base_price_don # Keep sync
            
            # Logic: Applied Price per Don = Base * Multiplier
            applied_price_don = base_price_don * multiplier
            
            # Logic: Per Gram (for storage consistency) = math.floor((Applied Don / 3.75) / 100) * 100
            gold_price_applied = math.floor((applied_price_don / 3.75) / 100) * 100
            
            if multiplier != 1.0:
                st.caption(f"ℹ️ Applied ({multiplier}): {format_currency(applied_price_don)} / don")
            st.caption(f"≈ {format_currency(gold_price_applied)} / g (Stored)")
            
            # Update session state for calculation & saving
            st.session_state['reg_gold_price_applied'] = gold_price_applied
            
        st.markdown("**Stones Details**")
        
        stone_types = ["None", "Diamond", "Ruby", "Sapphire", "Emerald", "Pearl", "Cubic Zirconia", "Direct Input"]
        
        def stone_input_row(prefix, index, obj):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                # Resolve current name to type + text
                current_name = obj['name']
                current_type = "None" # Default
                manual_text = ""
                
                if current_name in stone_types:
                    current_type = current_name
                elif current_name: # Something else
                    current_type = "Direct Input"
                    manual_text = current_name
                    
                sel_type = st.selectbox(f"Type {index+1}", stone_types, index=stone_types.index(current_type) if current_type in stone_types else 0, key=f"{prefix}_type_{index}")
                
                final_name = sel_type
                if sel_type == "Direct Input":
                    final_name = st.text_input(f"Name {index+1}", value=manual_text, placeholder="Type stone name", key=f"{prefix}_manual_{index}")
                    
                # Update Session State Immediately for persistence
                st.session_state[prefix == "ms" and "main_stones" or "sub_stones"][index]['name'] = final_name
                
            with c2:
                st.session_state[prefix == "ms" and "main_stones" or "sub_stones"][index]['qty'] = st.number_input(f"Qty", min_value=0, value=obj['qty'], key=f"{prefix}_qty_{index}")
            with c3:
                st.session_state[prefix == "ms" and "main_stones" or "sub_stones"][index]['price'] = st.number_input(f"Price", min_value=0, step=1000, value=obj['price'], key=f"{prefix}_price_{index}")

        st.caption("Main Stones")
        for i, stone in enumerate(st.session_state.main_stones):
             stone_input_row("ms", i, stone)

        m_btn_c1, m_btn_c2 = st.columns([1, 5])
        with m_btn_c1: st.button("➕ Add", on_click=add_main_stone, key='add_main_btn')
        with m_btn_c2: st.button("➖ Remove", on_click=remove_main_stone, key='remove_main_btn')
            
        st.caption("Sub Stones")
        for i, stone in enumerate(st.session_state.sub_stones):
             stone_input_row("ss", i, stone)

        s_btn_c1, s_btn_c2 = st.columns([1, 5])
        with s_btn_c1: st.button("➕ Add", on_click=add_sub_stone, key='add_sub_btn')
        with s_btn_c2: st.button("➖ Remove", on_click=remove_sub_stone, key='remove_sub_btn')

        st.markdown("---")
        st.subheader("3. Pricing Factors")
        
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1: labor_cost = st.number_input("Labor Cost (RW)", min_value=0, step=5000, key="reg_labor")
        with p_col2: margin_pct = st.number_input("Margin (%)", min_value=0.0, value=10.0, key="reg_margin")
        with p_col3: discount_pct = st.number_input("Discount (%)", min_value=0.0, value=0.0, key="reg_discount")
            
        p_col4, p_col5 = st.columns(2)
        with p_col4: vat_pct = st.number_input("VAT (%)", min_value=0.0, value=10.0, key="reg_vat")
        with p_col5: fee_pct = st.number_input("Fee (%)", min_value=0.0, value=3.0, key="reg_fee")

        # Calculations
        gold_cost = gold_weight * gold_price_applied
        stone_cost = 0
        for s in st.session_state.main_stones: stone_cost += (s['qty'] * s['price'])
        for s in st.session_state.sub_stones: stone_cost += (s['qty'] * s['price'])
            
        product_cost = gold_cost + stone_cost + labor_cost
        selling_price = product_cost * (1 + margin_pct/100)
        expected_profit = selling_price - product_cost
        
        vat_amount = selling_price * (vat_pct / 100)
        fee_amount = selling_price * (fee_pct / 100)
        final_price = selling_price + vat_amount + fee_amount
        
        st.markdown("### 💰 Price Preview")
        calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
        calc_col1.metric("Product Cost", format_currency(product_cost))
        calc_col2.metric("Expected Profit (Margin)", format_currency(expected_profit), delta_color="normal")
        calc_col3.metric("Selling Price", format_currency(selling_price))
        calc_col4.metric("Final Price", format_currency(final_price), delta_color="normal")
        
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
        st.subheader("💰 Pricing")
        pc1, pc2, pc3 = st.columns(3)
        with pc1: d_cost = st.number_input("Purchase Cost (KRW)", min_value=0, step=10000, key="dia_cost")
        with pc2: d_margin = st.number_input("Margin (%)", min_value=0.0, value=10.0, key="dia_margin")
        with pc3: d_vat = st.number_input("VAT (%)", min_value=0.0, value=10.0, key="dia_vat")
        
        # Calc
        selling_price_dia = d_cost * (1 + d_margin/100)
        final_price_dia = selling_price_dia * (1 + d_vat/100)
        final_price = final_price_dia
        
        st.metric("Final Price (Inc. VAT)", format_currency(final_price_dia))
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
        st.subheader("💰 Pricing")
        
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1: cs_cost = st.number_input("Cost (KRW)", min_value=0, step=10000, key="cs_cost")
        with pc2: cs_margin = st.number_input("Margin (%)", min_value=0.0, value=20.0, key="cs_margin")
        with pc3: cs_vat = st.number_input("VAT (%)", min_value=0.0, value=10.0, key="cs_vat")
        with pc4: cs_tax = st.number_input("Tax/Fee (%)", min_value=0.0, value=0.0, key="cs_tax")

        # Pricing Logic: Final = Cost + (Cost*Margin) + VAT_Amt + Tax_Amt
        margin_amt = cs_cost * (cs_margin / 100)
        vat_amt = (cs_cost + margin_amt) * (cs_vat / 100) # Standard VAT on Sale Price
        tax_amt = (cs_cost + margin_amt) * (cs_tax / 100) # Fee on Sale Price
        
        final_price_cs = (cs_cost + margin_amt) + vat_amt + tax_amt
        final_price = final_price_cs
        
        st.metric("Final Price (Inc. Tax+VAT)", format_currency(final_price_cs))
        st.caption(f"Margin: {format_currency(margin_amt)} | VAT: {format_currency(vat_amt)} | Tax: {format_currency(tax_amt)}")
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
        st.subheader("💰 Pricing")
        
        # Pricing Logic (Margin-based Tax)
        wp1, wp2, wp3, wp4 = st.columns(4)
        with wp1: w_cost = st.number_input("Cost (KRW)", min_value=0, step=10000, key="w_cost")
        with wp2: w_margin = st.number_input("Margin (%)", min_value=0.0, value=15.0, key="w_margin")
        with wp3: w_vat = st.number_input("VAT (%)", min_value=0.0, value=10.0, key="w_vat")
        with wp4: w_tax = st.number_input("Tax (%)", min_value=0.0, value=0.0, key="w_tax")
        
        # Formula:
        # Margin Amt = Cost * Margin%
        # VAT Amt = Margin Amt * VAT%
        # Tax Amt = Margin Amt * Tax%
        # Final = Cost + Margin Amt + VAT Amt + Tax Amt
        
        w_margin_amt = w_cost * (w_margin / 100)
        w_vat_amt = w_margin_amt * (w_vat / 100)
        w_tax_amt = w_margin_amt * (w_tax / 100)
        
        final_price_w = w_cost + w_margin_amt + w_vat_amt + w_tax_amt
        final_price = final_price_w
        
        st.metric("Final Price", format_currency(final_price_w))
        st.caption(f"Margin: {format_currency(w_margin_amt)} | VAT: {format_currency(w_vat_amt)} | Tax: {format_currency(w_tax_amt)}")
        st.markdown("---")

    elif product_type == "Etc":
        st.subheader("1. General Item Details")
        
        # Row 1: Name | SubCat
        ec1, ec2 = st.columns([2, 1])
        with ec1: name = st.text_input("Product Name", placeholder="e.g. Leather Strap, Watch Box", key="e_name")
        with ec2: 
             # Sub Category is handled at top, just display stock
             stock_qty = st.number_input("Stock Qty", min_value=1, value=1, key="e_stock")

        # Row 2: Images
        st.markdown("### Images")
        img_col1, img_col2, img_col3, img_col4 = st.columns(4)
        with img_col1: img_rep = st.file_uploader("Main Image", type=['png', 'jpg', 'jpeg'], key="e_img_rep")
        with img_col2: img_top = st.file_uploader("Top View", type=['png', 'jpg', 'jpeg'], key="e_img_top")
        with img_col3: img_front = st.file_uploader("Front View", type=['png', 'jpg', 'jpeg'], key="e_img_front")
        with img_col4: img_side = st.file_uploader("Side View", type=['png', 'jpg', 'jpeg'], key="e_img_side")
        
        st.markdown("---")
        st.subheader("💰 Pricing")
        
        # Pricing Logic (Same as Watch: Margin-based Tax)
        ep1, ep2, ep3, ep4 = st.columns(4)
        with ep1: e_cost = st.number_input("Cost (KRW)", min_value=0, step=1000, key="e_cost")
        with ep2: e_margin = st.number_input("Margin (%)", min_value=0.0, value=30.0, key="e_margin")
        with ep3: e_vat = st.number_input("VAT (%)", min_value=0.0, value=10.0, key="e_vat")
        with ep4: e_tax = st.number_input("Tax (%)", min_value=0.0, value=0.0, key="e_tax")

        # Formula: Final = Cost + Margin + VAT(Margin) + Tax(Margin)
        e_margin_amt = e_cost * (e_margin / 100)
        e_vat_amt = e_margin_amt * (e_vat / 100)
        e_tax_amt = e_margin_amt * (e_tax / 100)
        
        final_price_e = e_cost + e_margin_amt + e_vat_amt + e_tax_amt
        final_price = final_price_e
        
        st.metric("Final Price", format_currency(final_price_e))
        st.caption(f"Margin: {format_currency(e_margin_amt)} | VAT: {format_currency(e_vat_amt)} | Tax: {format_currency(e_tax_amt)}")
        
        # Row 4: Remarks
        e_comments = st.text_area("Remarks", height=100, key="e_comments")
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
                    target_product = Product(user_id=1, category=product_type) # Use dynamic type
                    session.add(target_product)
                
                # Common Fields
                target_product.category = product_type
                target_product.sub_category = sub_category
                target_product.name = name
                target_product.total_price = final_price
                target_product.stock_quantity = stock_qty 

                # Image Saving
                if img_rep: target_product.image_rep = save_uploaded_file(img_rep, "rep")
                if img_top: target_product.image_top = save_uploaded_file(img_top, "top")
                if img_front: target_product.image_front = save_uploaded_file(img_front, "front")
                if img_side: target_product.image_side = save_uploaded_file(img_side, "side")
                
                # Type Specific Logic
                if product_type in ["Jewelry", "Gold", "Etc"] and product_type != "Etc": # Fix: logic was merging Etc
                     # ... (Existing Jewelry Logic) ...
                     # Wait, the previous logic merged "Etc" into Jewelry. We need to separate it now since Etc has its own table.
                     pass
                
                # RE-CHECK: The user prompt says "If main_category == 'Etc'".
                # Previously "Etc" was in ["Jewelry", "Gold", "Etc"].
                # Now we must REMOVE "Etc" from that list or handle it specifically.
                
                if product_type in ["Jewelry", "Gold"]:
                    if edit_mode_id and target_product.jewelry_details:
                        jd = target_product.jewelry_details
                    else:
                        jd = ProductJewelry(product=target_product)
                        if not edit_mode_id: session.add(jd)
                        
                    jd.gold_weight = gold_weight
                    jd.gold_purity = gold_purity
                    jd.gold_price_applied = gold_price_applied
                    jd.labor_cost = labor_cost
                    jd.margin_pct = margin_pct
                    jd.discount_pct = discount_pct
                    jd.vat_pct = vat_pct
                    jd.fee_pct = fee_pct
                    jd.product_cost = product_cost
                    jd.calc_selling_price = selling_price
                    jd.final_price = final_price
                    
                    # Stones
                    if edit_mode_id:
                         session.query(ProductStone).filter(ProductStone.product_id == target_product.id).delete()
                    for ms in st.session_state.main_stones:
                        if ms['name']: session.add(ProductStone(product=target_product, stone_type="Main", name=ms['name'], quantity=ms['qty'], unit_price=ms['price']))
                    for ss in st.session_state.sub_stones:
                        if ss['name']: session.add(ProductStone(product=target_product, stone_type="Sub", name=ss['name'], quantity=ss['qty'], unit_price=ss['price']))
                
                elif product_type == "Dia/Stone":
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
                
                session.commit()
                st.toast(f"Product '{name}' saved!", icon="🎉")
                
                if edit_mode_id:
                    del st.session_state['edit_mode_id']
                    del st.session_state['data_loaded']
                    keys_to_clear = ['reg_name', 'reg_stock', 'reg_category', 'reg_subcategory', 'reg_gold_weight', 'reg_gold_price_applied', 'reg_labor', 'reg_margin', 'reg_discount', 'reg_vat', 'reg_fee', 'reg_img_rep', 'reg_img_top', 'reg_img_front', 'reg_img_side', 'dia_name', 'dia_type', 'dia_cert', 'dia_shape', 'dia_weight', 'dia_color', 'dia_clarity', 'dia_cut', 'dia_polish', 'dia_symmetry', 'dia_fluo', 'dia_cost', 'dia_margin', 'dia_vat', 'cs_name', 'cs_type', 'cs_cert', 'cs_shape', 'cs_weight', 'cs_color', 'cs_tone', 'cs_sat', 'cs_clarity', 'cs_origin', 'cs_comment', 'cs_cost', 'cs_margin', 'cs_vat', 'cs_tax', 'w_model', 'w_year', 'w_size', 'w_material', 'w_color', 'w_movement', 'w_band', 'w_cert', 'w_case', 'w_status', 'w_name', 'w_stock', 'w_cost', 'w_margin', 'w_vat', 'w_tax', 'e_name', 'e_stock', 'e_cost', 'e_margin', 'e_vat', 'e_tax', 'e_comments']
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
        else:
            st.info("No sub-categories defined.")

    session.close()

def show_sales_page():
    st.header("🛍️ POS / Sales")
    session = get_db_session()
    
    st.subheader("1. Add Items")
    search_term = st.text_input("Search Product", placeholder="Name or Category...")
    
    query = session.query(Product).filter(Product.stock_quantity > 0)
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
    
    # Gold Price Input (Don System)
    gold_price_don = st.sidebar.number_input("Today's Gold Price (per 1 Don / 3.75g)", min_value=0, value=450000, step=1000, format="%d")
    
    # Calculate Per Gram (Floor to nearest 100)
    gold_price_per_g = math.floor((gold_price_don / 3.75) / 100) * 100
    st.sidebar.caption(f"Applied: {format_currency(gold_price_per_g)} / g")
    
    show_admin_details = st.sidebar.checkbox("Show Admin Details (Cost & Margin)", value=False)
    
    # 2. Fetch All Products
    session = get_db_session()
    all_products = session.query(Product).order_by(Product.created_at.desc()).all()
    
    if not all_products:
        st.info("No products found.")
        session.close()
        return

    # 3. Category Tabs
    categories = ["ALL", "Jewelry", "Gold", "Watch", "Dia/Stone", "ColorStone", "Etc"]
    tabs = st.tabs(categories)
    
    for i, tab in enumerate(tabs):
        with tab:
            selected_cat = categories[i]
            
            # Filter Products
            if selected_cat == "ALL":
                products_to_show = all_products
            else:
                products_to_show = [p for p in all_products if p.category == selected_cat]
            
            if not products_to_show:
                st.info(f"No products in {selected_cat}.")
                continue
                
            # Render Grid
            cols = st.columns(3)
            for idx, product in enumerate(products_to_show):
                with cols[idx % 3]:
                    with st.container(border=True):
                        # Stock Badge
                        if product.stock_quantity > 0:
                            st.markdown(f":green[In Stock: {product.stock_quantity}]")
                        else:
                            st.markdown(":red[Out of Stock]")
                        
                        # Image
                        if product.image_rep and os.path.exists(product.image_rep):
                            st.image(product.image_rep)
                        else:
                            st.empty() 
                        
                        st.subheader(product.name)
                        st.caption(f"{product.category} / {product.sub_category if product.sub_category else '-'}")
                        
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
                            if st.button("👁️", key=f"view_{selected_cat}_{product.id}"): view_product_details(product.id, gold_price_per_g)
                        with ac2:
                            st.button("✏️", key=f"edit_{selected_cat}_{product.id}", on_click=go_to_edit, args=(product.id,))
                        with ac3:
                            if st.button("🗑️", key=f"del_{selected_cat}_{product.id}"):
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
    
    st.markdown("""<style>div[data-testid="stDialog"] div[data-testid="column"]:nth-of-type(2) button {color: red !important; border-color: red !important;}</style>""", unsafe_allow_html=True)
    
    if product:
        st.header(product.name)
        col_edit, col_del = st.columns(2)
        with col_edit:
            st.button("✏️ Edit Product", use_container_width=True, key=f"pop_edit_{product.id}", on_click=go_to_edit, args=(product.id,))
        with col_del:
            if st.button("🗑️ Delete Product", use_container_width=True, key=f"pop_del_{product.id}"):
                 try:
                     session.delete(product)
                     session.commit()
                     st.toast("Product deleted!")
                     time.sleep(1)
                     st.rerun()
                 except Exception as e: st.error(f"Error: {e}")
        
        st.markdown("---")
        if product.image_rep: st.image(product.image_rep, caption="Representative")
            
        imgs = [x for x in [product.image_top, product.image_front, product.image_side] if x and os.path.exists(x)]
        if imgs:
            st.markdown("##### Additional Views")
            ic1, ic2, ic3 = st.columns(3)
            for i, img_path in enumerate(imgs):
                with [ic1, ic2, ic3][i]: st.image(img_path)

        st.markdown("---")
        st.write(f"**Category:** {product.category} > {product.sub_category}")
        st.write(f"**Stock:** {product.stock_quantity}")
        
        if product.jewelry_details:
             jd = product.jewelry_details
             gold_cost = jd.gold_weight * current_gold_price
             stone_cost = sum(s.quantity * s.unit_price for s in product.stones) if product.stones else 0
             prod_cost = gold_cost + stone_cost + jd.labor_cost
             selling = prod_cost * (1 + jd.margin_pct / 100)
             final = selling * (1 + (jd.vat_pct + jd.fee_pct)/100)

             st.markdown(f"### 🏷️ Current Price: {format_currency(final)}")
             st.markdown("#### Materials")
             st.write(f"**Gold**: {jd.gold_purity} | {jd.gold_weight}g")
             if product.stones:
                 st.markdown("**Stones:**")
                 for stone in product.stones:
                     st.write(f"- {stone.stone_type}: {stone.name} ({stone.quantity} x {format_currency(stone.unit_price)})")
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

# --- Main Logic ---

st.sidebar.title("💎 Jewelry ERP")

if 'edit_mode_id' in st.session_state and st.session_state['edit_mode_id']:
    st.session_state['nav_selection'] = "Register Product"
elif 'nav_selection' not in st.session_state:
    st.session_state['nav_selection'] = "Gallery"

page = st.sidebar.radio("Navigate", ["Gallery", "Register Product", "Sales / POS", "Order History", "Settings"], key="nav_selection")

if page == "Gallery": show_gallery_page()
elif page == "Register Product": show_register_page()
elif page == "Sales / POS": show_sales_page()
elif page == "Order History": show_order_history_page()
elif page == "Settings": show_settings_page()

st.sidebar.divider()
st.sidebar.caption("System v1.4 | Order History")
