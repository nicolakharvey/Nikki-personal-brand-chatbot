import streamlit as st
from openai import OpenAI
import chromadb
import os

# ====================
# CONFIGURATION
# ====================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

YOUR_NAME = "Nicola (Nikki) Harvey"
YOUR_ROLE = "Strategic Consultant & Opportunity Architect"
BRAND_DESCRIPTION = """Empowering women, creatives, NFP's & startups in crypto, blockchain & AI."""

# ====================
# SETUP
# ====================
st.set_page_config(page_title=f"Chat with {YOUR_NAME}", page_icon="💬")

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize ChromaDB (local storage)
chroma_client = chromadb.PersistentClient(path="./knowledge_db")
collection = chroma_client.get_or_create_collection(name="personal_brand")

# ====================
# SIDEBAR: KNOWLEDGE BASE MANAGEMENT
# ====================
with st.sidebar:
    st.header("📚 Knowledge Base")
    
    # Password protection for admin features
    password_input = st.text_input("🔐 Admin Password:", type="password", key="admin_pass")
    
    # Show stats (visible to everyone)
    total_items = len(collection.get()['ids'])
    st.metric("Total Knowledge Items", total_items)
    
    st.divider()
    
    # Check if password is correct
    if password_input == ADMIN_PASSWORD:
        st.success("✅ Admin access granted!")
        
        # DEBUG: Show what's in the database
        st.subheader("🐛 Debug Info")
        if st.button("🔍 Show All Stored Items"):
            all_data = collection.get()
            if all_data['ids']:
                st.write(f"**Found {len(all_data['ids'])} items:**")
                for i, (doc_id, doc) in enumerate(zip(all_data['ids'][:5], all_data['documents'][:5])):
                    st.write(f"**ID {i+1}:** {doc_id}")
                    st.write(f"**Content preview:** {doc[:100]}...")
                    st.divider()
                if len(all_data['ids']) > 5:
                    st.write(f"... and {len(all_data['ids']) - 5} more items")
            else:
                st.warning("⚠️ Database is empty!")
        
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
                
                # Add to ChromaDB
                ids_added = []
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{category}_{len(collection.get()['ids'])}_{i}"
                    collection.add(
                        documents=[chunk],
                        ids=[chunk_id],
                        metadatas=[{"category": category}]
                    )
                    ids_added.append(chunk_id)
                
                st.success(f"✅ Added {len(chunks)} chunks to knowledge base!")
                st.write(f"**IDs added:** {', '.join(ids_added[:3])}")
            else:
                st.error("Please fill in both fields")
        
        st.divider()
        
        if st.button("🗑️ Clear Knowledge Base"):
            chroma_client.delete_collection("personal_brand")
            chroma_client.create_collection("personal_brand")
            collection = chroma_client.get_collection("personal_brand")
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
    try:
        results = collection.query(
            query_texts=[prompt],
            n_results=5  # Increased from 3 to 5 for better retrieval
        )
        if results['documents'] and results['documents'][0]:
            context = "\n\n".join(results['documents'][0])
            debug_info = f"Retrieved {len(results['documents'][0])} chunks from knowledge base."
        else:
            debug_info = "No relevant chunks found in knowledge base."
    except Exception as e:
        debug_info = f"Error querying database: {str(e)}"
        context = ""
    
    # Build system prompt
    system_prompt = f"""You are a helpful assistant representing {YOUR_NAME}, a {YOUR_ROLE}.

{BRAND_DESCRIPTION}

IMPORTANT: When answering questions about {YOUR_NAME}, ALWAYS use the specific information from the context below. DO NOT make up generic answers.

Context from {YOUR_NAME}'s knowledge base:
{context if context else "No specific context available from knowledge base."}

If the context contains specific information (education, experience, skills, etc.), USE IT in your answer with exact details.
If no specific information is in the context, say "I don't have that specific information in my knowledge base yet."

Respond naturally and conversationally."""

    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Show debug info if admin
        if password_input == ADMIN_PASSWORD:
            st.caption(f"🐛 Debug: {debug_info}")
            if context:
                with st.expander("📄 Context Retrieved"):
                    st.write(context[:500] + "..." if len(context) > 500 else context)
        
        full_response = ""
        
        # Stream the response
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
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ====================
# FOOTER
# ====================
st.divider()
st.caption("💡 Visitors can chat freely. Admin password required to edit knowledge base.")
