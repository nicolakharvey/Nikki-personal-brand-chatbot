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
        
        # DEBUG: Show what's stored
        st.subheader("🐛 Debug Info")
        if st.button("🔍 Show All Categories"):
            if st.session_state.knowledge_base:
                categories = {}
                for item in st.session_state.knowledge_base:
                    cat = item['category']
                    categories[cat] = categories.get(cat, 0) + 1
                
                st.write("**Categories in knowledge base:**")
                for cat, count in sorted(categories.items()):
                    st.write(f"- {cat}: {count} items")
            else:
                st.warning("⚠️ Knowledge base is empty!")
        
        if st.button("📄 Show First 3 Items"):
            if st.session_state.knowledge_base:
                for i, item in enumerate(st.session_state.knowledge_base[:3]):
                    st.write(f"**Item {i+1}:**")
                    st.write(f"Category: {item['category']}")
                    st.write(f"Content: {item['content'][:150]}...")
                    st.divider()
            else:
                st.warning("⚠️ Knowledge base is empty!")
        
        st.divider()
        
        st.subheader("Add Information")
        
        # Text input
        knowledge_text = st.text_area(
            "Paste text about yourself:",
            height=150,
            placeholder="e.g., Your bio, project descriptions, achievements, values..."
        )
        
        category = st.text_input("Category/Tag:", placeholder="e.g., bio, projects, skills")
        
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
                st.info("💡 To make this permanent in Streamlit Cloud, download the knowledge_base.json file and commit it to GitHub")
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
        
        st.divider()
        
        if st.button("🗑️ Clear Knowledge Base"):
            st.session_state.knowledge_base = []
            save_knowledge_base([])
            st.success("Knowledge base cleared!")
            st.rerun()
            
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
        # Show debug info FIRST if admin (before placeholder)
        debug_expander = None
        if password_input == ADMIN_PASSWORD and ADMIN_PASSWORD:
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
