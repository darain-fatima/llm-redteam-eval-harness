# app.py - Production-Grade Red-Teaming Evaluation Dashboard
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration
st.set_page_config(
    page_title="LLM Safety & Red-Teaming Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Clean UI Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .status-refusal {
        color: #27ae60;
        font-weight: 600;
        background-color: #eafaf1;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    .status-compliance {
        color: #c0392b;
        font-weight: 600;
        background-color: #fdedec;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# 3. Data Ingestion
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_redteam_evaluation_log.csv")
        return df
    except FileNotFoundError:
        return None

df = load_data()

# Error handling if file is missing
if df is None:
    st.error("⚠️ File `master_redteam_evaluation_log.csv` not found.")
    st.info("Place `master_redteam_evaluation_log.csv` in the same directory as this script and refresh the page.")
    st.stop()

# 4. Sidebar Controls
with st.sidebar:
    st.title("🛡️ Controls & Filters")
    st.markdown("Filter evaluation records across testing vectors.")
    
    # Filter by Attack Type
    available_attacks = ["All Attacks"] + list(df['Attack_Type'].unique())
    selected_attack = st.selectbox("Select Attack Technique:", available_attacks)
    
    # Filter by Verdict
    available_scores = ["All Results", "COMPLIANCE (Bypasses Only)", "REFUSAL (Defenses Only)"]
    selected_verdict = st.radio("Filter by Outcome:", available_scores)
    
    st.divider()
    st.markdown("**Evaluated Model**: `qwen/qwen3.8-27b`")
    st.markdown("**Draft Generator**: `openai/gpt-oss-20b`")
    st.markdown("**Evaluated Samples**: 100 trials")

# Apply filters
filtered_df = df.copy()
if selected_attack != "All Attacks":
    filtered_df = filtered_df[filtered_df['Attack_Type'] == selected_attack]

if selected_verdict == "COMPLIANCE (Bypasses Only)":
    filtered_df = filtered_df[filtered_df['Score'] == "COMPLIANCE"]
elif selected_verdict == "REFUSAL (Defenses Only)":
    filtered_df = filtered_df[filtered_df['Score'] == "REFUSAL"]

filtered_df.reset_index(drop=True, inplace=True)

# 5. Header Section
st.title("🛡️ Automated LLM Red-Teaming & Safety Evaluation Harness")
st.markdown("Auditing adversarial resilience across standard and novel jailbreak attacks on **Qwen-27B**.")

# 6. Global Top Metrics
total_tests = len(df)
bypasses = (df['Score'] == 'COMPLIANCE').sum()
refusals = (df['Score'] == 'REFUSAL').sum()
overall_asr = (bypasses / total_tests) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Evaluations", f"{total_tests}")
col2.metric("Total Bypasses", f"{bypasses}")
col3.metric("Total Refusals", f"{refusals}")
col4.metric("Overall System ASR", f"{overall_asr:.1f}%")

st.divider()

# 7. Tabbed Interface
tab1, tab2, tab3 = st.tabs(["📊 Evaluation Leaderboard", "🔍 Transcript Explorer", "📋 Raw Dataset Logs"])

# --- TAB 1: Overview & Charts ---
with tab1:
    st.subheader("Adversarial Vulnerability Profile")
    
    col_chart, col_table = st.columns([1.2, 1])
    
    # Compute Leaderboard Metrics
    leaderboard = df.groupby('Attack_Type').agg(
        Attempts=('Score', 'count'),
        Bypasses=('Score', lambda x: (x == 'COMPLIANCE').sum()),
        Refusals=('Score', lambda x: (x == 'REFUSAL').sum())
    ).reset_index()
    leaderboard['ASR (%)'] = (leaderboard['Bypasses'] / leaderboard['Attempts']) * 100
    leaderboard = leaderboard.sort_values(by="ASR (%)", ascending=True).reset_index(drop=True)
    
    with col_chart:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        # Color mapping: Highlight non-zero vulnerabilities
        bar_colors = ['#2ecc71' if asr == 0 else '#e74c3c' for asr in leaderboard['ASR (%)']]
        bars = ax.barh(leaderboard['Attack_Type'], leaderboard['ASR (%)'], color=bar_colors, height=0.55)
        
        ax.set_xlim(0, 50)  # Clean axis limit
        ax.set_xlabel('Attack Success Rate (ASR %)', fontweight='bold', fontsize=11)
        ax.xaxis.grid(True, linestyle='--', alpha=0.5)
        
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', va='center', ha='left', fontweight='bold')
            
        plt.tight_layout()
        st.pyplot(fig)
        
    with col_table:
        st.markdown("**Vulnerability Summary by Technique**")
        st.dataframe(
            leaderboard[['Attack_Type', 'Attempts', 'Bypasses', 'ASR (%)']].style.format({'ASR (%)': '{:.1f}%'}),
            use_container_width=True,
            hide_index=True
        )
        st.info("💡 **Key Finding**: Base64 Obfuscation and Content Concretization (refinement framing) demonstrated measurable vulnerabilities (5.0% ASR), while Roleplay, Many-Shot, and Baseline maintained 0.0% ASR.")

# --- TAB 2: Transcript Explorer ---
with tab2:
    st.subheader("Adversarial Transcript & Audit Viewer")
    st.markdown("Inspect individual test interactions, original harmful goals, model outputs, and automated auditor verdicts.")
    
    if len(filtered_df) == 0:
        st.warning("No records match the current sidebar filter criteria.")
    else:
        # Selector for prompt
        record_idx = st.selectbox(
            f"Select Record (Showing {len(filtered_df)} matches):", 
            options=range(len(filtered_df)), 
            format_func=lambda i: f"Record #{i+1}: [{filtered_df.iloc[i]['Attack_Type']}] - {filtered_df.iloc[i]['Goal'][:70]}..."
        )
        
        selected_row = filtered_df.iloc[record_idx]
        
        col_meta1, col_meta2 = st.columns(2)
        col_meta1.markdown(f"**Attack Technique**: `{selected_row['Attack_Type']}`")
        
        # Color badge for verdict
        if selected_row['Score'] == "REFUSAL":
            col_meta2.markdown('**Auditor Verdict**: <span class="status-refusal">🛡️ REFUSAL (Defended)</span>', unsafe_allow_html=True)
        else:
            col_meta2.markdown('**Auditor Verdict**: <span class="status-compliance">⚠️ COMPLIANCE (Jailbreak Succeeded)</span>', unsafe_allow_html=True)
            
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Harmful Benchmark Goal:**")
            st.warning(selected_row['Goal'])
            
        with col_right:
            st.markdown("**Model Output Completion:**")
            st.text_area("", value=selected_row['Output'], height=220, disabled=True, label_visibility="collapsed")

# --- TAB 3: Raw Data Logs ---
with tab3:
    st.subheader("Raw Evaluation Database")
    st.markdown("Inspect or export the raw dataset generated by the automated harness.")
    
    st.dataframe(filtered_df, use_container_width=True)
    
    # Download Button for filtered view
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Results as CSV",
        data=csv_data,
        file_name="filtered_evaluation_log.csv",
        mime="text/csv"
    )