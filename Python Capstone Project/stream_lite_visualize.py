# Import required libraries
import pandas as pd
import sqlite3
from datetime import datetime
from abc import ABC, abstractmethod
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
import hashlib
import re

def create_database():
    """Create SQLite database and tables"""
    conn = sqlite3.connect('tax_arrears.db')
    cursor = conn.cursor()
    
    # Create Taxpayers table
    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS taxpayers (
                            pin_no TEXT PRIMARY KEY,
                            tax_payer_name TEXT NOT NULL,
                            phone_no TEXT,
                            station_name TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    '''
                   )
    
    # Create Tax Records table 
    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS tax_records (
                            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            pin_no TEXT,
                            obligation_name TEXT NOT NULL,
                            from_date DATE,
                            to_date DATE,
                            principal REAL DEFAULT 0,
                            penalty REAL DEFAULT 0,
                            interest REAL DEFAULT 0,
                            grand_total REAL DEFAULT 0,
                            status TEXT DEFAULT 'PENDING',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (pin_no) REFERENCES taxpayers(pin_no)
                        )
                    '''
                    )
    
    # Create Audit Log table
    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS audit_log (
                            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            action TEXT,
                            pin_no TEXT,
                            record_id INTEGER,
                            old_value TEXT,
                            new_value TEXT,
                            changed_by TEXT DEFAULT 'SYSTEM',
                            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    '''
                    )
    
    # Create Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'VIEWER',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database created successfully!")

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = 'VIEWER'


def login_page():
    """Login page for the application"""
    st.title("🔐 Tax Arrears Management System - Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h2>Welcome to TAMS</h2>
            <p>Please login to access the system</p>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            # Simple authentication (in production, use proper authentication)
            if username == "admin" and password == "admin123":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = "ADMIN"
                st.success("Login successful!")
                st.rerun()
            elif username == "viewer" and password == "viewer123":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = "VIEWER"
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")


def dashboard_page(db_manager):
    """Main dashboard page"""
    st.title("📊 Tax Arrears Dashboard")
    
    # Get statistics
    stats = db_manager.get_summary_statistics()
    
    # Display KPI cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Taxpayers", f"{stats['total_taxpayers']:,}")
    
    with col2:
        st.metric("Total Records", f"{stats['total_records']:,}")  # Renamed from total_obligations
    
    with col3:
        st.metric("Total Arrears", f"KES {stats['total_arrears']:,.0f}")
    
    with col4:
        st.metric("Total Penalties", f"KES {stats['total_penalties']:,.0f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Arrears by Station")
        if not stats['by_station'].empty:
            fig = px.pie(stats['by_station'], values='arrears', names='station_name',
                         title='Distribution of Tax Arrears by Station')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for station-wise analysis")
    
    with col2:
        st.subheader("Records by Obligation Type")  # Renamed
        if not stats['by_obligation'].empty:
            fig = px.bar(stats['by_obligation'].head(10), 
                         x='obligation_name', y='count',
                         title='Top 10 Obligation Types',
                         labels={'count': 'Number of Records',  # Renamed
                                'obligation_name': 'Obligation Type'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for obligation type analysis")
    
    # Recent taxpayers
    st.subheader("Recent Taxpayers")
    df_taxpayers = db_manager.get_all_taxpayers()
    if not df_taxpayers.empty:
        st.dataframe(
            df_taxpayers[['pin_no', 'tax_payer_name', 'station_name', 
                          'total_records', 'total_principal', 'total_arrears']].head(10),  # Renamed
            use_container_width=True,
            hide_index=True
        )


def taxpayers_page(db_manager):
    """Taxpayers management page"""
    st.title("👥 Taxpayers Management")
    
    # Get all taxpayers
    df = db_manager.get_all_taxpayers()
    
    if df.empty:
        st.info("No taxpayers found in the database")
        return
    
    # Search and filter
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("🔍 Search by name or PIN", "")
    
    with col2:
        station_filter = st.multiselect("Filter by Station", 
                                        options=df['station_name'].unique())
    
    # Apply filters
    filtered_df = df.copy()
    if search_term:
        filtered_df = filtered_df[
            filtered_df['tax_payer_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['pin_no'].str.contains(search_term, case=False, na=False)
        ]
    
    if station_filter:
        filtered_df = filtered_df[filtered_df['station_name'].isin(station_filter)]
    
    # Display
    st.dataframe(
        filtered_df[['pin_no', 'tax_payer_name', 'station_name', 'phone_no',
                    'total_records', 'total_principal', 'total_penalty',
                    'total_interest', 'total_arrears']],  
        use_container_width=True,
        hide_index=True
    )
    
    # Export option
    if st.button("📥 Export to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"taxpayers_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def records_page(db_manager):  
    """Tax records management page"""
    st.title("📋 Tax Records")
    
    conn = db_manager.get_connection()
    
    # Get all records with taxpayer details
    query = '''
        SELECT 
            r.record_id,
            t.pin_no,
            t.tax_payer_name,
            r.obligation_name,
            r.from_date,
            r.to_date,
            r.principal,
            r.penalty,
            r.interest,
            r.grand_total,
            r.status
        FROM tax_records r
        JOIN taxpayers t ON r.pin_no = t.pin_no
        ORDER BY r.from_date DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("No tax records found in the database")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect("Filter by Status", 
                                      options=df['status'].unique())
    
    with col2:
        name_filter = st.text_input("Search by taxpayer name", "")
    
    with col3:
        min_amount = st.number_input("Minimum amount", min_value=0, value=0, step=1000)
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    
    if name_filter:
        filtered_df = filtered_df[filtered_df['tax_payer_name'].str.contains(name_filter, case=False, na=False)]
    
    if min_amount > 0:
        filtered_df = filtered_df[filtered_df['grand_total'] >= min_amount]
    
    # Display
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary
    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(filtered_df))  # Renamed
    with col2:
        st.metric("Total Principal", f"KES {filtered_df['principal'].sum():,.0f}")
    with col3:
        st.metric("Total Penalties", f"KES {filtered_df['penalty'].sum():,.0f}")
    with col4:
        st.metric("Total Interest", f"KES {filtered_df['interest'].sum():,.0f}")


def analytics_page(db_manager):
    """Advanced analytics page"""
    st.title("📈 Advanced Analytics")
    
    conn = db_manager.get_connection()
    
    # Time series analysis
    query = '''
        SELECT 
            strftime('%Y', from_date) as year,
            COUNT(*) as record_count,
            SUM(principal) as total_principal,
            SUM(penalty) as total_penalty,
            SUM(interest) as total_interest,
            SUM(grand_total) as total_arrears
        FROM tax_records
        WHERE from_date IS NOT NULL AND from_date != ''
        GROUP BY year
        ORDER BY year
    '''
    df_yearly = pd.read_sql_query(query, conn)
    
    if not df_yearly.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(df_yearly, x='year', y='total_principal',
                          title='Annual Tax Principal Trend',
                          labels={'total_principal': 'Total Principal (KES)', 'year': 'Year'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(df_yearly, x='year', y='record_count',
                         title='Annual Record Count',
                         labels={'record_count': 'Number of Records', 'year': 'Year'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Top defaulters
    query = '''
        SELECT 
            t.tax_payer_name,
            t.pin_no,
            COUNT(r.record_id) as records,
            SUM(r.grand_total) as total_arrears,
            SUM(r.penalty) as total_penalties
        FROM taxpayers t
        JOIN tax_records r ON t.pin_no = r.pin_no
        WHERE r.grand_total > 0
        GROUP BY t.pin_no
        ORDER BY total_arrears DESC
        LIMIT 10
    '''
    df_top = pd.read_sql_query(query, conn)
    
    st.subheader("Top 10 Defaulters")
    if not df_top.empty:
        fig = px.bar(df_top, x='tax_payer_name', y='total_arrears',
                     title='Top 10 Taxpayers by Arrears Amount',
                     labels={'total_arrears': 'Total Arrears (KES)', 'tax_payer_name': 'Taxpayer'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Status distribution
    query = '''
        SELECT 
            status,
            COUNT(*) as count,
            SUM(grand_total) as total_amount
        FROM tax_records
        GROUP BY status
    '''
    df_status = pd.read_sql_query(query, conn)
    
    if not df_status.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(df_status, values='count', names='status',
                         title='Records by Status')  # Renamed
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(df_status, values='total_amount', names='status',
                         title='Arrears Amount by Status')
            st.plotly_chart(fig, use_container_width=True)
    
    # Penalty vs Interest Analysis
    query = '''
        SELECT 
            obligation_name,
            SUM(penalty) as total_penalty,
            SUM(interest) as total_interest
        FROM tax_records
        GROUP BY obligation_name
        HAVING total_penalty > 0 OR total_interest > 0
        ORDER BY (total_penalty + total_interest) DESC
        LIMIT 10
    '''
    df_penalty_interest = pd.read_sql_query(query, conn)
    
    if not df_penalty_interest.empty:
        st.subheader("Top 10 Obligations with Penalties and Interest")
        fig = px.bar(df_penalty_interest, x='obligation_name', 
                     y=['total_penalty', 'total_interest'],
                     title='Penalty vs Interest by Obligation Type',
                     barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    
    conn.close()


def import_data_page(db_manager):
    """Data import page"""
    st.title("📤 Import Data")
    
    st.info("Upload a CSV file with tax data to import into the system")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        # Show preview of uploaded data
        try:
            df_preview = pd.read_csv(uploaded_file)
            st.subheader("Data Preview")
            st.dataframe(df_preview.head(10), use_container_width=True)
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            if st.button("Start Import", type="primary"):
                # Save uploaded file temporarily
                with open("temp_upload.csv", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner("Importing data..."):
                    importer = DataImporter()
                    result = importer.import_from_csv("temp_upload.csv", db_manager)
                    
                    if 'error' in result:
                        st.error(f"Error importing data: {result['error']}")
                    else:
                        st.success("✅ Import completed successfully!")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Taxpayers Added", result['taxpayers_added'])
                        col2.metric("Records Added", result['records_added'])  # Renamed
                        col3.metric("Errors", result['errors'])
        except Exception as e:
            st.error(f"Error reading file: {e}")


def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Tax Arrears Management System",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    create_database()
    
    # Initialize session state
    init_session_state()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/tax.png", width=80)
        st.title(f"Welcome, {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.role}")
        st.markdown("---")
        
        # Navigation menu
        menu_options = {
            "🏠 Dashboard": dashboard_page,
            "👥 Taxpayers": taxpayers_page,
            "📋 Tax Records": records_page,  # Renamed
            "📈 Analytics": analytics_page,
        }
        
        # Add admin-only pages
        if st.session_state.role == "ADMIN":
            menu_options["📤 Import Data"] = import_data_page
        
        selection = st.radio("Navigation", list(menu_options.keys()))
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
    
    # Display selected page
    menu_options[selection](db_manager)


if __name__ == "__main__":
    main()