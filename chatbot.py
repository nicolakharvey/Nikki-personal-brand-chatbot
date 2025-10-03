import streamlit as st
from openai import OpenAI
import chromadb
import os

# ====================
# CONFIGURATION
# ====================
# Add your OpenAI API key here or set as environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-your-new-key-here")

# ADMIN PASSWORD - Change this to your own secure password!
ADMIN_PASSWORD = "your-new-password-here"

# Your brand information (edit this section!)
YOUR_NAME = "Nicola Harvey"
YOUR_ROLE = "AI & Web3 Strategist | Creator of Agency Systems"
BRAND_DESCRIPTION = """Nicola Harvey is a strategist and thought leader at the intersection of AI, blockchain, and human agency. As AI & Web3 Strategist, she helps individuals, founders, and organisations harness intelligent systems to create stability, unlock new opportunities, and design futures they can actively shape. Her approach blends deep technical understanding with systems thinking, business strategy, and a human-centered perspective informed by her work in trauma-informed and multicultural contexts. Nicola’s voice is relatable but strategic — weaving big ideas like truth, resilience, and creativity with practical anchors like AI workflows, crypto tools, and content systems. She is the co-founder of AI Marketing Content (AIMC), leads AI projects for STARTTS (NSW Service for the Treatment and Rehabilitation of Torture and Trauma Survivors), and is building Frontier Women — a movement to empower women in emerging industries such as AI and Web3. Her mission is simple: to show how technology can be leveraged not just for efficiency or profit, but for agency, empowerment, and creating a parallel stability in an uncertain world."""

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
                for i, chunk in enumerate(chunks):
                    collection.add(
                        documents=[chunk],
                        ids=[f"{category}_{len(collection.get()['ids'])}_{i}"],
                        metadatas=[{"category": category}]
                    )
                
                st.success(f"✅ Added {len(chunks)} chunks to knowledge base!")
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
    try:
        results = collection.query(
            query_texts=[prompt],
            n_results=3
        )
        if results['documents'] and results['documents'][0]:
            context = "\n\n".join(results['documents'][0])
    except:
        context = ""
    
    # Build system prompt
    system_prompt = f"""You are a helpful assistant representing {YOUR_NAME}, a {YOUR_ROLE}.

{BRAND_DESCRIPTION}

When answering questions, use the following context from {YOUR_NAME}'s knowledge base if relevant:

{context if context else "No specific context available - answer based on general knowledge about personal branding."}

Respond naturally and conversationally. If you don't have specific information in the context, be honest about it but still be helpful."""

    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Stream the response
        for response in client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model, or use "gpt-4" for better quality
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
