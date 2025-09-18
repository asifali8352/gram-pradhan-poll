import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import hashlib
import re

# Set page configuration
st.set_page_config(
    page_title="Gram Pradhan Opinion Poll",
    page_icon="🗳️",
    layout="wide"
)

# CSS FILE को LOAD करने का function
def load_css(file_name):
    """Load CSS from external file"""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("CSS file not found! Please make sure style.css exists in the same directory.")

# CSS FILE को LOAD करें
load_css('style.css')

# Initialize data file
DATA_FILE = "data/votes.csv"

def create_data_folder():
    """Create data folder if it doesn't exist"""
    if not os.path.exists("data"):
        os.makedirs("data")

def initialize_votes_csv():
    """Create votes.csv with proper structure if it doesn't exist"""
    create_data_folder()
    if not os.path.exists(DATA_FILE):
        # Create CSV with proper columns
        initial_data = {
            'voter_id': [],
            'voter_name': [],
            'voter_phone': [],
            'candidate': [],
            'timestamp': []
        }
        df = pd.DataFrame(initial_data)
        df.to_csv(DATA_FILE, index=False)
        return df
    else:
        return pd.read_csv(DATA_FILE)

def load_votes():
    """Load votes from CSV file"""
    df = initialize_votes_csv()
    # Ensure voter_phone column is treated as string to prevent type issues
    if not df.empty:
        df['voter_phone'] = df['voter_phone'].astype(str)
    return df

def save_vote(voter_id, voter_name, voter_phone, candidate):
    """Save a vote to CSV file"""
    new_vote = {
        'voter_id': voter_id,
        'voter_name': voter_name,
        'voter_phone': str(voter_phone),  # Ensure phone is stored as string
        'candidate': candidate,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Load existing votes
    votes_df = load_votes()
    
    # Add new vote
    new_row = pd.DataFrame([new_vote])
    votes_df = pd.concat([votes_df, new_row], ignore_index=True)
    
    # Save to file
    votes_df.to_csv(DATA_FILE, index=False)
    
    return True

def has_voted(voter_phone):
    """Check if voter has already voted using phone number - IMPROVED VERSION"""
    try:
        votes_df = load_votes()
        
        # If CSV is empty, no one has voted
        if votes_df.empty or len(votes_df) == 0:
            return False
        
        # Clean the phone number for comparison
        clean_phone = str(voter_phone).strip()
        
        # Check if this phone number exists in the CSV
        phone_exists = votes_df['voter_phone'].astype(str).str.strip().isin([clean_phone]).any()
        
        return phone_exists
        
    except Exception as e:
        st.error(f"Error checking vote status: {e}")
        return False

def validate_phone(phone):
    """Validate Indian phone number - IMPROVED VERSION"""
    if not phone:
        return False
    
    # Clean the phone number
    phone = str(phone).strip()
    
    # Check if it's exactly 10 digits and starts with 6,7,8,9
    if len(phone) == 10 and phone.isdigit() and phone[0] in ['6', '7', '8', '9']:
        return True
    
    return False

def validate_name(name):
    """Validate name - IMPROVED VERSION"""
    if not name:
        return False
    
    name = name.strip()
    
    # Name should be at least 2 characters and not just numbers
    if len(name) >= 2 and not name.isdigit():
        return True
    
    return False

def calculate_results():
    """Calculate voting results"""
    votes_df = load_votes()
    
    if votes_df.empty or len(votes_df) == 0:
        return {}, 0
    
    # Count votes for each candidate
    vote_counts = votes_df['candidate'].value_counts()
    total_votes = len(votes_df)
    
    # Calculate percentages
    results = {}
    for candidate, count in vote_counts.items():
        percentage = (count / total_votes) * 100
        results[candidate] = {
            'votes': count,
            'percentage': round(percentage, 1)
        }
    
    return results, total_votes

# Define candidates list
CANDIDATES = [
    "हारुन चौधरी",
    "मौमीन कुरैशी", 
    "आज़ाद प्रधान",
    "राशिद चौधरी",
    "साजिद मामा और मारुफ़",
    "पुनीत कुमार शर्मा",
    "मांगेराम",
    "साबिर मुखिया",
    "डॉक्टर रहीश",
    "इंतजार बेट्री वाला",
    "इनमे से कोई नहीं"
]

# Initialize session state for preventing double clicks
if 'voted' not in st.session_state:
    st.session_state.voted = False
if 'processing_vote' not in st.session_state:
    st.session_state.processing_vote = False
if 'last_voted_phone' not in st.session_state:
    st.session_state.last_voted_phone = None

# App title
st.title("🗳️ Tilbegumpur Gram Pradhan Opinion Poll")
st.markdown("### **बेहतर नेता, बेहतर गांव****सही प्रधान चुनें, गांव का भला करें**")

# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🗳️ अपना वोट दें (Cast Your Vote)")
    
    if not st.session_state.voted:
        # Step 1: Show candidates as radio buttons
        st.markdown("#### 👥 उम्मीदवार चुनें (Choose Candidate)")
        selected_candidate = st.radio(
            "अपना पसंदीदा उम्मीदवार चुनें:",
            CANDIDATES,
            index=None,
            key="candidate_selection"
        )
        
        if selected_candidate:
            st.success(f"✅ आपने चुना: **{selected_candidate}**")
            
            # Step 2: Get voter details
            st.markdown("#### 👤 आपकी जानकारी (Your Details)")
            
            voter_name = st.text_input(
                "📝 अपना पूरा नाम लिखें:",
                placeholder="उदाहरण: राजेश कुमार",
                key="voter_name"
            )
            
            voter_phone = st.text_input(
                "📱 मोबाइल नंबर (10 अंक):",
                placeholder="9876543210",
                max_chars=10,
                key="voter_phone"
            )
            
            # Step 3: Submit button with improved logic
            submit_disabled = st.session_state.processing_vote
            
            if st.button(
                "✅ Submit Your Vote", 
                type="primary", 
                use_container_width=True, 
                disabled=submit_disabled,
                key="submit_vote_btn"
            ):
                
                # Set processing flag to prevent double clicks
                st.session_state.processing_vote = True
                
                # Validation
                validation_passed = True
                
                if not validate_name(voter_name):
                    st.error("⚠️ कृपया सही नाम दर्ज करें! (Please enter a valid name)")
                    validation_passed = False
                
                if not validate_phone(voter_phone):
                    st.error("⚠️ कृपया सही 10 अंकों का मोबाइल नंबर दर्ज करें! (Please enter valid 10-digit mobile number)")
                    validation_passed = False
                
                # Check for duplicate voting - IMPROVED CHECK
                if validation_passed and has_voted(voter_phone):
                    st.error("⚠️ इस मोबाइल नंबर से पहले ही वोट दिया जा चुका है!")
                    st.error("❌ This mobile number has already been used to vote!")
                    st.error(f"📱 Duplicate phone number: {voter_phone}")
                    validation_passed = False
                
                # If all validations pass, save the vote
                if validation_passed:
                    try:
                        # Create unique voter ID
                        voter_id = hashlib.md5(f"{voter_name}{voter_phone}{datetime.now()}".encode()).hexdigest()[:8]
                        
                        # Save vote
                        success = save_vote(voter_id, voter_name.strip(), voter_phone, selected_candidate)
                        
                        if success:
                            # Update session state
                            st.session_state.voted = True
                            st.session_state.last_voted_phone = voter_phone
                            st.success("🎉 वोट सफलतापूर्वक सबमिट हो गया!")
                            st.balloons()
                            
                    except Exception as e:
                        st.error(f"❌ Error saving vote: {e}")
                
                # Reset processing flag
                st.session_state.processing_vote = False
        else:
            st.info("👆 पहले कोई उम्मीदवार चुनें (Please select a candidate first)")
    
    else:
        # Show success message
        st.success("🎉 धन्यवाद! आपका वोट सफलतापूর्वक दर्ज हो गया!")
        st.success("Thank you! Your vote has been recorded successfully!")
        
        if st.session_state.last_voted_phone:
            st.info(f"📱 आपका पंजीकृत नंबर: {st.session_state.last_voted_phone}")
        
        # Reset button for demo purposes only
        if st.button("🔄 Reset (Demo केवल)", type="secondary"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

with col2:
    st.header("📊 Live Results")
    
    # Calculate and show results
    results, total_votes = calculate_results()
    
    if results:
        # Show total votes
        st.metric("🗳️ कुल वोट (Total Votes)", total_votes)
        
        # Create pie chart
        candidates = list(results.keys())
        percentages = [results[candidate]['percentage'] for candidate in candidates]
        
        fig = px.pie(
            values=percentages,
            names=candidates,
            title="वोटिंग परिणाम (Voting Results)",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True, legend=dict(orientation="v"))
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed results
        st.markdown("#### 📈 विस्तृत परिणाम (Detailed Results)")
        for candidate, data in results.items():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**{candidate}**")
            with col_b:
                st.write(f"**{data['percentage']}%** ({data['votes']} votes)")
            
    else:
        st.info("🗳️ अभी तक कोई वोट नहीं आया!")
        st.info("No votes cast yet!")

# Footer with rules and statistics
st.markdown("---")

footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    st.markdown("### 📋 मतदान नियम (Voting Rules)")
    st.markdown("""
    - **एक मोबाइल नंबर = एक वोट का अधिकार** (One phone number = One vote)
    - सभी जानकारी सुरक्षित और गुप्त है (All information is secure and private)
    - परिणाम तुरंत अपडेट होते हैं (Results update instantly)
    - सिर्फ भारतीय मोबाइल नंबर से वोट कर सकते हैं (Only Indian mobile numbers accepted)
    """)

with footer_col2:
    st.markdown("### 📊 आंकड़े (Statistics)")
    votes_df = load_votes()
    
    if not votes_df.empty:
        total_votes = len(votes_df)
        latest_vote_time = votes_df.iloc[-1]['timestamp'] if len(votes_df) > 0 else "No votes"
        
        st.metric("कुल वोट", total_votes)
        st.metric("अंतिम वोट समय", latest_vote_time.split(' ')[1][:5] if latest_vote_time != "No votes" else "N/A")
    else:
        st.metric("कुल वोट", 0)
        st.metric("अंतिम वोट समय", "N/A")

# Admin section to view recent votes (expandable)
if not votes_df.empty and len(votes_df) > 0:
    with st.expander("📊 हाल के वोट देखें (View Recent Votes)"):
        # Show last 10 votes
        recent_votes = votes_df.tail(10)[['voter_name', 'voter_phone', 'candidate', 'timestamp']].copy()
        recent_votes.columns = ['नाम', 'फोन', 'उम्मीदवार', 'समय']
        
        # Hide phone numbers and name partially for privacy
        recent_votes['फोन'] = recent_votes['फोन'].apply(lambda x: f"{'*' * 6}{str(x)[-3:]}")
        recent_votes['नाम'] = recent_votes['नाम'].apply(lambda x: f"{'*' * 6}{str(x)[-2:]}")

        st.dataframe(recent_votes, use_container_width=True)
        
        # Show duplicate check information
        st.markdown("#### 🔍 डुप्लिकेट चेक स्टेटस")
        unique_phones = votes_df['voter_phone'].nunique()
        total_votes_count = len(votes_df)
        
        if unique_phones == total_votes_count:
            st.success(f"✅ सभी वोट अलग फोन नंबर से हैं! ({unique_phones} unique phones)")
        else:
            st.warning(f"⚠️ संभावित डुप्लिकेट मिले: {total_votes_count - unique_phones}")
