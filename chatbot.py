import streamlit as st
from openai import OpenAI
import os
import json
from pathlib import Path

# ====================
# CONFIGURATION
# ====================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

YOUR_NAME = "Nicola Harvey"
YOUR_ROLE = "Strategic Consultant & Opportunity Architect"
BRAND_DESCRIPTION = """Empowering women, creatives, NFP's & startups in crypto, blockchain & AI."""

# ====================
# PERSISTENT STORAGE (JSON-based)
# ====================
KNOWLEDGE_FILE = "knowledge_base.json"

def load_knowledge_base():
    """Load knowledge base from JSON file"""
    if Path(KNOWLEDGE_FILE).exists():
        with open(KNOWLEDGE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_knowledge_base(knowledge_list):
    """Save knowledge base to JSON file"""
    with open(KNOWLEDGE_FILE, 'w') as f:
        json.dump(knowledge_list, f, indent=2)

def search_knowledge(query, knowledge_list, top_k=15):
    """Enhanced keyword search with category awareness"""
    query_lower = query.lower()
    
    # Category keywords mapping - if these are in the query, get ALL items from that category
    category_keywords = {
        'education': ['education', 'degree', 'degrees', 'qualification', 'qualifications', 
                     'university', 'college', 'diploma', 'certificate', 'studied', 'study',
                     'bachelor', 'masters', 'phd', 'certified', 'credentials', 'academic'],
        'experience': ['experience', 'work', 'job', 'role', 'position', 'career', 'worked'],
        'expertise': ['expertise', 'skills', 'expert', 'specialization', 'capabilities'],
        'bio': ['bio', 'about', 'background', 'who', 'introduction'],
        'brand-voice': ['voice', 'style', 'tone', 'write', 'writing', 'communication'],
        'values': ['values', 'mission', 'believe', 'philosophy', 'principles']
    }
    
    # Check if query is asking for a specific category
    matched_categories = []
    for category, keywords in category_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            matched_categories.append(category)
    
    # If we found category matches, get ALL items from those categories
    if matched_categories:
        category_items = []
        for item in knowledge_list:
            # Check if item's category matches or contains the matched category
            item_cat = item['category'].lower()
            if any(cat in item_cat for cat in matched_categories):
                category_items.append(item)
        
        # If we found items in the matched categories, return all of them
        if category_items:
            return category_items
    
    # Otherwise, do keyword-based search
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'how', 'who', 'where', 
                  'when', 'why', 'tell', 'me', 'about', 'can', 'you', 'please',
                  'nikki', 'nikkis', 'nicola', 'nicolas', 'harvey', 'harveys'}
    
    query_words = set(word for word in query_lower.split() if word not in stop_words and len(word) > 2)
    
    scored_items = []
    for item in knowledge_list:
        content_lower = item['content'].lower()
        category_lower = item['category'].lower()
        
        score = 0
        
        if query_lower in content_lower:
            score += 10
        
        for word in query_words:
            if word in category_lower:
                score += 5
            if word in content_lower:
                score += 2
            if any(word in content_word for content_word in content_lower.split()):
                score += 1
        
        if score > 0:
            scored_items.append((score, item))
    
    scored_items.sort(reverse=True, key=lambda x: x[0])
    return [item for score, item in scored_items[:top_k]]

# ====================
# SETUP
# ====================
st.set_page_config(page_title=f"Chat with {YOUR_NAME}", page_icon="💬")

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Load knowledge base
if 'knowledge_base' not in st.session_state:
    st.session_state.knowledge_base = load_knowledge_base()

if 'show_debug' not in st.session_state:
    st.session_state.show_debug = False

# ====================
# SIDEBAR: KNOWLEDGE BASE MANAGEMENT
# ====================
with st.sidebar:
    st.header("📚 Knowledge Base")
    
    # Password protection for admin features
    password_input = st.text_input("🔐 Admin Password:", type="password", key="admin_pass")
    
    # Show stats (visible to everyone)
    total_items = len(st.session_state.knowledge_base)
    st.metric("Total Knowledge Items", total_items)
    
    st.divider()
    
    # Check if password is correct
    if password_input == ADMIN_PASSWORD:
        st.success("✅ Admin access granted!")
        
        # KNOWLEDGE BASE MANAGER
        st.subheader("🗂️ Manage Knowledge Base")
        
        # View by category
        if st.session_state.knowledge_base:
            categories = {}
            for i, item in enumerate(st.session_state.knowledge_base):
                cat = item['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((i, item))
            
            st.write(f"**Total Items: {len(st.session_state.knowledge_base)}**")
            
            # Category selector
            view_option = st.selectbox(
                "View by category:",
                ["All"] + sorted(categories.keys())
            )
            
            # Show items
            items_to_show = []
            if view_option == "All":
                items_to_show = [(i, item) for i, item in enumerate(st.session_state.knowledge_base)]
            else:
                items_to_show = categories[view_option]
            
            st.write(f"**Showing {len(items_to_show)} items**")
            
            # Display items with delete option
            for idx, item in items_to_show[:20]:  # Show max 20 at a time
                with st.expander(f"📄 {item['category']} - Item #{idx}"):
                    st.text_area(
                        "Content:",
                        value=item['content'],
                        height=100,
                        disabled=True,
                        key=f"view_{idx}"
                    )
                    
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_{idx}"):
                            st.session_state.knowledge_base.pop(idx)
                            save_knowledge_base(st.session_state.knowledge_base)
                            st.success(f"Deleted item #{idx}")
                            st.rerun()
            
            if len(items_to_show) > 20:
                st.info(f"Showing first 20 of {len(items_to_show)} items")
        else:
            st.warning("⚠️ Knowledge base is empty!")
        
        st.divider()
        
        st.subheader("Add Information")
        
        # Text input
        knowledge_text = st.text_area(
            "Paste text about yourself:",
            height=150,
            placeholder="e.g., Your bio, project descriptions, achievements, values...",
            key="add_text"
        )
        
        category = st.text_input("Category/Tag:", placeholder="e.g., bio, projects, skills", key="add_cat")
        
        if st.button("💾 Save to Knowledge Base"):
            if knowledge_text and category:
                # Split into chunks (by paragraphs)
                chunks = [chunk.strip() for chunk in knowledge_text.split('\n\n') if chunk.strip()]
                
                # Add to knowledge base
                for chunk in chunks:
                    st.session_state.knowledge_base.append({
                        'category': category,
                        'content': chunk
                    })
                
                # Save to file
                save_knowledge_base(st.session_state.knowledge_base)
                
                st.success(f"✅ Added {len(chunks)} chunks to knowledge base!")
                st.info("💡 Download and commit to GitHub for permanent storage")
            else:
                st.error("Please fill in both fields")
        
        st.divider()
        
        # Download knowledge base
        if st.session_state.knowledge_base:
            json_str = json.dumps(st.session_state.knowledge_base, indent=2)
            st.download_button(
                label="⬇️ Download Knowledge Base (JSON)",
                data=json_str,
                file_name="knowledge_base.json",
                mime="application/json"
            )
        
        # BULK OPERATIONS
        st.subheader("🔧 Bulk Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Delete by category
            if st.session_state.knowledge_base:
                delete_cat = st.selectbox(
                    "Delete all items from category:",
                    ["Select..."] + sorted(set(item['category'] for item in st.session_state.knowledge_base))
                )
                if delete_cat != "Select..." and st.button(f"🗑️ Delete All from {delete_cat}"):
                    original_count = len(st.session_state.knowledge_base)
                    st.session_state.knowledge_base = [
                        item for item in st.session_state.knowledge_base 
                        if item['category'] != delete_cat
                    ]
                    deleted = original_count - len(st.session_state.knowledge_base)
                    save_knowledge_base(st.session_state.knowledge_base)
                    st.success(f"Deleted {deleted} items from {delete_cat}")
                    st.rerun()
        
        with col2:
            # Search in content
            search_term = st.text_input("🔍 Search content:", placeholder="Enter keyword...")
            if search_term:
                matches = [
                    (i, item) for i, item in enumerate(st.session_state.knowledge_base)
                    if search_term.lower() in item['content'].lower()
                ]
                st.write(f"Found {len(matches)} matches")
        
        st.divider()
        
        if st.button("🗑️ Clear Entire Knowledge Base"):
            if st.button("⚠️ Confirm Clear All", key="confirm_clear"):
                st.session_state.knowledge_base = []
                save_knowledge_base([])
                st.success("Knowledge base cleared!")
                st.rerun()
        
        st.divider()
    elif password_input:
        st.error("❌ Incorrect password")
    else:
        st.info("🔒 Enter admin password to manage knowledge base")

# ====================
# MAIN CHAT INTERFACE
# ====================
st.title(f"💬 Chat with {YOUR_NAME}")
st.caption(f"{YOUR_ROLE} • {BRAND_DESCRIPTION}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get relevant context from knowledge base
    context = ""
    debug_info = ""
    
    if st.session_state.knowledge_base:
        # Category-aware search will return ALL items from matched categories
        results = search_knowledge(prompt, st.session_state.knowledge_base)
        if results:
            context = "\n\n".join([item['content'] for item in results])
            categories_found = set(item['category'] for item in results)
            debug_info = f"Retrieved {len(results)} chunks from categories: {', '.join(categories_found)}"
        else:
            debug_info = "No relevant information found for this query."
    else:
        debug_info = "Knowledge base is empty. Please add information via the sidebar."
    
    # Build system prompt
    system_prompt = f"""You are a helpful assistant representing {YOUR_NAME}, a {YOUR_ROLE}.

{BRAND_DESCRIPTION}

CRITICAL INSTRUCTIONS:
- When answering questions about {YOUR_NAME}, you MUST use ALL information from the context below
- For questions about education/qualifications/degrees/certifications: List EVERY SINGLE item from the context, organized chronologically or by institution
- For questions about experience/work: Include ALL positions and roles mentioned
- For questions about skills/expertise: Include ALL capabilities mentioned
- Synthesize and organize the information clearly, but include EVERYTHING relevant from the context
- Group similar items together for clarity (e.g., all degrees from one university together)
- NEVER make up or infer information that isn't explicitly in the context
- NEVER omit relevant information that is in the context
- If the context contains 10 items about something, your answer should reference all 10 items

Context from {YOUR_NAME}'s knowledge base:
{context if context else "No information available in knowledge base."}

Respond naturally and organize the information well, but ensure you include ALL relevant details from the context above. Completeness is critical."""

    # Get AI response
    with st.chat_message("assistant"):
        # Show debug info FIRST if admin AND debug mode enabled
        debug_expander = None
        if password_input == ADMIN_PASSWORD and ADMIN_PASSWORD and st.session_state.get('show_debug', False):
            st.caption(f"🐛 Debug: {debug_info}")
            if context:
                debug_expander = st.expander("📄 Context Retrieved (Click to expand)")
                with debug_expander:
                    st.write(context)
        
        message_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        try:
            for response in client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            ):
                if response.choices[0].delta.content:
                    full_response += response.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.error(error_msg)
            full_response = "I encountered an error. Please check your API key in Streamlit Secrets."
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ====================
# FOOTER
# ====================
st.divider()
st.caption("💡 Visitors can chat freely. Admin password required to edit knowledge base.")
st.caption("⚠️ Note: Knowledge added via the interface persists until next deployment. Download and commit to GitHub for permanent storage.")
