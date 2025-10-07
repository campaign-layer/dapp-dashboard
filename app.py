#!/usr/bin/env python3
"""
Camp Network MAU Dashboard - Blockscout API Version
Supports both token transfers AND general contract events!
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from collections import defaultdict
import io

# Page config
st.set_page_config(
    page_title="Camp Network MAU Dashboard",
    page_icon="🏕️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🏕️ Camp Network MAU Dashboard</h1>', unsafe_allow_html=True)
st.markdown("**Powered by Blockscout API** - Works for tokens AND general contracts!")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    blockscout_url = st.text_input(
        "Blockscout Base URL",
        value="https://camp.cloud.blockscout.com",
        help="Camp Network Blockscout explorer URL"
    )
    
    contract_address = st.text_input(
        "Contract Address",
        value="0x4F83314E4752E7f732210D043B218B269989a181",
        help="Smart contract address to analyze"
    )
    
    # Contract type selector
    contract_type = st.radio(
        "Contract Type",
        options=["Token Contract", "General Contract"],
        index=0,
        help="Choose based on your contract type"
    )
    
    if contract_type == "Token Contract":
        token_type = st.selectbox(
            "Token Type",
            options=["ERC-721", "ERC-20", "ERC-1155"],
            index=0,
            help="Type of token contract"
        )
        st.info("📌 Will fetch all token transfers (mints, transfers, burns)")
    else:
        st.info("📌 Will fetch all contract transactions")
        st.warning("⚠️ Note: General contract mode tracks transaction senders.")
    
    app_name = st.text_input(
        "App Name",
        value="Token Tails Mystery Box",
        help="Name of the application for reporting"
    )
    
    st.divider()
    
    st.markdown("### 📖 How to Use")
    if contract_type == "Token Contract":
        st.markdown("""
        1. Enter your token contract address
        2. Select token type
        3. Click **Fetch Data**
        4. View analytics & download CSV
        """)
    else:
        st.markdown("""
        1. Enter your contract address
        2. Click **Fetch Data**
        3. Will track all transaction senders
        4. View analytics & download CSV
        """)

# Initialize session state
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False

# Main action button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    fetch_button = st.button("🚀 Fetch Data from Blockscout", type="primary", use_container_width=True)

if fetch_button:
    with st.spinner("Fetching data from Blockscout..."):
        try:
            wallets = set()
            wallet_data = []
            mau_by_month = defaultdict(set)
            dau_by_date = defaultdict(set)
            
            if contract_type == "Token Contract":
                # Fetch token transfers
                api_url = f"{blockscout_url}/api/v2/tokens/{contract_address}/transfers"
                if token_type:
                    api_url += f"?type={token_type}"
                
                st.info(f"📡 Fetching from: \`{api_url}\`")
                
                response = requests.get(api_url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                transfers = data.get('items', [])
                
                if len(transfers) == 0:
                    st.warning("⚠️ No transfers found for this contract")
                    st.info("Check if the contract address is correct and has activity")
                else:
                    st.success(f"✅ Found {len(transfers)} transfers!")
                    
                    for transfer in transfers:
                        # Get recipient wallet
                        wallet = transfer['to']['hash']
                        timestamp_str = transfer['timestamp']
                        
                        # Parse timestamp
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        month = dt.strftime('%Y-%m')
                        date = dt.date()
                        
                        # Track unique wallets
                        wallets.add(wallet)
                        mau_by_month[month].add(wallet)
                        dau_by_date[date].add(wallet)
                        
                        # Store detailed data
                        wallet_data.append({
                            'wallet_address': wallet,
                            'timestamp': dt,
                            'date': date,
                            'month': month,
                            'block_number': transfer.get('block_number', 'N/A'),
                            'tx_hash': transfer.get('transaction_hash', 'N/A'),
                            'from_address': transfer['from']['hash'],
                            'method': transfer.get('method', 'N/A')
                        })
            
            else:
                # Fetch general contract transactions
                api_url = f"{blockscout_url}/api/v2/addresses/{contract_address}/transactions"
                
                st.info(f"📡 Fetching from: \`{api_url}\`")
                
                response = requests.get(api_url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                transactions = data.get('items', [])
                
                if len(transactions) == 0:
                    st.warning("⚠️ No transactions found for this contract")
                    st.info("Check if the contract address is correct and has activity")
                else:
                    st.success(f"✅ Found {len(transactions)} transactions!")
                    
                    for tx in transactions:
                        # Get transaction sender (the user who interacted)
                        wallet = tx['from']['hash']
                        timestamp_str = tx['timestamp']
                        
                        # Parse timestamp
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        month = dt.strftime('%Y-%m')
                        date = dt.date()
                        
                        # Track unique wallets
                        wallets.add(wallet)
                        mau_by_month[month].add(wallet)
                        dau_by_date[date].add(wallet)
                        
                        # Store detailed data
                        wallet_data.append({
                            'wallet_address': wallet,
                            'timestamp': dt,
                            'date': date,
                            'month': month,
                            'block_number': tx.get('block', 'N/A'),
                            'tx_hash': tx.get('hash', 'N/A'),
                            'from_address': wallet,
                            'method': tx.get('method', 'N/A'),
                            'tx_type': tx.get('tx_types', ['contract_call'])[0] if tx.get('tx_types') else 'contract_call'
                        })
            
            if len(wallet_data) > 0:
                # Create DataFrames
                raw_df = pd.DataFrame(wallet_data)
                
                # MAU DataFrame
                mau_data = []
                for month, users in sorted(mau_by_month.items()):
                    mau_data.append({
                        'month': month,
                        'app_name': app_name,
                        'mau': len(users)
                    })
                mau_df = pd.DataFrame(mau_data)
                
                # DAU DataFrame
                dau_data = []
                for date, users in sorted(dau_by_date.items()):
                    dau_data.append({
                        'date': date,
                        'app_name': app_name,
                        'dau': len(users)
                    })
                dau_df = pd.DataFrame(dau_data)
                
                # Unique wallets DataFrame
                unique_wallets_df = pd.DataFrame({
                    'wallet_address': sorted(wallets)
                })
                
                # Store in session state
                st.session_state.mau_df = mau_df
                st.session_state.dau_df = dau_df
                st.session_state.unique_wallets_df = unique_wallets_df
                st.session_state.raw_df = raw_df
                st.session_state.data_fetched = True
                st.session_state.app_name = app_name
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network Error: {e}")
            st.info("Check your internet connection or Blockscout URL")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.info("Make sure the contract address and Blockscout URL are correct")

# Display results
if st.session_state.data_fetched:
    st.divider()
    
    # Key Metrics
    st.header("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Events",
            len(st.session_state.raw_df),
            help="Total number of interactions"
        )
    
    with col2:
        st.metric(
            "Unique Wallets",
            len(st.session_state.unique_wallets_df),
            help="Total unique wallet addresses"
        )
    
    with col3:
        if len(st.session_state.mau_df) > 0:
            latest_mau = st.session_state.mau_df.iloc[-1]['mau']
            st.metric(
                "Latest MAU",
                latest_mau,
                help="Most recent month's active users"
            )
    
    with col4:
        if len(st.session_state.dau_df) > 0:
            avg_dau = int(st.session_state.dau_df['dau'].mean())
            st.metric(
                "Avg DAU",
                avg_dau,
                help="Average daily active users"
            )
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 MAU", "📊 DAU", "👤 Wallets", "💾 Export"])
    
    with tab1:
        st.subheader("Monthly Active Users (MAU)")
        
        if len(st.session_state.mau_df) > 0:
            # Bar chart
            fig_mau = px.bar(
                st.session_state.mau_df,
                x='month',
                y='mau',
                text='mau',
                title=f'Monthly Active Users - {st.session_state.app_name}',
                labels={'mau': 'Active Users', 'month': 'Month'},
                color='mau',
                color_continuous_scale='Blues'
            )
            fig_mau.update_traces(textposition='outside')
            fig_mau.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_mau, use_container_width=True)
            
            # Data table
            st.dataframe(
                st.session_state.mau_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No MAU data available")
    
    with tab2:
        st.subheader("Daily Active Users (DAU)")
        
        if len(st.session_state.dau_df) > 0:
            # Line chart
            fig_dau = px.line(
                st.session_state.dau_df,
                x='date',
                y='dau',
                title=f'Daily Active Users - {st.session_state.app_name}',
                labels={'dau': 'Active Users', 'date': 'Date'},
                markers=True
            )
            fig_dau.update_layout(height=400)
            st.plotly_chart(fig_dau, use_container_width=True)
            
            # Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Max DAU", st.session_state.dau_df['dau'].max())
            with col2:
                st.metric("Min DAU", st.session_state.dau_df['dau'].min())
            with col3:
                st.metric("Median DAU", int(st.session_state.dau_df['dau'].median()))
            
            # Data table
            with st.expander("📋 View DAU Data Table"):
                st.dataframe(
                    st.session_state.dau_df,
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No DAU data available")
    
    with tab3:
        st.subheader("Unique Wallets")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(
                st.session_state.unique_wallets_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        
        with col2:
            st.markdown("### 📊 Summary")
            st.metric("Total Unique Wallets", len(st.session_state.unique_wallets_df))
            
            # Quick download
            csv_wallets = st.session_state.unique_wallets_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Wallets CSV",
                data=csv_wallets,
                file_name=f"unique_wallets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with tab4:
        st.subheader("💾 Export Data")
        
        st.markdown("Download your analytics data in various formats:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📄 CSV Exports")
            
            # Unique Wallets CSV
            csv_wallets = st.session_state.unique_wallets_df.to_csv(index=False)
            st.download_button(
                label="📥 Unique Wallets CSV",
                data=csv_wallets,
                file_name=f"unique_wallets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # MAU CSV
            csv_mau = st.session_state.mau_df.to_csv(index=False)
            st.download_button(
                label="📥 MAU Data CSV",
                data=csv_mau,
                file_name=f"mau_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # DAU CSV
            csv_dau = st.session_state.dau_df.to_csv(index=False)
            st.download_button(
                label="📥 DAU Data CSV",
                data=csv_dau,
                file_name=f"dau_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.markdown("#### 📊 Complete Excel File")
            st.info("Includes all data in separate sheets")
            
            if st.button("🔨 Generate Excel File", use_container_width=True):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    st.session_state.unique_wallets_df.to_excel(writer, index=False, sheet_name='Unique Wallets')
                    st.session_state.mau_df.to_excel(writer, index=False, sheet_name='MAU')
                    st.session_state.dau_df.to_excel(writer, index=False, sheet_name='DAU')
                    st.session_state.raw_df.to_excel(writer, index=False, sheet_name='Raw Data')
                
                buffer.seek(0)
                
                st.download_button(
                    label="💾 Download Excel",
                    data=buffer,
                    file_name=f"camp_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
        
        with col3:
            st.markdown("#### 🔍 Raw Data")
            st.info(f"{len(st.session_state.raw_df)} total records")
            
            csv_raw = st.session_state.raw_df.to_csv(index=False)
            st.download_button(
                label="📥 Raw Data CSV",
                data=csv_raw,
                file_name=f"raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Preview raw data
        with st.expander("👁️ Preview Raw Data"):
            st.dataframe(
                st.session_state.raw_df.head(20),
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"Showing first 20 of {len(st.session_state.raw_df)} records")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>🏕️ Camp Network MAU Dashboard</strong></p>
    <p>Powered by Blockscout API | Built with Streamlit</p>
    <p style='font-size: 0.8rem;'>Works for tokens & general contracts • Instant data • Real analytics</p>
</div>
""", unsafe_allow_html=True)
