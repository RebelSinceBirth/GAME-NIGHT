import streamlit as st
import random
from datetime import datetime
from PIL import Image, ImageDraw
import io
import base64
import json
import os
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Raymond & Wife's Game Night 🎮",
    page_icon="🎮",
    layout="wide"
)

# ===== ANALYTICS TRACKING =====
def track_visit():
    """Simple visit counter"""
    counter_file = Path("visit_counter.json")
    
    if counter_file.exists():
        with open(counter_file, 'r') as f:
            data = json.load(f)
    else:
        data = {
            'total_visits': 0,
            'unique_sessions': [],
            'game_plays': {}
        }
    
    # Track session
    if 'session_id' not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
        
        # Only count as new visit if it's a new session
        if st.session_state.session_id not in data['unique_sessions']:
            data['total_visits'] += 1
            data['unique_sessions'].append(st.session_state.session_id)
            
            # Keep only last 1000 sessions to avoid file bloat
            if len(data['unique_sessions']) > 1000:
                data['unique_sessions'] = data['unique_sessions'][-1000:]
            
            # Save updated data
            with open(counter_file, 'w') as f:
                json.dump(data, f)
    
    return data['total_visits']

def track_game_play(game_name):
    """Track which games are being played"""
    counter_file = Path("visit_counter.json")
    
    if counter_file.exists():
        with open(counter_file, 'r') as f:
            data = json.load(f)
    else:
        data = {'total_visits': 0, 'unique_sessions': [], 'game_plays': {}}
    
    if game_name not in data['game_plays']:
        data['game_plays'][game_name] = 0
    
    data['game_plays'][game_name] += 1
    
    with open(counter_file, 'w') as f:
        json.dump(data, f)

# Google Analytics Integration
# To use: Replace 'G-XXXXXXXXXX' with your actual Google Analytics Measurement ID
GOOGLE_ANALYTICS_ID = "G-0ZXQ2C7P09"  # Replace this with your GA4 Measurement ID

def inject_ga():
    """Inject Google Analytics tracking code"""
    if GOOGLE_ANALYTICS_ID != "G-00000000000":
        GA_JS = f"""
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{GOOGLE_ANALYTICS_ID}');
        </script>
        """
        st.components.v1.html(GA_JS, height=0)

# Track visit on app load
total_visits = track_visit()

# Inject Google Analytics
inject_ga()

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #1a1a2e;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #FF1493, #FF69B4);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 15px;
        font-size: 18px;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #FF69B4, #FF1493);
        box-shadow: 0 0 20px rgba(255, 20, 147, 0.8);
    }
    h1 {
        color: #FF1493;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }
    h2, h3 {
        color: #FFB6C1;
    }
    .score-box {
        background: rgba(255, 20, 147, 0.1);
        border: 2px solid #FF1493;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    .game-card {
        background: rgba(255, 182, 193, 0.1);
        border: 2px solid #FFB6C1;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .game-card:hover {
        background: rgba(255, 182, 193, 0.2);
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'game_mode' not in st.session_state:
    st.session_state.game_mode = None
if 'player1_name' not in st.session_state:
    st.session_state.player1_name = "Raymond"
if 'player2_name' not in st.session_state:
    st.session_state.player2_name = "Wife"
if 'overall_score' not in st.session_state:
    st.session_state.overall_score = {st.session_state.player1_name: 0, st.session_state.player2_name: 0}

# ===== TRIVIA QUESTIONS =====
TRIVIA_QUESTIONS = {
    "Movies": [
        {"q": "What 1997 movie features Leonardo DiCaprio saying 'I'm the king of the world!'?", "a": ["Titanic", "titanic"], "hint": "It's about a ship..."},
        {"q": "Which movie features the line 'Nobody puts Baby in a corner'?", "a": ["Dirty Dancing", "dirty dancing"], "hint": "Patrick Swayze dance movie"},
        {"q": "In Mean Girls, what day do they wear pink?", "a": ["Wednesday", "wednesday"], "hint": "Middle of the week!"},
        {"q": "What movie has the song 'Let It Go'?", "a": ["Frozen", "frozen"], "hint": "Disney ice princess"},
        {"q": "Who plays Iron Man in the Marvel movies?", "a": ["Robert Downey Jr", "robert downey jr", "rdj", "Robert Downey Junior"], "hint": "RDJ"},
        {"q": "What's the name of the kingdom in Tangled?", "a": ["Corona", "corona"], "hint": "Same name as a beer or a virus!"},
        {"q": "In The Notebook, where do Noah and Allie reunite?", "a": ["plantation", "the plantation", "Noah's house", "his house"], "hint": "A big house Noah restored"},
        {"q": "What movie features Cher Horowitz and 'As if!'?", "a": ["Clueless", "clueless"], "hint": "Alicia Silverstone 90s classic"},
    ],
    "TV Shows": [
        {"q": "What's the name of the coffee shop in Friends?", "a": ["Central Perk", "central perk"], "hint": "Central ___"},
        {"q": "In The Office, what's the name of the company?", "a": ["Dunder Mifflin", "dunder mifflin"], "hint": "Dunder ___"},
        {"q": "What town do the Gilmore Girls live in?", "a": ["Stars Hollow", "stars hollow"], "hint": "Stars ___"},
        {"q": "In Grey's Anatomy, what's the name of the hospital?", "a": ["Seattle Grace", "seattle grace", "Grey Sloan Memorial", "grey sloan memorial"], "hint": "Seattle ___"},
        {"q": "What's the name of Tony Soprano's strip club?", "a": ["Bada Bing", "bada bing", "The Bada Bing"], "hint": "Bada ___!"},
        {"q": "In Stranger Things, what's Eleven's favorite food?", "a": ["Eggos", "eggos", "waffles", "Eggo waffles"], "hint": "Leggo my ___"},
        {"q": "What's the name of the bar in How I Met Your Mother?", "a": ["MacLaren's", "maclarens", "McLaren's"], "hint": "Mac___'s"},
        {"q": "In Breaking Bad, what alias does Walter White use?", "a": ["Heisenberg", "heisenberg"], "hint": "Famous physicist"},
    ],
    "Reality TV": [
        {"q": "Who was the first Black Bachelor?", "a": ["Matt James", "matt james"], "hint": "First name Matt"},
        {"q": "What city are the Real Housewives of Beverly Hills from?", "a": ["Beverly Hills", "beverly hills", "LA", "Los Angeles"], "hint": "It's in the name!"},
        {"q": "On The Bachelor, what does the host say? 'This is the ___ rose tonight'", "a": ["final", "Final"], "hint": "The last one!"},
        {"q": "What show has the tagline 'Expect the Unexpected'?", "a": ["Big Brother", "big brother"], "hint": "BB"},
        {"q": "Who was the first Bachelorette?", "a": ["Trista Sutter", "trista sutter", "Trista Rehn", "trista"], "hint": "First name Trista"},
        {"q": "What do contestants say in Survivor before voting someone out?", "a": ["The tribe has spoken", "tribe has spoken"], "hint": "The ___ has spoken"},
        {"q": "Which Real Housewife flipped a table at dinner?", "a": ["Teresa Giudice", "teresa giudice", "Teresa", "teresa"], "hint": "Teresa from New Jersey"},
        {"q": "What's the name of the mansion in Love Island?", "a": ["Love Island Villa", "the villa", "villa"], "hint": "The ___"},
        {"q": "On Keeping Up with the Kardashians, what's Kris Jenner's catchphrase?", "a": ["You're doing amazing sweetie", "youre doing amazing sweetie", "doing amazing sweetie"], "hint": "You're doing ___"},
        {"q": "Which Bachelor couple got married in a TV wedding in 2003?", "a": ["Trista and Ryan", "trista and ryan", "Trista Sutter"], "hint": "First Bachelorette"},
    ]
}

# ===== CONNECT FOUR =====
def init_connect_four():
    st.session_state.c4_board = [[' ' for _ in range(7)] for _ in range(6)]
    st.session_state.c4_current_player = 1
    st.session_state.c4_game_over = False
    st.session_state.c4_winner = None
    st.session_state.c4_score = {st.session_state.player1_name: 0, st.session_state.player2_name: 0}

def check_winner_c4(board):
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if board[row][col] != ' ' and board[row][col] == board[row][col+1] == board[row][col+2] == board[row][col+3]:
                return int(board[row][col])
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if board[row][col] != ' ' and board[row][col] == board[row+1][col] == board[row+2][col] == board[row+3][col]:
                return int(board[row][col])
    
    # Check diagonal (down-right)
    for row in range(3):
        for col in range(4):
            if board[row][col] != ' ' and board[row][col] == board[row+1][col+1] == board[row+2][col+2] == board[row+3][col+3]:
                return int(board[row][col])
    
    # Check diagonal (down-left)
    for row in range(3):
        for col in range(3, 7):
            if board[row][col] != ' ' and board[row][col] == board[row+1][col-1] == board[row+2][col-2] == board[row+3][col-3]:
                return int(board[row][col])
    
    return None

def drop_piece_c4(col, player):
    board = st.session_state.c4_board
    for row in range(5, -1, -1):
        if board[row][col] == ' ':
            board[row][col] = str(player)
            return True
    return False

# ===== CHESS TUTORIAL =====
def init_chess():
    st.session_state.chess_lesson = 1
    st.session_state.chess_progress = []

# ===== 20 QUESTIONS =====
def init_20q():
    st.session_state.q20_questions_asked = []
    st.session_state.q20_guesses = []
    st.session_state.q20_current_thinker = st.session_state.player1_name
    st.session_state.q20_game_active = True

# ===== HIDDEN OBJECTS =====
def init_hidden_objects():
    if 'ho_score' not in st.session_state:
        st.session_state.ho_score = {st.session_state.player1_name: 0, st.session_state.player2_name: 0}
    if 'ho_current_round' not in st.session_state:
        st.session_state.ho_current_round = 1
    if 'ho_items_to_find' not in st.session_state:
        st.session_state.ho_items_to_find = []
    if 'ho_found_items' not in st.session_state:
        st.session_state.ho_found_items = []

# ===== TRIVIA GAME =====
def init_trivia():
    if 'trivia_score' not in st.session_state:
        st.session_state.trivia_score = {st.session_state.player1_name: 0, st.session_state.player2_name: 0}
    if 'trivia_current_question' not in st.session_state:
        st.session_state.trivia_current_question = None
    if 'trivia_current_player' not in st.session_state:
        st.session_state.trivia_current_player = st.session_state.player1_name
    if 'trivia_round' not in st.session_state:
        st.session_state.trivia_round = 1
    if 'trivia_used_questions' not in st.session_state:
        st.session_state.trivia_used_questions = []

def get_random_question(category):
    available = [q for q in TRIVIA_QUESTIONS[category] if q['q'] not in st.session_state.trivia_used_questions]
    if not available:
        st.session_state.trivia_used_questions = []
        available = TRIVIA_QUESTIONS[category]
    question = random.choice(available)
    st.session_state.trivia_used_questions.append(question['q'])
    return question

# ===== WOULD YOU RATHER =====
WYR_QUESTIONS = [
    {"q": "Would you rather have a rewind button or a pause button for your life?", "theme": "Life"},
    {"q": "Would you rather always have to sing instead of speak or dance everywhere you go?", "theme": "Silly"},
    {"q": "Would you rather live in a treehouse or a houseboat?", "theme": "Living"},
    {"q": "Would you rather have unlimited tacos for life or unlimited pizza for life?", "theme": "Food"},
    {"q": "Would you rather always know when someone is lying or get away with any lie?", "theme": "Truth"},
    {"q": "Would you rather have a pet dragon or be a dragon?", "theme": "Fantasy"},
    {"q": "Would you rather fight one horse-sized duck or 100 duck-sized horses?", "theme": "Silly"},
    {"q": "Would you rather never have to sleep or never have to eat?", "theme": "Life"},
    {"q": "Would you rather have to wear a clown wig every day or clown shoes every day?", "theme": "Silly"},
    {"q": "Would you rather live without music or live without movies?", "theme": "Entertainment"},
]

def init_wyr():
    if 'wyr_score' not in st.session_state:
        st.session_state.wyr_score = {'Same Answer': 0, 'Different Answer': 0}
    if 'wyr_current_question' not in st.session_state:
        st.session_state.wyr_current_question = random.choice(WYR_QUESTIONS)
    if 'wyr_answers' not in st.session_state:
        st.session_state.wyr_answers = {}

# ===== MAIN APP =====
def main():
    st.title("🎮 Raymond & Wife's Epic Game Night 🎮")
    st.markdown("---")
    
    # Sidebar for names and overall score
    with st.sidebar:
        st.header("⚙️ Setup")
        st.session_state.player1_name = st.text_input("Player 1 Name", st.session_state.player1_name)
        st.session_state.player2_name = st.text_input("Player 2 Name", st.session_state.player2_name)
        
        st.markdown("---")
        st.header("🏆 Overall Score")
        st.markdown(f"**{st.session_state.player1_name}:** {st.session_state.overall_score.get(st.session_state.player1_name, 0)} wins")
        st.markdown(f"**{st.session_state.player2_name}:** {st.session_state.overall_score.get(st.session_state.player2_name, 0)} wins")
        
        if st.button("🔄 Reset Overall Score"):
            st.session_state.overall_score = {st.session_state.player1_name: 0, st.session_state.player2_name: 0}
            st.rerun()
        
        st.markdown("---")
        st.header("📊 Analytics")
        st.metric("Total Visitors", total_visits)
        
        # Show game popularity
        counter_file = Path("visit_counter.json")
        if counter_file.exists():
            with open(counter_file, 'r') as f:
                data = json.load(f)
                if data.get('game_plays'):
                    st.markdown("**Popular Games:**")
                    sorted_games = sorted(data['game_plays'].items(), key=lambda x: x[1], reverse=True)
                    for game, plays in sorted_games[:5]:
                        st.write(f"• {game}: {plays} plays")
    
    # Game selection menu
    if st.session_state.game_mode is None:
        st.header("Choose Your Game!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🔍 Hidden Objects")
            st.write("Find hidden items in pictures! Upload any photo and challenge each other.")
            if st.button("Play Hidden Objects", key="ho"):
                st.session_state.game_mode = "hidden_objects"
                init_hidden_objects()
                track_game_play("Hidden Objects")
                st.rerun()
            
            st.markdown("### 🧠 Trivia Challenge")
            st.write("Movies, TV Shows, Reality TV gossip! Take turns answering questions.")
            if st.button("Play Trivia", key="trivia"):
                st.session_state.game_mode = "trivia"
                init_trivia()
                track_game_play("Trivia")
                st.rerun()
        
        with col2:
            st.markdown("### 🔴 Connect Four")
            st.write("Classic Connect Four! First to get 4 in a row wins!")
            if st.button("Play Connect Four", key="c4"):
                st.session_state.game_mode = "connect_four"
                init_connect_four()
                track_game_play("Connect Four")
                st.rerun()
            
            st.markdown("### ♟️ Learn Chess")
            st.write("Raymond teaches chess! Interactive lessons for beginners.")
            if st.button("Learn Chess", key="chess"):
                st.session_state.game_mode = "chess"
                init_chess()
                track_game_play("Chess Tutorial")
                st.rerun()
        
        with col3:
            st.markdown("### ❓ 20 Questions")
            st.write("Think of something, the other person guesses! Classic game.")
            if st.button("Play 20 Questions", key="20q"):
                st.session_state.game_mode = "20_questions"
                init_20q()
                track_game_play("20 Questions")
                st.rerun()
            
            st.markdown("### 🤔 Would You Rather")
            st.write("Silly choices! See if you think alike or totally different.")
            if st.button("Play Would You Rather", key="wyr"):
                st.session_state.game_mode = "would_you_rather"
                init_wyr()
                track_game_play("Would You Rather")
                st.rerun()
    
    # Individual game screens
    elif st.session_state.game_mode == "hidden_objects":
        play_hidden_objects()
    elif st.session_state.game_mode == "trivia":
        play_trivia()
    elif st.session_state.game_mode == "connect_four":
        play_connect_four()
    elif st.session_state.game_mode == "chess":
        play_chess()
    elif st.session_state.game_mode == "20_questions":
        play_20_questions()
    elif st.session_state.game_mode == "would_you_rather":
        play_would_you_rather()

# ===== HIDDEN OBJECTS GAME =====
def play_hidden_objects():
    st.header("🔍 Hidden Objects Game")
    
    if st.button("← Back to Menu"):
        st.session_state.game_mode = None
        st.rerun()
    
    st.markdown(f"### Round {st.session_state.ho_current_round}")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{st.session_state.player1_name}'s Score", st.session_state.ho_score[st.session_state.player1_name])
    with col2:
        st.metric(f"{st.session_state.player2_name}'s Score", st.session_state.ho_score[st.session_state.player2_name])
    
    st.markdown("---")
    
    st.info("""
    **How to Play:**
    1. One player uploads a photo (could be from your room, a magazine, anything!)
    2. Tell the other person what items to find (e.g., "Find: Red cup, Book, Phone")
    3. The other person describes where they see the items
    4. Award points for correct finds!
    5. Switch roles and play again!
    """)
    
    uploaded_file = st.file_uploader("Upload a picture with hidden objects", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Find the hidden objects!", use_container_width=True)
        
        st.markdown("### What items should they find?")
        items_input = st.text_input("Enter items separated by commas", placeholder="e.g., Red cup, Book, Phone")
        
        if items_input:
            items = [item.strip() for item in items_input.split(',')]
            st.session_state.ho_items_to_find = items
            
            st.markdown(f"**Items to find:** {', '.join(items)}")
            
            st.markdown("### Check off items as they're found:")
            for item in items:
                if st.checkbox(f"Found: {item}", key=f"found_{item}"):
                    if item not in st.session_state.ho_found_items:
                        st.session_state.ho_found_items.append(item)
            
            found_count = len(st.session_state.ho_found_items)
            total_count = len(items)
            st.progress(found_count / total_count if total_count > 0 else 0)
            st.write(f"Found {found_count} out of {total_count} items!")
            
            if found_count == total_count and total_count > 0:
                st.success("🎉 All items found!")
                
                winner = st.selectbox("Who found the items?", 
                                     [st.session_state.player1_name, st.session_state.player2_name])
                
                if st.button("Award Points & Next Round"):
                    st.session_state.ho_score[winner] += found_count
                    st.session_state.overall_score[winner] += 1
                    st.session_state.ho_current_round += 1
                    st.session_state.ho_items_to_find = []
                    st.session_state.ho_found_items = []
                    st.success(f"{winner} earned {found_count} points!")
                    st.rerun()

# ===== TRIVIA GAME =====
def play_trivia():
    st.header("🧠 Trivia Challenge")
    
    if st.button("← Back to Menu"):
        st.session_state.game_mode = None
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{st.session_state.player1_name}'s Score", st.session_state.trivia_score[st.session_state.player1_name])
    with col2:
        st.metric(f"{st.session_state.player2_name}'s Score", st.session_state.trivia_score[st.session_state.player2_name])
    
    st.markdown(f"### Round {st.session_state.trivia_round}")
    st.markdown(f"**Current Player:** {st.session_state.trivia_current_player}")
    
    st.markdown("---")
    
    # Category selection
    if st.session_state.trivia_current_question is None:
        st.subheader("Choose a category:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎬 Movies", use_container_width=True):
                st.session_state.trivia_current_question = get_random_question("Movies")
                st.rerun()
        
        with col2:
            if st.button("📺 TV Shows", use_container_width=True):
                st.session_state.trivia_current_question = get_random_question("TV Shows")
                st.rerun()
        
        with col3:
            if st.button("💅 Reality TV", use_container_width=True):
                st.session_state.trivia_current_question = get_random_question("Reality TV")
                st.rerun()
    
    # Show question
    else:
        question_data = st.session_state.trivia_current_question
        st.subheader("Question:")
        st.markdown(f"### {question_data['q']}")
        
        # Answer input
        user_answer = st.text_input("Your answer:", key=f"answer_{st.session_state.trivia_round}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💡 Need a hint?"):
                st.info(f"Hint: {question_data['hint']}")
        
        with col2:
            if st.button("✅ Submit Answer"):
                correct_answers = [ans.lower().strip() for ans in question_data['a']]
                user_ans_clean = user_answer.lower().strip()
                
                if user_ans_clean in correct_answers:
                    st.success(f"🎉 Correct! {st.session_state.trivia_current_player} gets a point!")
                    st.session_state.trivia_score[st.session_state.trivia_current_player] += 1
                    st.session_state.overall_score[st.session_state.trivia_current_player] += 1
                    st.balloons()
                else:
                    st.error(f"❌ Nope! The answer was: {question_data['a'][0]}")
                
                # Switch players
                if st.session_state.trivia_current_player == st.session_state.player1_name:
                    st.session_state.trivia_current_player = st.session_state.player2_name
                else:
                    st.session_state.trivia_current_player = st.session_state.player1_name
                
                st.session_state.trivia_current_question = None
                st.session_state.trivia_round += 1
                
                if st.button("Next Question"):
                    st.rerun()

# ===== CONNECT FOUR GAME =====
def play_connect_four():
    st.header("🔴 Connect Four")
    
    if st.button("← Back to Menu"):
        st.session_state.game_mode = None
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"{st.session_state.player1_name} (🔴)", st.session_state.c4_score[st.session_state.player1_name])
    with col2:
        st.metric(f"{st.session_state.player2_name} (🟡)", st.session_state.c4_score[st.session_state.player2_name])
    
    if not st.session_state.c4_game_over:
        current_player_name = st.session_state.player1_name if st.session_state.c4_current_player == 1 else st.session_state.player2_name
        emoji = "🔴" if st.session_state.c4_current_player == 1 else "🟡"
        st.markdown(f"### {current_player_name}'s turn {emoji}")
    
    # Draw board
    st.markdown("---")
    board_html = "<div style='font-size: 40px; text-align: center;'>"
    for row in st.session_state.c4_board:
        board_html += "<div>"
        for cell in row:
            if cell == '1':
                board_html += "🔴"
            elif cell == '2':
                board_html += "🟡"
            else:
                board_html += "⚪"
        board_html += "</div>"
    board_html += "</div>"
    st.markdown(board_html, unsafe_allow_html=True)
    
    # Column buttons
    if not st.session_state.c4_game_over:
        st.markdown("### Drop your piece:")
        cols = st.columns(7)
        for i, col in enumerate(cols):
            with col:
                if st.button(f"↓ {i+1}", key=f"col_{i}", use_container_width=True):
                    if drop_piece_c4(i, st.session_state.c4_current_player):
                        winner = check_winner_c4(st.session_state.c4_board)
                        if winner:
                            st.session_state.c4_game_over = True
                            st.session_state.c4_winner = winner
                            winner_name = st.session_state.player1_name if winner == 1 else st.session_state.player2_name
                            st.session_state.c4_score[winner_name] += 1
                            st.session_state.overall_score[winner_name] += 1
                        else:
                            # Check for tie
                            if all(st.session_state.c4_board[0][c] != ' ' for c in range(7)):
                                st.session_state.c4_game_over = True
                                st.session_state.c4_winner = 0
                            else:
                                # Switch player
                                st.session_state.c4_current_player = 2 if st.session_state.c4_current_player == 1 else 1
                        st.rerun()
    
    # Game over
    if st.session_state.c4_game_over:
        if st.session_state.c4_winner == 0:
            st.info("It's a tie! 🤝")
        else:
            winner_name = st.session_state.player1_name if st.session_state.c4_winner == 1 else st.session_state.player2_name
            st.success(f"🎉 {winner_name} wins!")
            st.balloons()
        
        if st.button("🔄 Play Again"):
            init_connect_four()
            st.rerun()

# ===== CHESS TUTORIAL =====
def play_chess():
    st.header("♟️ Learn Chess with Raymond")
    
    if st.button("← Back to Menu"):
        st.session_state.game_mode = None
        st.rerun()
    
    st.info("🚧 Chess tutorial coming soon! This will be an interactive way to learn chess step by step.")
    
    lessons = [
        {"title": "Lesson 1: The Board", "desc": "Learn how the chess board is set up"},
        {"title": "Lesson 2: The Pieces", "desc": "Meet all the pieces and how they move"},
        {"title": "Lesson 3: Special Moves", "desc": "Castling, en passant, and pawn promotion"},
        {"title": "Lesson 4: Basic Strategy", "desc": "Control the center and develop pieces"},
        {"title": "Lesson 5: Checkmate Patterns", "desc": "Learn common ways to win"},
    ]
    
    for i, lesson in enumerate(lessons, 1):
        with st.expander(f"{lesson['title']} {'✅' if i <= st.session_state.chess_lesson else '🔒'}"):
            st.write(lesson['desc'])
            if i == st.session_state.chess_lesson:
                if st.button(f"Complete {lesson['title']}", key=f"lesson_{i}"):
                    st.session_state.chess_lesson += 1
                    st.success("Lesson complete! 🎉")
                    st.rerun()

# ===== 20 QUESTIONS =====
def play_20_questions():
    st.header("❓ 20 Questions")
    
    if st.button("← Back to Menu"):
        st.session_state.game_mode = None
        st.rerun()
    
    st.info("""
    **How to Play:**
    1. One person thinks of something (person, place, thing, animal, etc.)
    2. The other person asks YES/NO questions to guess what it is
    3. You have 20 questions to figure it out!
    """)
    
    st.markdown(f"### Current Thinker: {st.session_state.q20_current_thinker}")
    st.markdown(f"**Questions asked: {len(st.session_state.q20_questions_asked)}/20**")
    
    if st.session_state.q20_game_active:
        # Ask question
        question = st.text_input("Ask a YES/NO question:", key="q20_input")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ YES") and question:
                st.session_state.q20_questions_asked.append(f"Q: {question} - A: YES")
                st.rerun()
        with col2:
            if st.button("❌ NO") and question:
                st.session_state.q20_questions_asked.append(f"Q: {question} - A: NO")
                st.rerun()
        with col3:
            if st.button("🤷 MAYBE") and question:
                st.session_state.q20_questions_asked.append(f"Q: {question} - A: MAYBE")
                st.rerun()
        
        # Show previous questions
        if st.session_state.q20_questions_asked:
            st.markdown("### Questions so far:")
            for q in st.session_state.q20_questions_asked:
                st.write(q)
        
        # Make a guess
        st.markdown("---")
        st.markdown("### Ready to guess?")
        guess = st.text_input("What is it?", key="q20_guess")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Correct Guess!") and guess:
                guesser = st.session_state.player2_name if st.session_state.q20_current_thinker == st.session_state.player1_name else st.session_state.player1_name
                st.success(f"🎉 {guesser} wins! They guessed it in {len(st.session_state.q20_questions_asked)} questions!")
                st.session_state.overall_score[guesser] += 1
                st.balloons()
                if st.button("Play Again"):
                    init_20q()
                    st.session_state.q20_current_thinker = guesser
                    st.rerun()
        
        with col2:
            if st.button("❌ Wrong Guess") and guess:
                st.session_state.q20_guesses.append(guess)
                st.error("Not quite! Keep asking questions.")
                st.rerun()
        
        # Out of questions
        if len(st.session_state.q20_questions_asked) >= 20:
            st.error("Out of questions! Time for a final guess!")
            final_guess = st.text_input("Final guess:", key="q20_final")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Got it!") and final_guess:
                    guesser = st.session_state.player2_name if st.session_state.q20_current_thinker == st.session_state.player1_name else st.session_state.player1_name
                    st.success(f"🎉 {guesser} wins!")
                    st.session_state.overall_score[guesser] += 1
            with col2:
                if st.button("❌ Didn't get it"):
                    st.success(f"{st.session_state.q20_current_thinker} wins! They stumped you!")
                    st.session_state.overall_score[st.session_state.q20_current_thinker] += 1

# ===== WOULD YOU RATHER =====
def play_would_you_rather():
    st.header("🤔 Would You Rather")
    
    if st.button("← Back to Menu"):
        st.session_state.game_mode = None
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Same Answers", st.session_state.wyr_score['Same Answer'])
    with col2:
        st.metric("Different Answers", st.session_state.wyr_score['Different Answer'])
    
    st.markdown("---")
    
    # Show question
    question = st.session_state.wyr_current_question
    st.markdown(f"### {question['q']}")
    
    # Get answers
    st.markdown(f"**{st.session_state.player1_name}'s choice:**")
    p1_choice = st.radio("Choose one:", ["Option 1", "Option 2"], key="p1_choice", 
                         label_visibility="collapsed")
    
    st.markdown(f"**{st.session_state.player2_name}'s choice:**")
    p2_choice = st.radio("Choose one:", ["Option 1", "Option 2"], key="p2_choice",
                         label_visibility="collapsed")
    
    if st.button("Reveal Answers!"):
        if p1_choice == p2_choice:
            st.success("🎉 You both chose the same! Great minds think alike!")
            st.session_state.wyr_score['Same Answer'] += 1
        else:
            st.info("🤷 Different choices! You two are unique!")
            st.session_state.wyr_score['Different Answer'] += 1
        
        st.markdown("---")
        if st.button("Next Question"):
            st.session_state.wyr_current_question = random.choice(WYR_QUESTIONS)
            st.rerun()

if __name__ == "__main__":
    main()
