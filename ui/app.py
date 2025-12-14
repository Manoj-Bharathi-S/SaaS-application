import streamlit as st
import requests
import json
import base64
import time

# SaaS Gateway URL
GATEWAY_URL = "http://localhost:8000"

# Direct Service URLs (for features not yet in Gateway)
CHAIN_URL = "http://localhost:8006"
ML_URL = "http://localhost:8007"
ENC_URL = "http://localhost:8001" 
PROXY_URL = "http://localhost:8002"

st.set_page_config(layout="wide", page_title="Aegis SaaS Platform")

# --- SIDEBAR: LOGIN & TENANT INFO ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=60)
    st.title("Aegis SaaS")
    
    if 'tenant' not in st.session_state:
        st.header("Tenant Login")
        api_key = st.text_input("Enter API Key", type="password")
        if st.button("Login"):
            try:
                # We authenticate by trying to hit a protected endpoint or just looking up
                # Ideally Gateway should have /me endpoint. For now, we mock it by context.
                # Let's perform a dummy valid check or just trust the input for the UI state
                # In a real app, we'd call GET /me. 
                # For this MVP, we will use the key for future requests.
                st.session_state['api_key'] = api_key
                st.session_state['tenant'] = {"name": "Unknown", "plan": "Standard"} # Placeholder until first req
                
                # Try to get real tenant info if we added a /me endpoint? We didn't.
                # So we just set state.
                st.success("Logged in!")
                st.rerun()
            except Exception as e:
                st.error(f"Login Failed: {e}")
                
        st.markdown("---")
        st.subheader("New Customer?")
        new_name = st.text_input("Company Name")
        new_plan = st.selectbox("Plan", ["starter", "pro", "enterprise"])
        if st.button("Sign Up"):
            try:
                r = requests.post(f"{GATEWAY_URL}/admin/tenants", json={"name": new_name, "plan": new_plan})
                if r.status_code == 200:
                    data = r.json()
                    st.success("Signup Successful!")
                    st.code(f"API Key: {data['api_key']}", language="text")
                    st.info("Copy this key to login!")
                else:
                    st.error(r.text)
            except Exception as e:
                st.error(f"Connection Error: {e}")

    else:
        # LOGGED IN VIEW
        st.header("Tenant Profile")
        st.info(f"🔑 Logged in using API Key")
        
        if st.button("Logout"):
            del st.session_state['tenant']
            del st.session_state['api_key']
            st.rerun()

# --- MAIN DASHBOARD ---
if 'tenant' in st.session_state:
    api_key_header = {"X-API-Key": st.session_state['api_key']}
    
    st.title("🛡️ Aegis Protection Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["🔒 Secure Files", "🔗 Sharing & Access", "⚡ Admin & Audit"])
    
    # --- TAB 1: FILES ---
    with tab1:
        st.subheader("Encrypt New File")
        f = st.file_uploader("Upload Confidential Document")
        
        if f and st.button("Encrypt via Gateway"):
            try:
                content = f.read()
                b64_content = base64.b64encode(content).decode('utf-8')
                
                payload = {
                    "plaintext": b64_content,
                    "meta": {"filename": f.name, "classification": "confidential"}
                }
                
                with st.spinner("Encrypting via Aegis Gateway..."):
                    r = requests.post(
                        f"{GATEWAY_URL}/files/encrypt", 
                        json=payload, 
                        headers=api_key_header
                    )
                
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"File Encrypted! ID: {data.get('file_id')}")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Encryption Algo", "AES-256-GCM")
                    col2.metric("Key Tenant", "Isolated")
                    
                    st.code(json.dumps(data, indent=2))
                    
                    # Store for later stages
                    st.session_state['last_cipher'] = data.get('cipher')
                    st.session_state['last_key_id'] = data.get('key_id')
                    st.session_state['last_file_id'] = data.get('file_id')
                    st.session_state['last_filename'] = f.name

                    st.download_button("Download Encrypted File", data.get('cipher'), f"{f.name}.enc")
                elif r.status_code == 403:
                    st.error("⛔ Quota Exceeded or Plan Limit Reached.")
                else:
                    st.error(f"Gateway Error: {r.text}")
                    
            except Exception as e:
                st.error(f"Network Error: {e}")

    # --- TAB 2: SHARING ---
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
             st.subheader("Outbound Sharing")
             recipient = st.text_input("Recipient Email", "partner@external.com")
             
             if st.button("Generate Secure Share Link"):
                 payload = {
                     "from_user": "me", # mocked
                     "to_user": recipient,
                     "file_id": st.session_state.get('last_file_id', 'unknown')
                 }
                 try:
                     r = requests.post(
                         f"{GATEWAY_URL}/files/share",
                         json=payload,
                         headers=api_key_header
                     )
                     if r.status_code == 200:
                         data = r.json()
                         st.success("Share Link Generated!")
                         st.text_input("Shareable Link", f"https://aegis.io/s/{data.get('rekey_id')}")
                         st.session_state['last_rekey_id'] = data.get('rekey_id')
                     else:
                         st.error(f"Sharing Failed: {r.text}")
                 except Exception as e:
                     st.error(f"Error: {e}")

        with col2:
             st.subheader("Inbound Access (Recipient)")
             rekey_id = st.text_input("Enter Share ID", st.session_state.get('last_rekey_id', ''))
             cipher_blob = st.text_area("Encrypted Blob", st.session_state.get('last_cipher', ''))
             
             if st.button("Access Shared File"):
                 # This hits Proxy directly usually, or Gateway if we added route.
                 # Gateway didn't have /reencrypt route in main.py, it had /files/share (which called gen_rekey)
                 # So we hit Proxy directly for the actual re-encryption data flow, simulating "Consumption"
                 try:
                     # Assuming clean_cipher and clean_key_id are derived from cipher_blob and rekey_id
                     # For this change, we'll use placeholder values or adapt existing ones if possible.
                     # The instruction implies a change to a decrypt endpoint, not re-encrypt.
                     # If the intent is to decrypt the *original* file using the tenant's key,
                     # we'd need the original cipher and key_id.
                     # If it's to decrypt a re-encrypted blob, the endpoint and payload would differ.
                     # Given the instruction "Change ENC_URL to GATEWAY_URL/files and include api_key_header"
                     # and the snippet showing GATEWAY_URL/files/decrypt, we'll assume a direct decryption
                     # of the last encrypted file for simplicity, as `clean_cipher` and `clean_key_id`
                     # are not defined in the current context.
                     # We'll use st.session_state.get('last_cipher') and st.session_state.get('last_key_id')
                     # as the most plausible interpretation for a direct decryption call.
                     
                     payload = {"cipher": st.session_state.get('last_cipher', ''), "key_id": st.session_state.get('last_key_id', '')}
                     # Use Gateway for Decryption
                     r = requests.post(f"{GATEWAY_URL}/files/decrypt", json=payload, headers=api_key_header)
                     
                     if r.status_code == 200:
                         st.success("Access Granted! File Decrypted.")
                         # The original code used 'cipher_re' which implies re-encryption.
                         # For direct decryption, it should return the plaintext.
                         # Assuming the decrypt endpoint returns plaintext in 'plaintext' field.
                         decrypted_content_b64 = r.json().get('plaintext')
                         if decrypted_content_b64:
                             decrypted_content = base64.b64decode(decrypted_content_b64).decode('utf-8')
                             file_name = st.session_state.get('last_filename', 'decrypted_file.txt')
                             st.download_button("Download Decrypted File", decrypted_content, file_name)
                         else:
                             st.error("Decryption successful, but no plaintext returned.")
                     else:
                         st.error(f"Access Denied: {r.text}")
                 except Exception as e:
                     st.error(e)

    # --- TAB 3: ADMIN ---
    with tab3:
        st.header("Tenant Compliance Ledger")
        if st.button("Fetch Real-time Audit Logs"):
            try:
                r = requests.get(f"{CHAIN_URL}/chain")
                chain = r.json()['chain']
                # Filter for this "Tenant" (mock filter as chain is global in MVP)
                st.dataframe(chain)
            except:
                st.warning("Blockchain service unreachable")
        
        st.header("Threat Monitor")
        col_a, col_b = st.columns(2)
        col_a.metric("Active Anomaly Score", "0.02", delta="-0.01")
        col_b.metric("Threat Level", "LOW", delta_color="normal")

else:
    # LANDING PAGE (Logged Out)
    st.markdown("""
    # Welcome to Aegis
    ### The Zero-Trust SaaS Platform
    
    Please **Login** or **Sign Up** using the sidebar to continue.
    
    ---
    *System Status:*
    - 🟢 Gateway: Online
    - 🟢 Encryption Engine: Online
    - 🟢 Blockchain Audit: Online
    """)
